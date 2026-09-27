"""opening.bnr 안 banner.bin/icon.bin 의 TPL(RGB5A3) 그림을 같은 크기로 바꿔 다시 묶는다.
구조: 0x40 빈칸 + IMET(크기=압축 해제 크기, 그대로) + U8(meta/banner.bin, icon.bin, sound.bin)
각 .bin = IMD5(32바이트: 'IMD5', 데이터 크기, 0*8, MD5) + LZ77(0x10) 압축 U8."""
import hashlib
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texenc import enc_rgb5a3


def u8_entries(d):
    """→ [(경로, 데이터 오프셋, 크기)] 와 노드 정보"""
    root, hsz, doff = struct.unpack_from('>III', d, 4)
    n = struct.unpack_from('>I', d, root + 8)[0]
    st = root + n * 12
    out = []; path = []; ends = []
    for i in range(1, n):
        t, no, a, b = struct.unpack_from('>BxHII', d, root + i * 12)
        while ends and ends[-1] <= i:
            ends.pop(); path.pop()
        name = d[st + no:].split(b'\0')[0].decode()
        if t == 1:
            path.append(name); ends.append(b)
        else:
            out.append(('/'.join(path + [name]), i, a, b))
    return out


def lz77_dec(d):
    assert d[:4] == b'LZ77' and d[4] == 0x10
    d = d[4:]
    size = d[1] | d[2] << 8 | d[3] << 16; o = 4; out = bytearray()
    while len(out) < size:
        fl = d[o]; o += 1
        for b in range(8):
            if len(out) >= size: break
            if fl & (0x80 >> b):
                x = d[o] << 8 | d[o + 1]; o += 2
                ln = (x >> 12) + 3; disp = (x & 0xFFF) + 1
                for _ in range(ln): out.append(out[-disp])
            else:
                out.append(d[o]); o += 1
    return bytes(out)


def lz77_enc(src):
    out = bytearray(b'LZ77' + bytes([0x10]) + struct.pack('<I', len(src))[:3])
    table = {}
    i = 0; n = len(src)
    while i < n:
        flag_pos = len(out); out.append(0); flag = 0
        for b in range(8):
            if i >= n: break
            best_len = 0; best_d = 0
            key = src[i:i + 3]
            if len(key) == 3:
                for p in reversed(table.get(key, [])[-64:]):
                    dist = i - p
                    if dist > 4096: break
                    if dist < 2: continue  # 일부 해제기 호환(거리 1 회피)
                    ln = 3
                    while ln < 18 and i + ln < n and src[p + ln] == src[i + ln]:
                        ln += 1
                    if ln > best_len:
                        best_len, best_d = ln, dist
                        if ln == 18: break
            if best_len >= 3:
                flag |= 0x80 >> b
                x = ((best_len - 3) << 12) | (best_d - 1)
                out += bytes([x >> 8, x & 0xFF])
                for j in range(i, i + best_len):
                    table.setdefault(src[j:j + 3], []).append(j)
                i += best_len
            else:
                out.append(src[i])
                table.setdefault(key, []).append(i)
                i += 1
        out[flag_pos] = flag
    while len(out) % 4: out.append(0)
    return bytes(out)


def imd5(data):
    return b'IMD5' + struct.pack('>I', len(data)) + b'\0' * 8 + hashlib.md5(data).digest() + data


def patch_tpl(tpl, img):
    tpl = bytearray(tpl)
    io = struct.unpack_from('>I', tpl, 12)[0]
    h, w, fmt, do = struct.unpack_from('>HHII', tpl, io)
    assert fmt == 5 and (w, h) == img.size, (fmt, w, h, img.size)
    px = enc_rgb5a3(img)
    tpl[do:do + len(px)] = px
    return bytes(tpl)


def patch_bin(binf, repl):
    """binf: IMD5+LZ77 U8, repl: {U8 내부 경로: PIL 이미지}"""
    dec = bytearray(lz77_dec(binf[32:]))
    for path, _, a, b in u8_entries(dec):
        if path in repl:
            dec[a:a + b] = patch_tpl(bytes(dec[a:a + b]), repl[path])
    assert lz77_dec(lz77_enc(bytes(dec))) == bytes(dec)
    return imd5(lz77_enc(bytes(dec)))


def rebuild_outer(u8, newdata):
    """바깥 U8: 노드·이름표 그대로, 파일 데이터만 교체(32바이트 정렬)"""
    root, hsz, doff = struct.unpack_from('>III', u8, 4)
    head = bytearray(u8[:doff])
    ents = u8_entries(u8)
    body = bytearray(); o = doff
    for path, node, a, b in ents:
        data = newdata.get(path, u8[a:a + b])
        struct.pack_into('>II', head, root + node * 12 + 4, o + len(body), len(data))
        body += data
        while len(body) % 32: body.append(0)
    return bytes(head + body)


def patch_bnr(bnr, banner_repl, icon_repl):
    i = bnr.find(b'\x55\xaa\x38\x2d')
    u8 = bnr[i:]
    ents = {p: u8[a:a + b] for p, _, a, b in u8_entries(u8)}
    new = {}
    if banner_repl: new['meta/banner.bin'] = patch_bin(ents['meta/banner.bin'], banner_repl)
    if icon_repl: new['meta/icon.bin'] = patch_bin(ents['meta/icon.bin'], icon_repl)
    return bnr[:i] + rebuild_outer(u8, new)
