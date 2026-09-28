"""배포용 패처 생성: 바뀐 게임 파일마다 원본과의 xdelta 차분을 만들어 패처 폴더·zip 으로 묶는다.
ISO 통째 차분과 달리 원본 덤프 형태(정본 ISO·WBFS 변환본·WBFS 등)와 상관없이 적용된다.
.gz 파일은 압축을 푼 내용끼리 차분하고, 패처가 적용 후 다시 압축한다(게임은 풀어서 읽기만 함).
사용: python tools/make_patcher.py [버전]        (기본 0.1.1)
결과: release/TotsugekiFamicomWarsVS_KO_v{버전}/ 과 같은 이름의 .zip"""
import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_images
import build_text
import patch_dol
import paths

VER = sys.argv[1] if len(sys.argv) > 1 else '0.1.1'
NAME = f'TotsugekiFamicomWarsVS_KO_v{VER}'
OUT = paths.RELEASE / NAME
PATCHER = paths.ROOT / 'patcher'
WIT_BIN = paths.TOOLS / 'bin' / 'wit-v3.05a-r8638-cygwin64'
WIT_FILES = ('bin/wit.exe', 'bin/cygwin1.dll', 'bin/cygz.dll', 'bin/cygcrypto-1.1.dll', 'bin/cygncursesw-10.dll',
             'gpl-2.0.txt')


def md5(b):
    return hashlib.md5(b).hexdigest()


def changed_files():
    """(DATA 파티션 안 경로, 원본 경로, 빌드 결과 경로) — 원본과 내용이 다른 것만"""
    for sub in ('sys', 'files'):
        base = paths.BUILD / sub
        for dp, _, fs in os.walk(base):
            for f in sorted(fs):
                new = os.path.join(dp, f)
                rel = os.path.relpath(new, paths.BUILD).replace(os.sep, '/')
                old = paths.JP / 'DATA' / rel
                if not old.exists():
                    raise SystemExit(f'원본에 없는 파일: {rel}')
                if old.read_bytes() != open(new, 'rb').read():
                    yield rel, old, new


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    paths.ensure_jp()
    if paths.BUILD.exists():
        shutil.rmtree(paths.BUILD)
    print('[1] 문자열·장면 폰트'); build_text.main()
    print('[2] 이미지'); build_images.main()
    print('[3] main.dol'); patch_dol.main()

    print('[4] 파일별 차분')
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'data').mkdir(parents=True)
    tmp = paths.WORK / 'patcher_tmp'
    tmp.mkdir(exist_ok=True)
    lines, n_gz = [], 0
    for i, (rel, old, new) in enumerate(changed_files()):
        a, b = old.read_bytes(), open(new, 'rb').read()
        mode = 'raw'
        if a[:2] == b'\x1f\x8b':
            a, b, mode = gzip.decompress(a), gzip.decompress(b), 'gz'
            n_gz += 1
        (tmp / 'a').write_bytes(a); (tmp / 'b').write_bytes(b)
        patch = f'{i:03d}.xdelta'
        subprocess.run([paths.xdelta3(), '-e', '-f', '-9', '-S', 'djw', '-s', str(tmp / 'a'), str(tmp / 'b'),
                        str(OUT / 'data' / patch)], check=True)
        # 모드, 차분 파일, 경로, 원본 MD5(디스크 속 파일 그대로), 결과 MD5(gz 는 푼 내용)
        lines.append('\t'.join((mode, patch, rel, md5(old.read_bytes()), md5(b))))
    shutil.rmtree(tmp)
    (OUT / 'data' / 'manifest.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'  파일 {len(lines)}개(그중 gz {n_gz}개)')

    print('[5] 패처 폴더')
    for f in PATCHER.iterdir():
        shutil.copy2(f, OUT / f.name)
    shutil.copy2(paths.RELEASE / 'README_한국어.txt', OUT / 'README_한국어.txt')
    (OUT / 'bin').mkdir()
    for f in WIT_FILES:
        shutil.copy2(WIT_BIN / f, OUT / 'bin' / ('wit-gpl-2.0.txt' if f.endswith('.txt') else os.path.basename(f)))
    shutil.copy2(paths.xdelta3(), OUT / 'bin' / 'xdelta3.exe')

    zpath = paths.RELEASE / f'{NAME}.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fs in os.walk(OUT):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                z.write(p, os.path.join(NAME, os.path.relpath(p, OUT)))
    size = sum(f.stat().st_size for f in (OUT / 'data').iterdir())
    print(f'\n패처: {OUT}\n  차분 합계 {size / 1e6:.2f} MB, zip {zpath.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
