"""Kuju 폰트 BTF(FTBG, 2편 Wii) 읽기/쓰기 — 256x256 P4 시트 전용.

파일: 'FTBG' + 4바이트(?) + u32 시트 수(LE) + DXTG 청크 x N (빈틈 없음)
DXTG 청크(크기 필드 LE = 전체-8): 0x00 'DXTG', 0x04 크기, 0x08 이름[16], 0x28 폭(BE), 0x2C 높이(BE), 0x3E 형식('4P'),
  0x78 ' LAP' + 크기 0x20 + RGB5A3 팔레트 16색(BE), 0xA0 ' PIM' + 크기 0x8000 + C4 픽셀(8x8 타일, 앞 니블 먼저)
"""
import struct

import numpy as np

W = H = 256
HEAD = 0xA8


def _untile4(raw):
    a = np.frombuffer(raw, np.uint8)
    px = np.stack([a >> 4, a & 15], 1).reshape(H // 8, W // 8, 8, 8)
    return px.transpose(0, 2, 1, 3).reshape(H, W)


def _tile4(idx):
    t = idx.reshape(H // 8, 8, W // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 2)
    return ((t[:, 0] << 4) | t[:, 1]).astype(np.uint8).tobytes()


def load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'FTBG'
    n = struct.unpack_from('<I', d, 8)[0]
    o = 12
    texs = []
    for _ in range(n):
        assert d[o:o + 4] == b'DXTG'
        size = struct.unpack_from('<I', d, o + 4)[0] + 8
        c = d[o:o + size]
        assert c[0x3E:0x40] == b'4P' and c[0x78:0x7C] == b' LAP' and c[0xA0:0xA4] == b' PIM' and size == HEAD + 0x8000, path
        texs.append(dict(head=c[:HEAD], name=c[8:0x18].split(b'\0')[0].decode(),
                         idx=_untile4(c[HEAD:]), pal=c[0x80:0xA0]))
        o += size
    assert o == len(d)
    return dict(hdr=d[4:8], texs=texs)


def save(f, path):
    out = bytearray(b'FTBG' + f['hdr'] + struct.pack('<I', len(f['texs'])))
    for t in f['texs']:
        head = bytearray(t['head'])
        head[8:0x18] = t['name'].encode()[:15].ljust(16, b'\0')
        head[0x80:0xA0] = t['pal']
        out += head + _tile4(t['idx'])
    open(path, 'wb').write(out)


if __name__ == '__main__':
    import glob, sys, os, tempfile
    ok = bad = 0
    for p in sorted(glob.glob(sys.argv[1] + '/*.btf')):
        try:
            f = load(p)
        except AssertionError:
            continue
        t = os.path.join(tempfile.gettempdir(), 'x.btf'); save(f, t)
        same = open(t, 'rb').read() == open(p, 'rb').read()
        ok += same; bad += not same
        if not same: print('다름', p)
    print('동일', ok, '다름', bad)
