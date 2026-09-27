"""한글 글자 — 1편(돌격!! 패미컴 워즈 GC 한글 패치) 방식.
맑은 고딕 17px를 4배 해상도에서 흰 채움 + 둥근 1px 테두리 + 아래로 2px 내린 그림자로 합성해 22x22 로 줄인다.
2편 칸 규칙에 맞춰 글자마다 잉크 왼끝을 2열에 맞춰 0열을 비우고(테두리 1열), 글자 간격은 19px(1편 18 + 1)로 한다.
팔레트(일본어 시트): 1·3 반투명 검정, 4 검정, 11 흰색, 15 회색."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 4
FONT = 'C:/Windows/Fonts/malgun.ttf'
SIZE = 17
OUT_R = 1.15      # 테두리 반지름(px)
SHADOW_DY = 2     # 그림자 아래 이동(px)
MAX_FILL_W = 16   # 흰 채움 최대 폭(px): 넘는 글자만 가로로 눌러 넣는다
TOP, LEFT = 4, 2  # 기준 글자 '국' 잉크 위끝·왼끝
ADV = 19
SPACE = 7
_font = None
_off = None


def _font_and_offset():
    global _font, _off
    if _font is None:
        _font = ImageFont.truetype(FONT, SIZE * SS)
        img = Image.new('L', (40 * SS, 40 * SS), 0)
        ImageDraw.Draw(img).text((8 * SS, 8 * SS), '국', fill=255, font=_font)
        ys, xs = np.where(np.asarray(img) > 50)
        _off = (8 * SS + LEFT * SS - xs.min(), 8 * SS + TOP * SS - ys.min())
    return _font, _off


def _disk_dilate(a, r):
    k = int(np.ceil(r))
    pad = np.pad(a, k)
    h, w = a.shape
    out = a.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            if dx * dx + dy * dy <= r * r:
                out = np.maximum(out, pad[k + dy:k + dy + h, k + dx:k + dx + w])
    return out


def render(ch):
    """→ (22x22 팔레트 번호, 글자 간격)"""
    font, (ox, oy) = _font_and_offset()
    n = 22 * SS
    img = Image.new('L', (n, n), 0)
    ImageDraw.Draw(img).text((ox, oy), ch, fill=255, font=font)
    hi = np.asarray(img, np.float32) / 255
    xs = np.where(hi.max(0) > 0.05)[0]
    if len(xs):  # 글자마다 잉크 왼끝을 LEFT 열에 맞춘다(ㅇ으로 시작하는 글자가 0열로 나가 잘리지 않게)
        hi = np.roll(hi, LEFT * SS - xs.min(), 1)
    xs = np.where(hi.max(0) > 0.2)[0]
    if len(xs):
        x0, x1 = xs.min(), xs.max() + 1
        lim = MAX_FILL_W * SS
        if x1 - x0 > lim:
            part = Image.fromarray((hi[:, x0:x1] * 255).astype(np.uint8)).resize((lim, n), Image.LANCZOS)
            hi = np.zeros_like(hi)
            hi[:, x0:x0 + lim] = np.asarray(part, np.float32) / 255
    outline_hi = _disk_dilate(hi, OUT_R * SS)
    small = lambda x: np.asarray(Image.fromarray(x.astype(np.float32), 'F').resize((22, 22), Image.BOX), np.float32)
    fill = small(hi)
    out = small(outline_hi)
    sh = np.zeros_like(out); sh[SHADOW_DY:] = out[:-SHADOW_DY]
    black = np.maximum(out, sh)
    idx = np.zeros((22, 22), np.uint8)
    idx[black >= 0.1] = 1
    idx[black >= 0.25] = 3
    idx[black >= 0.5] = 4
    idx[fill >= 0.25] = 15
    idx[fill >= 0.45] = 11
    idx[0, :] = 0; idx[:, 0] = 0
    return idx, ADV
