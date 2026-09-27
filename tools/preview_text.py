"""빌드된 str+폰트로 문장을 그려 확인(게임 폭 규칙 근사: 글자폭=wdf).
사용: python tools/preview_text.py 출력.png 폰트:str파일:항목번호 …"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, btfg, strfile
import paths


def rgb5a3(v):
    v = v.astype(np.uint32); op = (v & 0x8000) != 0
    out = np.zeros(v.shape + (4,), np.uint8)
    out[..., 0] = np.where(op, ((v >> 10) & 31) * 255 // 31, ((v >> 8) & 15) * 17)
    out[..., 1] = np.where(op, ((v >> 5) & 31) * 255 // 31, ((v >> 4) & 15) * 17)
    out[..., 2] = np.where(op, (v & 31) * 255 // 31, (v & 15) * 17)
    out[..., 3] = np.where(op, 255, ((v >> 12) & 7) * 255 // 7)
    return out
from PIL import Image, ImageDraw
B = paths.BUILD / 'files' / 'Data'
SPACING = 0  # DOL 자간 패치(시험6부터 없음)
LINE = 22    # 칸 22(원본 행간)


def render(font, codes):
    f = btfg.load(f'{B}/font/{font}.btf'); w = open(f'{B}/font/{font}.wdf', 'rb').read()
    pals = [rgb5a3(np.frombuffer(t['pal'], '>u2')) for t in f['texs']]
    lines = [[]]
    for c in codes:
        if c == 10: lines.append([]); continue
        k = (c - 0x20) if c < 0x100 else ((c >> 8) - 0xB0) * 121 + (c & 0xFF) - 0x40
        lines[-1].append(k)
    W = max(sum(w[k] + SPACING for k in l) for l in lines) + 8 if any(lines) else 10
    img = Image.new('RGBA', (max(W, 10), LINE * len(lines) + 4), (40, 60, 90, 255))
    for y, l in enumerate(lines):
        x = 4
        for k in l:
            s, c = divmod(k, 121); r, col = divmod(c, 11)
            cell = pals[s][f['texs'][s]['idx'][r * 22:r * 22 + 22, col * 22:col * 22 + 22]]
            img.alpha_composite(Image.fromarray(cell, 'RGBA'), (x, 2 + y * LINE)); x += w[k] + SPACING
    return img


if __name__ == '__main__':
    reqs = [a.split(':') for a in sys.argv[2:]]
    ims = []
    for font, sname, i in reqs:
        e = strfile.load(f'{B}/Strings/{sname}')['ents'][int(i)]
        ims.append(render(font, e['text']))
    Wd = max(i.width for i in ims); H = sum(i.height + 4 for i in ims)
    c = Image.new('RGBA', (Wd, H), (20, 20, 20, 255)); y = 0
    for i in ims: c.alpha_composite(i, (0, y)); y += i.height + 4
    c.save(sys.argv[1])
