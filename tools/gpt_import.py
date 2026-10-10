"""GPT 가 다시 그린 그림을 게임용 크기로 맞춰 넣고 원본 | 현재 | GPT 반영 비교 시트를 만든다.

  work/GPT/결과/<번호_이름>.png  →  asset: tools/assets/<이름>.png (바꾸기 전 파일은 work/GPT/이전_assets/ 에 보관)
                                   home : tools/assets/home/<텍스처>.png (흰 글씨·검정 바탕, I4 16단계)
                                   video: tools/assets/video/<이름>.png
  비교 시트: work/GPT/비교/<번호_이름>.png
대상·맞추는 방식은 tools/gpt_jobs.py 참고.
사용: python tools/gpt_import.py              결과 폴더에 있는 것 전부
      python tools/gpt_import.py A01 H03      번호가 A01·H03 으로 시작하는 것만
"""
import glob
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from gpt_jobs import JOBS

GPT = paths.WORK / 'GPT'
FONT = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 14)


def bbox(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        raise SystemExit('그림에서 글자·로고 영역을 찾지 못했습니다(빈 그림?)')
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def alpha_of(im):
    """투명 배경이 아닌 결과(흰·검정·단색 배경)도 받아 준다: 네 귀퉁이 색과 다른 곳을 불투명으로."""
    a = np.asarray(im.convert('RGBA')).astype(np.int32)
    if (a[..., 3] < 250).mean() > 0.05:
        return im.convert('RGBA'), False
    corner = np.median(np.stack([a[0, 0], a[0, -1], a[-1, 0], a[-1, -1]]), 0)
    diff = np.abs(a[..., :3] - corner[:3]).max(2)
    out = a.copy(); out[..., 3] = np.clip((diff - 12) * 8, 0, 255)
    return Image.fromarray(out.astype(np.uint8), 'RGBA'), True


def fit_ink(res, orig, size):
    res, guessed = alpha_of(res)
    if guessed:
        print('    결과 배경이 투명하지 않아 귀퉁이 색을 배경으로 보고 지웠습니다. 비교 시트를 꼭 확인하세요.')
    o = np.asarray(orig.convert('RGBA'))
    omask = o[..., 3] > 16 if (o[..., 3] < 250).mean() > 0.05 else o[..., :3].max(2) > 40
    ox0, oy0, ox1, oy1 = bbox(omask)
    r = res.crop(bbox(np.asarray(res)[..., 3] > 16))
    s = min((ox1 - ox0) / r.width, (oy1 - oy0) / r.height)
    r = r.resize((max(1, round(r.width * s)), max(1, round(r.height * s))), Image.LANCZOS)
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    out.alpha_composite(r, (ox0 + (ox1 - ox0 - r.width) // 2, oy0 + (oy1 - oy0 - r.height) // 2))
    return out


def fit_frame(res, orig, size):
    return res.convert('RGB').resize(size, Image.LANCZOS).convert('RGBA')


def fit_text(res, orig, size):
    """흰 글씨(검정 바탕 또는 투명 바탕) → 글자 높이를 원본 글자 높이에 맞춘 흰 글씨·검정 바탕 L 그림(16단계)"""
    a = np.asarray(res.convert('RGBA')).astype(np.float32)
    lum = a[..., :3].max(2) * (a[..., 3] / 255)
    if np.median(lum) > 128:  # 흰 바탕 검정 글씨로 왔으면 뒤집기
        lum = 255 - lum
    g = Image.fromarray(lum.astype(np.uint8), 'L')
    g = g.crop(bbox(np.asarray(g) > 40))
    ox0, oy0, ox1, oy1 = bbox(np.asarray(orig.convert('L')) > 40)
    h = oy1 - oy0
    w = round(g.width * h / g.height)
    if w > size[0] - 8:
        w = size[0] - 8; h = round(g.height * w / g.width)
    g = g.resize((w, h), Image.LANCZOS)
    cx = (ox0 + ox1) // 2
    x = min(max(cx - w // 2, 4), size[0] - 4 - w)
    y = oy0 + ((oy1 - oy0) - h) // 2
    out = Image.new('L', size, 0); out.paste(g, (x, y))
    q = (np.asarray(out) // 17 * 17).astype(np.uint8)  # I4 = 16단계
    return Image.fromarray(q, 'L').convert('RGBA')


def checker(size):
    bg = Image.new('RGBA', size, (150, 150, 150, 255)); d = ImageDraw.Draw(bg)
    for y in range(0, size[1], 8):
        for x in range(0, size[0], 8):
            if (x // 8 + y // 8) % 2:
                d.rectangle([x, y, x + 7, y + 7], fill=(110, 110, 110, 255))
    return bg


def sheet(name, imgs, out):
    k = max(1, min(4, 300 // max(im.width for _, im in imgs)))
    tiles = []
    for label, im in imgs:
        im = im.convert('RGBA').resize((im.width * k, im.height * k), Image.NEAREST)
        t = checker(im.size); t.alpha_composite(im)
        tiles.append((label, t))
    W = sum(t.width for _, t in tiles) + 12 * (len(tiles) + 1)
    H = max(t.height for _, t in tiles) + 50
    S = Image.new('RGB', (W, H), (40, 40, 40)); d = ImageDraw.Draw(S)
    d.text((12, 6), name, font=FONT, fill=(255, 255, 255))
    x = 12
    for label, t in tiles:
        d.text((x, 26), label, font=FONT, fill=(255, 220, 0)); S.paste(t.convert('RGB'), (x, 46)); x += t.width + 12
    S.save(out)


def main(prefixes):
    done = 0
    for name, kind, src, out, size, fit, text in JOBS:
        if prefixes and not any(name.startswith(p) for p in prefixes):
            continue
        res_path = GPT / '결과' / f'{name}.png'
        if not res_path.exists():
            continue
        if kind == 'home':
            orig = Image.open(glob.glob(glob.escape(str(GPT / '원본')) + f'/{name}_원본_{size[0]}x{size[1]}.png')[0])
        else:
            orig = Image.open(paths.WORK / src)
        res = Image.open(res_path)
        if res.size == tuple(size):  # 이미 게임 크기로 맞춰 온 결과는 위치·크기를 건드리지 않는다
            if fit == 'text':
                q = np.asarray(res.convert('L'))
                if np.median(q) > 128:
                    q = 255 - q
                new = Image.fromarray((q // 17 * 17).astype(np.uint8), 'L').convert('RGBA')
            else:
                new = res.convert('RGBA')
        else:
            new = {'ink': fit_ink, 'frame': fit_frame, 'text': fit_text}[fit](res, orig, size)
        if kind == 'asset':
            dst = paths.ASSETS / out
            (GPT / '이전_assets').mkdir(exist_ok=True)
            bak = GPT / '이전_assets' / out
            if not bak.exists():
                shutil.copy2(dst, bak)
            cur = Image.open(dst).convert('RGBA')  # 덮어쓰기 전에 읽어 둔다
        else:
            dst = paths.ASSETS / kind / out
            dst.parent.mkdir(parents=True, exist_ok=True)
            cur = Image.open(dst).convert('RGBA') if dst.exists() else orig
        (new.convert('L') if kind == 'home' else new).save(dst)
        (GPT / '비교').mkdir(exist_ok=True)
        sheet(f'{name}  ({size[0]}x{size[1]}, {text})', [('원본', orig), ('현재', cur), ('GPT 반영', new)],
              GPT / '비교' / f'{name}.png')
        print(f'  {name} → {paths.rel(dst)}')
        done += 1
    print(f'반영 {done}개' + ('' if done else ' — work/GPT/결과/ 에 "번호_이름.png" 로 저장했는지 확인하세요'))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1:])
