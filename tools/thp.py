"""THP 동영상(Wii) 프레임 읽기·교체.

프레임 = [다음 프레임 크기, 이전 프레임 크기, 그림 크기, (소리 크기)] + JPEG + 소리.
JPEG 은 baseline 4:2:0 인데 엔트로피 구간의 바이트 채움(FF 00)이 없고 APP0 도 없다.
교체는 프레임 크기·위치를 바꾸지 않는다: 새 JPEG 을 원래 그림 칸 안에 넣고 남는 곳은 0 으로 채운다.
"""
import io
import struct

from PIL import Image


def frames(d):
    """→ [(번호, 프레임 위치, 프레임 크기, 그림 시작 위치, 그림 크기)]"""
    nf, first_size, _, comp_off, _, first_off = struct.unpack_from('>6I', d, 20)
    ncomp = struct.unpack_from('>I', d, comp_off)[0]
    hdr = 12 + 4 * (1 in d[comp_off + 4:comp_off + 4 + ncomp])
    out = []; o, sz = first_off, first_size
    for i in range(nf):
        out.append((i, o, sz, o + hdr, struct.unpack_from('>I', d, o + 8)[0]))
        nxt = struct.unpack_from('>I', d, o)[0]; o += sz; sz = nxt
    return out


def _scan_start(b):
    o = 2
    while True:
        m = b[o + 1]; ln = struct.unpack_from('>H', b, o + 2)[0]
        if m == 0xDA:
            return o + 2 + ln
        o += 2 + ln


def stuff(b):
    """THP JPEG → 표준 JPEG(엔트로피 구간 FF 뒤에 00)"""
    s = _scan_start(b); e = b.rfind(b'\xff\xd9')
    return b[:s] + b[s:e].replace(b'\xff', b'\xff\x00') + b'\xff\xd9'


def unstuff(b):
    """표준 JPEG → THP JPEG(APPn·COM 제거, 채움 제거)"""
    out = bytearray(b[:2]); o = 2
    while True:
        m = b[o + 1]; ln = struct.unpack_from('>H', b, o + 2)[0]
        if not (0xE0 <= m <= 0xEF or m == 0xFE):
            out += b[o:o + 2 + ln]
        if m == 0xDA:
            s = o + 2 + ln; break
        o += 2 + ln
    e = b.rfind(b'\xff\xd9'); body = b[s:e]
    assert b'\xff\xd0' not in body
    return bytes(out) + body.replace(b'\xff\x00', b'\xff') + b'\xff\xd9'


def decode(d, fr):
    _, _, _, io_, isz = fr
    return Image.open(io.BytesIO(stuff(bytes(d[io_:io_ + isz])))).convert('RGB')


def encode(img, q=95):
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=q, subsampling=2, optimize=True)
    return unstuff(buf.getvalue())


def rebuild(d, new_jpegs):
    """프레임 그림을 바꿔 THP 를 다시 짠다(프레임 크기가 달라져도 됨).
    new_jpegs: {프레임 번호: THP JPEG bytes}. 헤더의 최대 버퍼·전체 크기·첫/마지막 프레임 정보와 프레임별 앞뒤 크기를 다시 계산한다."""
    d = bytes(d)
    nf, first_size, _, comp_off, offs_off, first_off = struct.unpack_from('>6I', d, 20)
    assert offs_off == 0, '프레임 위치표가 있는 THP 는 지원 안 함'
    ncomp = struct.unpack_from('>I', d, comp_off)[0]
    has_audio = 1 in d[comp_off + 4:comp_off + 4 + ncomp]
    hdr = 16 if has_audio else 12
    bodies = []
    for i, o, sz, io_, isz in frames(d):
        asz = struct.unpack_from('>I', d, o + 12)[0] if has_audio else 0
        img = new_jpegs.get(i, d[io_:io_ + isz])
        audio = d[io_ + isz:io_ + isz + asz]
        body = bytearray(struct.pack('>III', 0, 0, len(img)) + (struct.pack('>I', asz) if has_audio else b'') + img + audio)
        while len(body) % 32:
            body.append(0)
        bodies.append(body)
    sizes = [len(b) for b in bodies]
    for k, b in enumerate(bodies):
        struct.pack_into('>I', b, 0, sizes[(k + 1) % len(sizes)])   # 다음 프레임 크기(원본도 마지막은 첫 프레임 크기)
        struct.pack_into('>I', b, 4, sizes[k - 1])                  # 이전 프레임 크기(첫 프레임은 마지막 크기)
    out = bytearray(d[:first_off]) + b''.join(bodies)
    struct.pack_into('>I', out, 8, max(sizes))                      # 최대 버퍼 크기
    struct.pack_into('>I', out, 24, sizes[0])                       # 첫 프레임 크기
    struct.pack_into('>I', out, 28, sum(sizes))                     # 프레임 데이터 전체 크기
    struct.pack_into('>I', out, 44, first_off + sum(sizes[:-1]))    # 마지막 프레임 위치
    return bytes(out)


def replace(d, fr, img, q0=92):
    """bytearray d 의 프레임 fr 그림을 img 로 교체(칸 크기 유지, 품질을 낮춰 가며 맞춤). → 쓴 품질"""
    _, _, _, io_, isz = fr
    for q in range(q0, 20, -4):
        buf = io.BytesIO(); img.save(buf, 'JPEG', quality=q, subsampling=2, optimize=True)
        j = unstuff(buf.getvalue())
        if len(j) <= isz:
            d[io_:io_ + isz] = j + bytes(isz - len(j))
            return q
    raise ValueError('프레임 칸에 맞출 수 없음')
