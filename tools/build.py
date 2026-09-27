"""한글 ISO 빌드: 문자열·장면 폰트 → 이미지 → main.dol 패치 → 원본 배치 유지 ISO → 검증.
사용: python tools/build.py [출력 ISO]      (기본 work/TotsugekiFamicomWarsVS_KO.iso)
"""
import filecmp
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_images
import build_text
import inplace
import patch_dol
import paths

DEFAULT_ISO = paths.WORK / 'TotsugekiFamicomWarsVS_KO.iso'


def verify(out_iso):
    """결과 ISO 의 DATA 파티션을 풀어 모든 파일을 (빌드 결과가 있으면 그것, 없으면 원본)과 비교"""
    chk = paths.WORK / 'verify'
    if chk.exists():
        shutil.rmtree(chk)
    subprocess.run([paths.dolphin_tool(), 'extract', '-i', str(out_iso), '-o', str(chk), '-g', '-q'], check=True)
    n = bad = 0
    for sub in ('files', 'sys'):
        base = chk / 'DATA' / sub
        for dp, _, fs in os.walk(base):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), base)
                exp = paths.BUILD / sub / rel
                if not exp.exists():
                    exp = paths.JP / 'DATA' / sub / rel
                n += 1
                if not filecmp.cmp(os.path.join(dp, f), exp, shallow=False):
                    bad += 1; print('    다름:', sub, rel)
    shutil.rmtree(chk)
    if bad:
        raise SystemExit(f'검증 실패: {bad}/{n}개 파일이 다릅니다')
    print(f'  검증: 파일 {n}개 모두 일치')


def main(out_iso=DEFAULT_ISO):
    sys.stdout.reconfigure(encoding='utf-8')
    paths.ensure_jp()
    if paths.BUILD.exists():
        shutil.rmtree(paths.BUILD)
    print('[1] 문자열·장면 폰트'); build_text.main()
    print('[2] 이미지'); build_images.main()
    print('[3] main.dol'); patch_dol.main()
    print('[4] ISO(원본 배치 유지)'); inplace.main(str(out_iso))
    print('[5] 검증'); verify(out_iso)
    print('완료:', out_iso)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ISO)
