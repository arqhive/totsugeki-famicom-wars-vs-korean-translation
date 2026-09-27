"""main.dol 패치 → work/build/sys/main.dol  (행간 +3px. 자간 +2px 는 꺼 둠)

글자 간격 = 글자폭(wdf) + 자간, 자간 = 전역값 + 폰트값(+0x18) - 1.0(r2-0x7fd4).
게임은 글자폭만큼 텍스처를 잘라 그리므로 폭을 칸(22px)보다 크게 하면 옆 칸이 딸려 나온다(시험2 점선).
그래서 폭은 22 이하로 두고, 자간 계산 세 곳(위치·그리기·줄 폭 측정)의 상수 1.0 을 -1.0(r2-0x7fd8)으로 바꿔 자간을 +2 한다.
상수 1.0 자체는 2,600곳에서 같이 쓰므로 값을 바꾸지 않고 명령의 참조 위치만 바꾼다."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

SRC = paths.JP_SYS / 'main.dol'
OUT = paths.BUILD / 'sys' / 'main.dol'
SPACING_PATCH = False
LINE_PATCH = os.environ.get('BW2_LINE_PATCH', '0') == '1'  # 행간 +3 패치(v0.1은 원본 행간)
SPACING = {
    0x8031d06c: (0xc042802c, 0xc0428028),  # lfs f2,-0x7fd4(r2) → -0x7fd8
    0x8031d130: (0xc022802c, 0xc0228028),  # lfs f1
    0x8031ea4c: (0xc022802c, 0xc0228028),  # lfs f1
}
PATCH = {  # 주소: (원래 명령, 새 명령)
    # 자간 +2(시험3~5에서 사용, 간격 24) — S1 글꼴(몸통 18)에는 틈이 너무 넓어 시험6부터 뺌(간격 22). 되살리려면 SPACING_PATCH = True
    # 행간 +3: 폰트 로드 때 줄 높이(+0x132) = 시트별 칸 높이의 최댓값 → 마지막 시트 칸 높이 + 3 (칸 높이는 모든 시트가 같음)
    # 줄 높이는 줄바꿈·줄 폭 계산에만 쓰이고 글자 그리기 크기와는 무관(모든 읽기 위치 확인).
    0x8031c48c: (0xa81e0132, 0xa8630016),  # lha r0,0x132(r30) → lha r3,0x16(r3)
    0x8031c490: (0xa8630016, 0x38630003),  # lha r3,0x16(r3)  → addi r3,r3,3
    0x8031c494: (0x7c001800, 0x60000000),  # cmpw r0,r3       → nop
    0x8031c498: (0x40810008, 0x60000000),  # ble              → nop
    0x8031c49c: (0x7c030378, 0x60000000),  # mr r3,r0         → nop
}


def a2f(d, a):
    offs = struct.unpack_from('>18I', d, 0); addrs = struct.unpack_from('>18I', d, 0x48); sizes = struct.unpack_from('>18I', d, 0x90)
    for o, b, s in zip(offs, addrs, sizes):
        if s and b <= a < b + s:
            return o + a - b
    raise ValueError(hex(a))


def main():
    d = bytearray(open(SRC, 'rb').read())
    r2 = 0x8060af80
    assert struct.unpack('>f', d[a2f(d, r2 - 0x7fd4):][:4])[0] == 1.0
    assert struct.unpack('>f', d[a2f(d, r2 - 0x7fd8):][:4])[0] == -1.0
    patch = dict(PATCH if LINE_PATCH else {}, **(SPACING if SPACING_PATCH else {}))
    for a, (old, new) in patch.items():
        f = a2f(d, a)
        assert struct.unpack_from('>I', d, f)[0] == old, hex(a)
        struct.pack_into('>I', d, f, new)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(bytes(d))
    print(f'  main.dol 명령 {len(patch)}곳 패치' + (' (자간 +2)' if SPACING_PATCH else '') + (' (행간 +3)' if LINE_PATCH else ''))


if __name__ == '__main__':
    main()
