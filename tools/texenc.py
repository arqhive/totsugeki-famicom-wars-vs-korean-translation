"""GC/Wii 텍스처 인코더(P8+RGB5A3 팔레트, RGBA8, CMPR, RGB5A3) + Kuju DXTG 청크 교체."""
import struct

import numpy as np
from PIL import Image


def to_rgb5a3(rgba):
    r, g, b, a = [rgba[..., i].astype(np.uint32) for i in range(4)]
    op = a >= 0xF0
    v_op = 0x8000 | ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)
    v_tr = ((a >> 5) << 12) | ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
    return np.where(op, v_op, v_tr).astype('>u2')


def tile(a, w, h, bw, bh):
    """(h,w,...) → 타일 순서로 펼친 배열"""
    W = (w + bw - 1) // bw * bw; H = (h + bh - 1) // bh * bh
    pad = np.zeros((H, W) + a.shape[2:], a.dtype); pad[:h, :w] = a
    return pad.reshape(H // bh, bh, W // bw, bw, *a.shape[2:]).swapaxes(1, 2).reshape(-1, *a.shape[2:])


def enc_rgba8(img):
    a = np.asarray(img.convert('RGBA'))
    h, w = a.shape[:2]
    t = tile(a, w, h, 4, 4).reshape(-1, 16, 4)
    ar = np.stack([t[..., 3], t[..., 0]], -1).reshape(-1, 32)
    gb = np.stack([t[..., 1], t[..., 2]], -1).reshape(-1, 32)
    return np.concatenate([ar, gb], 1).astype(np.uint8).tobytes()


def enc_rgb5a3(img):
    a = np.asarray(img.convert('RGBA'))
    h, w = a.shape[:2]
    return tile(to_rgb5a3(a), w, h, 4, 4).tobytes()


def enc_p8(img, ncol=256):
    """→ (팔레트 bytes 512, 픽셀 bytes)"""
    im = img.convert('RGBA')
    q = im.quantize(ncol, method=Image.FASTOCTREE, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette(rawmode='RGBA')[:ncol * 4], np.uint8).reshape(-1, 4)
    pal = np.vstack([pal, np.zeros((ncol - len(pal), 4), np.uint8)])
    idx = np.asarray(q, np.uint8)
    h, w = idx.shape
    return to_rgb5a3(pal).tobytes(), tile(idx, w, h, 8, 4).tobytes()


def _565(c):
    c = np.clip(c, 0, 255).astype(np.int32)
    return ((c[..., 0] >> 3) << 11) | ((c[..., 1] >> 2) << 5) | (c[..., 2] >> 3)


def _from565(v):
    return np.stack([(v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31], -1).astype(np.float32)


def _cmpr_block(px):
    """px (16,4) uint8 → 8바이트"""
    rgb = px[:, :3].astype(np.float32); alpha = px[:, 3]
    trans = alpha < 128
    opq = rgb[~trans] if (~trans).any() else rgb
    mean = opq.mean(0)
    if len(opq) > 1:
        cov = np.cov((opq - mean).T)
        axis = np.linalg.eigh(cov)[1][:, -1] if np.isfinite(cov).all() else np.array([1, 1, 1], np.float32)
    else:
        axis = np.array([1, 1, 1], np.float32)
    proj = (opq - mean) @ axis
    lo, hi = mean + axis * proj.min(), mean + axis * proj.max()
    c0, c1 = int(_565(hi)), int(_565(lo))
    if trans.any():
        if c0 > c1: c0, c1 = c1, c0
        e0, e1 = _from565(np.array(c0)), _from565(np.array(c1))
        pal = np.stack([e0, e1, (e0 + e1) / 2, np.zeros(3)])
        d = ((rgb[:, None, :] - pal[None, :3]) ** 2).sum(-1)
        sel = d.argmin(1); sel[trans] = 3
    else:
        if c0 < c1: c0, c1 = c1, c0
        if c0 == c1:
            sel = np.zeros(16, np.int64)
        else:
            e0, e1 = _from565(np.array(c0)), _from565(np.array(c1))
            pal = np.stack([e0, e1, (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3])
            sel = ((rgb[:, None, :] - pal[None]) ** 2).sum(-1).argmin(1)
    bits = 0
    for i in range(16):
        bits |= int(sel[i]) << (30 - 2 * i)
    return struct.pack('>HHI', c0, c1, bits)


def enc_cmpr(img):
    a = np.asarray(img.convert('RGBA'))
    h, w = a.shape[:2]
    W = (w + 7) // 8 * 8; H = (h + 7) // 8 * 8
    pad = np.zeros((H, W, 4), np.uint8); pad[:h, :w] = a
    out = bytearray()
    for ty in range(0, H, 8):
        for tx in range(0, W, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    out += _cmpr_block(pad[ty + sy:ty + sy + 4, tx + sx:tx + sx + 4].reshape(16, 4))
    return bytes(out)


def replace_dxtg(d, name, img):
    """리소스/btf 바이트 d 안의 이름 name 인 DXTG 텍스처를 img 로 교체(같은 크기·형식). 교체 수 반환"""
    d = bytearray(d); n = 0; o = 0
    while True:
        o = d.find(b'DXTG', o)
        if o < 0: break
        nm = bytes(d[o + 8:o + 0x18]).split(b'\0')[0].decode('latin1')
        if nm == name:
            w, h = struct.unpack_from('>II', d, o + 0x28)
            assert (w, h) == img.size, (name, (w, h), img.size)
            fmt = bytes(d[o + 0x3E:o + 0x40])[::-1].decode()
            q = o + 0x78
            if fmt == 'P8':
                assert d[q:q + 4] == b' LAP' and struct.unpack_from('<I', d, q + 4)[0] == 512
                pal, px = enc_p8(img)
                d[q + 8:q + 8 + 512] = pal; q += 8 + 512
            elif fmt == 'A8':
                px = enc_rgba8(img)
            elif fmt == 'DX':
                px = enc_cmpr(img)
            else:
                raise ValueError(fmt)
            assert d[q:q + 4] == b' PIM' and struct.unpack_from('<I', d, q + 4)[0] == len(px), (name, fmt, len(px))
            d[q + 8:q + 8 + len(px)] = px
            n += 1
        o += 4
    return bytes(d), n
