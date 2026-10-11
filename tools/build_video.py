"""시작 로고 영상(BWii_Intro.thp 4:3, BWii_Intro_w.thp 16:9)의 일본어 타이틀 로고 → 한글 로고(tools/assets/video/영상로고.png).
→ work/build/files/Data/Video/  (프레임 크기·위치 그대로, 파일 크기 같음)

기준: AttractMode.thp 2772번 프레임의 로고. 한글 로고 그림(497x178, '캔버스')은 이 프레임의 (72,51)~(569,229) 상자에 대응.
배치: 로고 전체 밝기 정렬(ECC, 확대·이동만). 원본 로고는 166~240·253~끝 프레임에서 정지 → 값 하나로 고정
      (「VS」 상자는 JPEG 잡음으로 높이가 41↔37px 튀어서 출발점으로만 쓴다).
애니메이션은 원본을 따른다:
  ~165  「ファミコンウォーズ」가 병사 뒤로 미끄러져 들어온다 → 줄 높이(병사 제외)를 지우고 「패미컴 워즈」를 같은 위치에(들어오는 첫 몇 프레임만 가로 흐림)
  166~  일본어 로고를 통째로 지우고 한글 로고를 한 장으로 그린다(조각 이음매 없음).
        「돌격!!」은 떨어지는 동안만 따로(세로 흐림), FAMICOM WARS 는 원본이 총으로 써지는 만큼 왼쪽부터 드러낸다.
        로고 밖(날아다니는 병사·조각)은 원본 그대로. 끝 정지 구간은 원본 VS 밝기를 따라 페이드.
사용: python tools/build_video.py [--preview]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import thp

VIDEO = paths.JP_FILES / 'Data' / 'Video'
OUT = paths.BUILD / 'files' / 'Data' / 'Video'
LOGO = paths.ASSETS / 'video' / '영상로고.png'
REF_VIDEO, REF_FRAME, REF_BOX = 'AttractMode.thp', 2772, (72, 51, 569, 229)
FILES = ['BWii_Intro.thp', 'BWii_Intro_w.thp']
FIRST, LAST, SETTLED = 126, 323, 166
W, H = 640, 480


def lum(a):
    return a.max(2).astype(np.float32)


def red_mask(a):
    a = a.astype(np.int32); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 14) & (r * 10 > g * 16) & (r * 10 > b * 16)


def yellow_mask(a):
    a = a.astype(np.int32); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 70) & (g > 55) & (b * 10 < g * 6) & (r - b > 45)


def vs_box(a):
    m = ndimage.binary_opening(red_mask(a), iterations=1)
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=3))
    if n == 0:
        return None
    sizes = ndimage.sum(m, lab, range(1, n + 1)); k = int(np.argmax(sizes)) + 1
    if sizes[k - 1] < 300:
        return None
    ys, xs = np.where((lab == k) & m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def warp(img, M):
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


class Ref:
    def __init__(self):
        d = open(VIDEO / REF_VIDEO, 'rb').read()
        a = np.asarray(thp.decode(d, thp.frames(d)[REF_FRAME]))
        self.box = vs_box(a)
        x0, y0, x1, y1 = REF_BOX
        self.rgb = np.zeros((H, W, 3), np.float32); self.rgb[y0:y1, x0:x1] = a[y0:y1, x0:x1]
        L = lum(self.rgb)
        self.body = (L > 40).astype(np.float32)
        self.jp = ndimage.binary_dilation(L > 14, iterations=7).astype(np.float32)  # 지울 자리(테두리까지 넉넉히)
        k = np.asarray(Image.open(LOGO).convert('RGBA')).astype(np.float32) / 255
        assert k.shape[:2] == (y1 - y0, x1 - x0), k.shape
        self.ko = np.zeros((H, W, 4), np.float32); self.ko[y0:y1, x0:x1] = k
        cy, cx = np.mgrid[0:y1 - y0, 0:x1 - x0]
        regions = {1: (cy < 78) & (cx < 172), 2: (cy < 78) & (cx >= 172) & (cx < 322), 3: (cy >= 78) & (cx < 322), 4: cx >= 322}
        self.part = {}
        for p, m in regions.items():
            full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = m; self.part[p] = full
        # 한글 로고 조각 구역(테두리가 잘리지 않게 한글 그림에 맞춰 넉넉히): 돌격!! / FAMICOM WARS / 패미컴 워즈★ / VS
        # (x≈316~327 은 FAMICOM WARS 줄 테두리와 V 테두리가 붙어 있다 → V 쪽에 넣어야 V 가 비지 않는다)
        kregions = {1: (cy < 84) & (cx < 184), 2: (cy < 80) & (cx >= 184) & (cx < 316), 3: (cy >= 84) & (cx < 338) | (cy >= 80) & (cx >= 184) & (cx < 338),
                    4: (cx >= 338) | (cy < 80) & (cx >= 316)}
        kk = np.asarray(Image.open(LOGO).convert('RGBA')).astype(np.int32)
        white = (kk[..., :3].min(2) > 150) & (kk[..., 3] > 40)  # 흰 글자(FAMICOM WARS)
        white = ndimage.binary_dilation(white, iterations=1)
        edge = (cy < 80) & (cx >= 316) & (cx < 330) & white   # S 끝 흰 글자는 FAMICOM WARS 쪽
        kregions[2] = kregions[2] | edge
        kregions[4] = kregions[4] & ~edge
        self.kpart = {}
        for p, m in kregions.items():
            full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = m; self.kpart[p] = full
        self.cx = np.zeros((H, W), np.float32); self.cx[y0:y1, x0:x1] = cx  # 캔버스 x 좌표(FAMICOM WARS 써지는 만큼 드러낼 때)

    def matrix(self, box):
        rx0, ry0, rx1, ry1 = self.box; x0, y0, x1, y1 = box
        sx = (x1 - x0) / (rx1 - rx0); sy = (y1 - y0) / (ry1 - ry0)
        return np.float32([[sx, 0, x0 - sx * rx0], [0, sy, y0 - sy * ry0]])


def blur_piece(ko, mask, dx=0, dy=0):
    """한글 로고 조각(RGBA, 0~1)을 움직인 거리만큼 가로·세로로 흐리게(원본의 모션 블러 흉내)"""
    a = ko[..., 3] * mask; rgb = ko[..., :3] * a[..., None]
    for d, horiz in ((dx, True), (dy, False)):
        n = int(min(abs(d), 60))
        if n >= 3:
            k = np.zeros((1, n) if horiz else (n, 1), np.float32) + 1.0 / n
            rgb = cv2.filter2D(rgb, -1, k, borderType=cv2.BORDER_CONSTANT)
            a = cv2.filter2D(a, -1, k, borderType=cv2.BORDER_CONSTANT)
    return rgb, a


def paste(base, rgb, a):
    return base * (1 - a[..., None]) + rgb * 255


def soldier_keep(a, L, y0b, y1b):
    """병사 = 로고 줄 위아래 밖까지 이어진 회색 덩어리(로고 테두리의 흰 선도 회색이라 덩어리 단위로 가른다)"""
    grey = ndimage.binary_closing((L > 70) & ((a.max(2).astype(int) - a.min(2)) < 70), iterations=2)
    lab, n = ndimage.label(grey)
    keep = np.zeros(L.shape, bool)
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is not None and (sl[0].start < y0b - 2 or sl[0].stop > y1b + 2):
            keep |= lab == k
    return ndimage.binary_fill_holes(ndimage.binary_dilation(keep, iterations=2))


def frame_out(ref, a, M, i, st):
    """안 B: 「FAMICOM WARS」·「VS」는 원본 애니메이션 그대로(영어), 「突撃!!」·「ファミコンウォーズ」만 같은 움직임의 한글 조각으로."""
    L = lum(a); f = a.astype(np.float32)
    parts = {p: warp(m, M) > 0.5 for p, m in ref.part.items()}
    jp = np.clip(warp(ref.jp, M), 0, 1) > 0.5
    vx = np.where(parts[4].any(0))[0].min()
    r3 = np.where(parts[3].any(1))[0]; r1 = np.where(parts[1].any(1))[0]
    c1 = np.where(parts[1].any(0))[0]
    y3a, y3b = max(r3.min() - 10, 0), r3.max() + 10
    keep = soldier_keep(a, L, y3a, y3b)
    yel = yellow_mask(a)
    changed = False
    # ── 「ファミコンウォーズ」 → 「패미컴 워즈」
    band = np.zeros(L.shape, bool); band[y3a:y3b, :vx + 2] = True
    y3 = ndimage.binary_opening(yel & band, iterations=1)
    if i < SETTLED:
        if y3.sum() >= 40:
            dx = int(np.where(y3.any(0))[0].max() - np.where((parts[3] & jp).any(0))[0].max())
            if st.get('dx_done') or abs(dx) <= 8:  # 거의 다 들어왔으면 제자리에 딱 붙인다(병사 겹침으로 측정이 떨림)
                dx = 0; st['dx_done'] = True
            vel = dx - st.get('dx', dx); st['dx'] = dx
            vel = vel if (abs(vel) >= 14 and i < 145) else 0  # 원본도 흐린 건 들어오는 첫 몇 프레임뿐
            f = f * (1 - (band & ~keep))[..., None]                       # 줄 높이 전부(병사 제외) 지움
            Mx = M.copy(); Mx[0, 2] += dx
            rgb, al = blur_piece(warp(ref.ko, Mx), warp(ref.part[3], Mx), dx=vel)
            f = paste(f, rgb, al); f[keep] = a[keep]; changed = True
        return np.clip(f, 0, 255).astype(np.uint8) if changed else None
    return settled_out(ref, a, M, i, st, parts, jp, L, yel, r1, c1, vx)


def settled_out(ref, a, M, i, st, parts, jp, L, yel, r1, c1, vx):
    """VS 가 자리 잡은 뒤: 일본어 로고 전체를 지우고 한글 로고를 한 장으로 그린다(조각 이음매 없음).
    「돌격!!」은 떨어지는 동안만 따로, FAMICOM WARS 는 원본이 써지는 만큼 왼쪽부터 드러낸다. 로고 밖(날아다니는 조각·병사)은 원본."""
    f = a.astype(np.float32)
    ys = np.where(jp.any(1))[0]; x0 = np.where(jp.any(0))[0].min()
    # 지울 곳: 일본어 로고 + 로고 위쪽 띠(떨어지는 「突撃!!」 잔상, 원본 윗 테두리). 노랗지 않은 큰 덩어리(병사·조각)는 남긴다.
    top = np.zeros(L.shape, bool); top[max(ys.min() - 40, 0):ys.min() + 6, max(x0 - 8, 0):vx + 2] = True
    col = np.zeros(L.shape, bool); col[:r1.max() + 4, max(c1.min() - 12, 0):c1.max() + 22] = True
    zone = top | (col & ~parts[2] & ~parts[3])
    lab, n = ndimage.label((L > 12) & zone)
    big = np.zeros(L.shape, bool)
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        comp = lab[sl] == k
        if comp.sum() > 400 and yel[sl][comp].mean() < 0.2 and (jp[sl][comp]).mean() < 0.5:
            big[sl] |= comp
    erase = (jp | (zone & ~ndimage.binary_dilation(big, iterations=1))).astype(np.float32)
    f = f * (1 - erase[..., None])
    # 페이드(끝 정지 구간): 원본 VS 밝기 비율
    al = 1.0
    if i >= STILL2:
        al = min(1.0, float(lum(a)[parts[4] & jp].mean()) / st['vs_lum'])
    ko = warp(ref.ko, M)
    mask = warp(ref.kpart[3], M) + warp(ref.kpart[4], M)
    # FAMICOM WARS: 원본에 써진 만큼
    white = (L > 60) & ((a.max(2).astype(int) - a.min(2)) < 60) & parts[2] & jp
    if white.sum() >= 0.85 * st['p2_full']:
        mask += warp(ref.kpart[2], M)
    elif white.sum() > 20:
        cut = (np.where(white.any(0))[0].max() + 2 - M[0, 2]) / M[0, 0] - REF_BOX[0]
        mask += warp(ref.kpart[2], M) * (warp(ref.cx, M) <= cut)
    # 「돌격!!」: 떨어지는 중이면 그 위치·세로 흐림으로 따로
    y1 = yel & col & ~parts[2] & ~parts[3]
    lit = (L > 50) & parts[1] & jp
    dy = None
    if st.get('dy_done') or (lit.sum() > 0.55 * (parts[1] & jp).sum() and y1[:r1.min() - 6].sum() < 30):
        dy = 0; st['dy_done'] = True
    elif y1.sum() > 40:
        dy = int(np.where(y1.any(1))[0].max() - np.where((parts[1] & jp).any(1))[0].max())
        if abs(dy) <= 8:
            dy = 0; st['dy_done'] = True
    if dy == 0:
        mask += warp(ref.kpart[1], M)
    rgb, a2 = blur_piece(ko, np.clip(mask, 0, 1))
    f = paste(f, rgb * al, a2 * al)
    if dy:
        vel = dy - st.get('dy', dy - 40); st['dy'] = dy
        M1 = M.copy(); M1[1, 2] += dy
        rgb, a1 = blur_piece(warp(ref.ko, M1), warp(ref.kpart[1], M1), dy=vel)
        f = paste(f, rgb, a1)
    return np.clip(f, 0, 255).astype(np.uint8)


TPL = 230          # 로고가 다 갖춰지고 멈춰 있는 기준 프레임
STILL1 = 240       # SETTLED~이 프레임까지 원본 로고는 정지(ECC 로 0.1px 이하 확인)
STILL2 = 253       # 이 프레임부터 끝까지 다시 정지(위로 올라가며 작아진 뒤)


def similar(A):
    """아핀 → 같은 배율·회전 없음(로고는 확대·이동만 한다)"""
    s = (A[0, 0] + A[1, 1]) / 2
    return np.float32([[s, 0, A[0, 2]], [0, s, A[1, 2]]])


def ecc(tmpl, img, mask, A0):
    try:
        c, A = cv2.findTransformECC(tmpl, img, A0.astype(np.float32).copy(), cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), mask, 5)
        return A, float(c)
    except cv2.error:
        return None, 0.0


def track(ref, rgb):
    """프레임별 캔버스→화면 변환. 「VS」 상자는 JPEG 잡음으로 높이가 41↔37px 튀므로 출발점으로만 쓰고,
    로고 전체 밝기 정렬(ECC)로 잰 뒤 배율을 가로세로 같게 묶는다. 정지 구간은 값 하나로 고정."""
    t = rgb[TPL]
    # 캔버스(기준 영상 로고) → 이 영상 기준 프레임
    A0 = ref.matrix(vs_box(t))
    A0 = np.float32([[A0[0, 0], 0, A0[0, 2]], [0, A0[0, 0], A0[1, 2]]])
    Mv, c = ecc(lum(ref.rgb) / 255, lum(t) / 255, (ref.jp > 0.5).astype(np.uint8), A0)
    assert Mv is not None and c > 0.9, ('기준 정렬 실패', c)
    Mv = similar(Mv)
    # 기준 프레임 → 각 프레임(움직이는 구간만)
    tm = lum(t) / 255
    tmask = (ndimage.binary_dilation(lum(t) > 20, iterations=6)).astype(np.uint8)
    tb = vs_box(t)
    A = {}
    prev = np.float32([[1, 0, 0], [0, 1, 0]])
    for i in range(STILL1 + 1, LAST + 1):
        b = vs_box(rgb[i])
        if b:  # 상자 너비로 배율·위치 대략 → ECC 로 다듬기
            s = (b[2] - b[0]) / (tb[2] - tb[0])
            guess = np.float32([[s, 0, b[0] - s * tb[0]], [0, s, b[3] - s * tb[3]]])
        else:
            guess = prev
        best = (None, 0)
        for g in (prev, guess):
            Ai, ci = ecc(tm, lum(rgb[i]) / 255, tmask, g)
            if Ai is not None and ci > best[1] and abs(Ai[0, 1]) < 0.05 and abs(Ai[1, 0]) < 0.05:
                best = (Ai, ci)
        A[i] = similar(best[0]) if best[1] > 0.85 else guess
        prev = A[i]
    end = np.median(np.stack([A[i] for i in range(STILL2, LAST + 1)]), 0).astype(np.float32)
    h = lambda m: np.vstack([m, [0, 0, 1]]).astype(np.float64)
    out = {}
    for i in range(SETTLED, LAST + 1):
        Ai = np.float32([[1, 0, 0], [0, 1, 0]]) if i <= STILL1 else (end if i >= STILL2 else A[i])
        out[i] = (h(Ai) @ h(Mv))[:2].astype(np.float32)
    return out


def process(name, ref, preview=None):
    d = bytearray(open(VIDEO / name, 'rb').read()); fr = thp.frames(d)
    rgb = {i: np.asarray(thp.decode(d, fr[i])) for i in range(FIRST, LAST + 1)}
    Ms = track(ref, rgb)
    shots = {}; qs = []; st = {}
    pt = {p: vl > 0.5 for p, vl in ((p, warp(m, Ms[TPL])) for p, m in ref.part.items())}
    jt = warp(ref.jp, Ms[TPL]) > 0.5; t = rgb[TPL]; Lt = lum(t)
    st['vs_lum'] = float(Lt[pt[4] & jt].mean())
    st['p2_full'] = int(((Lt > 60) & ((t.max(2).astype(int) - t.min(2)) < 60) & pt[2] & jt).sum())
    for i in range(FIRST, LAST + 1):
        M = Ms[max(i, SETTLED)]
        out = frame_out(ref, rgb[i], M, i, st)
        if out is None:
            continue
        if preview is not None:
            if i in preview:
                shots[i] = (rgb[i], out)
            continue
        qs.append(thp.replace(d, fr[i], Image.fromarray(out)))
    if preview is not None:
        return shots
    OUT.mkdir(parents=True, exist_ok=True)
    open(OUT / name, 'wb').write(bytes(d))
    return len(qs), min(qs), max(qs)


def main(preview=False):
    ref = Ref()
    if not preview:
        for name in FILES:
            n, q0, q1 = process(name, ref)
            print(f'  {name}: 로고 프레임 {n}장 교체(JPEG 품질 {q0}~{q1})')
        return
    F = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 14)
    picks = list(range(136, 166, 3)) + list(range(166, 180, 2)) + list(range(182, 324, 10))
    for name in FILES:
        shots = process(name, ref, preview=set(picks))
        tiles = []
        for i in sorted(shots):
            a, b = shots[i]
            t = Image.new('RGB', (480, 200)); t.paste(Image.fromarray(a).resize((240, 180)), (0, 20)); t.paste(Image.fromarray(b).resize((240, 180)), (240, 20))
            ImageDraw.Draw(t).text((4, 2), f'#{i}', font=F, fill=(255, 255, 0)); tiles.append(t)
        cols = 3; S = Image.new('RGB', (480 * cols, ((len(tiles) + cols - 1) // cols) * 202), (50, 0, 0))
        for n, t in enumerate(tiles):
            S.paste(t, (n % cols * 480, n // cols * 202))
        out = paths.WORK / f'opening_preview_{name.split(".")[0]}.jpg'; S.save(out, quality=85); print('미리보기', out)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main('--preview' in sys.argv)
