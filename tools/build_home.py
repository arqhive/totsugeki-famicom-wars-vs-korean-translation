"""HOME 버튼 메뉴 글씨: tools/assets/home/<텍스처>.png → Data/HomeButton2·3/homeBtn.arc 안 arc/timg/<텍스처>.tpl 교체.
글씨 텍스처는 I4(4비트 밝기, 흰 글씨=보임) 한 장짜리 TPL 이다. 같은 크기로 바꾸므로 arc 의 배치·크기는 그대로다.
→ work/build/files/Data/HomeButton{2,3}/homeBtn.arc"""
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bnrpack
import paths

ARCS = ['Data/HomeButton2/homeBtn.arc', 'Data/HomeButton3/homeBtn.arc']  # 일본어판이 쓰는 기본(접미사 없는) 묶음
SRC = paths.ASSETS / 'home'
OUT = paths.BUILD / 'files'


def enc_i4(img, w, h):
    a = np.asarray(img.convert('L'), np.uint8)
    assert a.shape == (h, w), (a.shape, w, h)
    v = (a.astype(np.uint16) * 15 + 127) // 255  # 0~255 → 0~15
    t = v.reshape(h // 8, 8, w // 8, 8).swapaxes(1, 2).reshape(-1, 64)  # 8x8 타일 순서
    return ((t[:, 0::2] << 4) | t[:, 1::2]).astype(np.uint8).tobytes()


def patch_tpl(tpl, img):
    tpl = bytearray(tpl)
    n, tab = struct.unpack_from('>II', tpl, 4)
    assert n == 1
    io = struct.unpack_from('>I', tpl, tab)[0]
    h, w, fmt, do = struct.unpack_from('>HHII', tpl, io)
    assert fmt == 0, fmt  # I4
    px = enc_i4(img, w, h)
    tpl[do:do + len(px)] = px
    return bytes(tpl)


def main():
    imgs = {p.stem: Image.open(p) for p in sorted(SRC.glob('*.png'))}
    total = 0; used = set()
    for arc in ARCS:
        d = bytearray(open(paths.JP_FILES / arc, 'rb').read())
        done = []
        for path, _, off, size in bnrpack.u8_entries(bytes(d)):
            name = os.path.basename(path)
            if name.endswith('.tpl') and name[:-4] in imgs:
                new = patch_tpl(bytes(d[off:off + size]), imgs[name[:-4]])
                assert len(new) == size
                d[off:off + size] = new; done.append(name[:-4])
        os.makedirs(os.path.dirname(OUT / arc), exist_ok=True)
        open(OUT / arc, 'wb').write(bytes(d))
        total += len(done); used |= set(done)
    missing = set(imgs) - used
    assert not missing, f'어느 묶음에도 없는 글씨: {missing}'
    print(f'  HOME 메뉴 글씨 {len(imgs)}종 → homeBtn.arc 2벌에 {total}곳')
    return total


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
