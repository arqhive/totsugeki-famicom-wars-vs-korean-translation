"""tools/assets/*.png(한글화 이미지) → 게임 파일에 삽입 → work/build/files/...
리소스(.res.gz/.btf.gz)는 풀어서 같은 이름 텍스처를 모두 교체한 뒤 다시 gzip."""
import gzip
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from texenc import replace_dxtg, enc_rgb5a3
import bnrpack
import paths

SRC = paths.JP_FILES
OUT = paths.BUILD / 'files'
IMG = paths.ASSETS
RES = [f'Data/CompoundFiles/{n}_Level.res.gz' for n in
       ('Frontend2', 'credits', 'fe_concept', 'fe_units_ai', 'fe_units_il', 'fe_units_se', 'fe_units_tt', 'fe_units_wf', 'fe_units_x')]

# (파일, 텍스처 이름, 이미지)
JOBS = []
for r in RES:
    JOBS += [(r, 'BWii_logo', '01_타이틀로고'), (r, 'but_back_n', '04_뒤로버튼_보통'), (r, 'but_back_s', '05_뒤로버튼_선택')]
JOBS += [
    ('Data/CompoundFiles/Frontend2_Level.res.gz', 'BWii_logo_mini', '02_타이틀로고_작은'),
    ('Data/Loading/Backdrop.btf', 'BWii_logo_load2', '03_로딩화면_로고'),
    ('Data/Loading/ObjButton_logo.btf', 'BWii_logo_mini', '03b_로딩화면_작은로고'),
    ('Data/Startup/strap_608x456_jp.btf.gz', 'strapA_608x456_j', '06_스트랩경고A_4대3'),
    ('Data/Startup/strap_608x456_jp.btf.gz', 'strapB_608x456_j', '07_스트랩경고B_4대3'),
    ('Data/Startup/strap_16_9_832x456_jp.btf.gz', 'strapA_16_9_832x', '08_스트랩경고A_16대9'),
    ('Data/Startup/strap_16_9_832x456_jp.btf.gz', 'strapB_16_9_832x', '09_스트랩경고B_16대9'),
]


def img(n):
    return Image.open(f'{IMG}/{n}.png').convert('RGBA')


def main():
    files = {}
    for f, tex, im in JOBS:
        if f not in files:
            raw = open(f'{SRC}/{f}', 'rb').read()
            files[f] = [gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw, raw[:2] == b'\x1f\x8b']
        files[f][0], n = replace_dxtg(files[f][0], tex, img(im))
        assert n >= 1, (f, tex)
    for f, (d, gz) in files.items():
        os.makedirs(os.path.dirname(f'{OUT}/{f}'), exist_ok=True)
        open(f'{OUT}/{f}', 'wb').write(gzip.compress(d, 9, mtime=0) if gz else d)
    # 세이브 데이터 배너 로고(TPL RGB5A3)
    f = 'Data/Loading/BWii_logo.tpl'
    t = bytearray(open(f'{SRC}/{f}', 'rb').read())
    io = struct.unpack_from('>I', t, 12)[0]
    h, w, fmt, do = struct.unpack_from('>HHII', t, io)
    im = img('10_세이브데이터_로고'); assert fmt == 5 and (w, h) == im.size
    px = enc_rgb5a3(im); t[do:do + len(px)] = px
    open(f'{OUT}/{f}', 'wb').write(bytes(t))
    # 채널 배너·아이콘
    b = open(f'{SRC}/opening.bnr', 'rb').read()
    nb = bnrpack.patch_bnr(b, {'arc/timg/BWii_logo.tpl': img('11_채널배너_로고')},
                           {'arc/timg/BWii_logo2.tpl': img('12_채널아이콘_로고')})
    open(f'{OUT}/opening.bnr', 'wb').write(nb)
    print(f'  이미지 {len(set(j[2] for j in JOBS)) + 3}장 → 텍스처 {len(JOBS)}곳, 세이브 로고, 채널 배너·아이콘')


if __name__ == '__main__':
    main()
