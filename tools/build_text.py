"""번역(translation/ko) → 한국어 .str + 장면별 폰트(.btf/.wdf) → work/build/files/Data/{Strings,font}

폰트 규칙(일본판과 같음):
  - 모든 폰트 칸 0~95 = 원본 ASCII 그대로(글자번호 상위바이트 0 → ASCII 칸)
  - 미션·메뉴·도감 폰트: 96~ = 공통(globjap) 글자(모든 폰트에서 같은 칸), 그 뒤 = 그 폰트 문자열 글자
  - 영상 자막 폰트(1.1_Anglo_Attack 등): 96~ = 자막·캡션 글자만
  - 글자번호 = 0xB000 | 시트<<8 | (0x40 + 칸%121)
글자 그림: 한글 = korglyph.py(1편 방식 맑은 고딕), 그 밖(기호·가나·악센트 문자) = 원본 일본어 폰트의 같은 글자 그림 복사.
시트 팔레트: 0·1·2번 시트는 원본 팔레트가 서로 다르므로 색을 가장 가까운 팔레트 번호로 바꿔 넣는다. 새 시트는 마지막 시트 팔레트.
모든 글자 칸은 0행·0열을 비운다(게임이 위·왼쪽 이웃 칸의 끝으로 섞어 읽음).
번역이 없는 항목(자리표시 등)은 원문 일본어를 그대로 다시 쓴다.
"""
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import btfg
import jpdec
import kolib
import importlib
import paths
import strfile

# 한글 글자 생성기(환경 변수 BW2_GLYPH 로 다른 모듈을 시험할 수 있다)
kg = importlib.import_module(os.environ.get('BW2_GLYPH', 'korglyph'))
OUT = paths.BUILD / 'files' / 'Data'


def pal_rgba(pal_bytes):
    out = []
    for i in range(16):
        v = struct.unpack('>H', pal_bytes[i * 2:i * 2 + 2])[0]
        if v & 0x8000:
            r, g, b, a = (v >> 10 & 31) * 255 / 31, (v >> 5 & 31) * 255 / 31, (v & 31) * 255 / 31, 255
        else:
            r, g, b, a = (v >> 8 & 15) * 17, (v >> 4 & 15) * 17, (v & 15) * 17, (v >> 12 & 7) * 255 / 7
        out.append((r * a / 255, g * a / 255, b * a / 255, a))
    return np.array(out, np.float32)


def idx_map(src_pal, dst_pal):
    """src 팔레트 번호 → dst 팔레트에서 가장 가까운 번호"""
    s, d = pal_rgba(src_pal), pal_rgba(dst_pal)
    return np.array([int(np.argmin(((d - c) ** 2).sum(1))) for c in s], np.uint8)


def code_of(k):
    return 0xB000 | ((k // 121) << 8) | (0x40 + k % 121)


def is_ascii(ch):
    return 0x20 <= ord(ch) < 0x7F


SRC_GLYPH = {}  # 원본 글자 그림 찾기: {글자: [(폰트, 칸)]}
for (f, k), ch in jpdec.labels().items():
    SRC_GLYPH.setdefault(ch, []).append((f, k))
_font_cache = {}


def load_font(name):
    if name not in _font_cache:
        _font_cache[name] = (btfg.load(paths.JP_DATA / 'font' / f'{name}.btf'), open(paths.JP_DATA / 'font' / f'{name}.wdf', 'rb').read())
    return _font_cache[name]


def orig_glyph(ch, prefer):
    """원본 폰트에서 글자 그림 → (22x22 idx, 팔레트 bytes, 폭) 또는 None. 같은 폰트 우선, 팔레트 3 시트 우선"""
    cands = SRC_GLYPH.get(ch)
    if not cands:
        return None
    f, k = sorted(cands, key=lambda fk: (fk[0] != prefer, fk[1] < 363, fk))[0]
    font, w = load_font(f)
    s, c = divmod(k, 121); r, col = divmod(c, 11)
    t = font['texs'][s]
    return t['idx'][r * 22:r * 22 + 22, col * 22:col * 22 + 22].copy(), t['pal'], w[k]


def is_story(font):
    return font[0].isdigit()


def texts_for(sname, ko):
    """str 항목별 최종 문자열(번역 있으면 ko, 없으면 원문 일본어 해독) 목록. 빈 항목은 None"""
    s = strfile.load(paths.JP_DATA / 'Strings' / sname)
    font = jpdec.font_of(sname)
    out = []
    for i, e in enumerate(s['ents']):
        if not e['text']:
            out.append(None)
        elif i in ko.get(sname, {}):
            out.append(ko[sname][i])
        else:
            out.append(jpdec.dec(font, e['text']))
    return s, out


def chars_needed(texts):
    seen = {}
    for t in texts:
        if t is None:
            continue
        for ch in t:
            if ch != '\n' and not is_ascii(ch):
                seen.setdefault(ch, None)
    return list(seen)


def make_font(name, chars):
    orig, ow = load_font(name)
    total = 96 + len(chars)
    nsheets = max(len(orig['texs']), (total + 120) // 121)
    last = orig['texs'][-1]
    texs = []
    for s in range(nsheets):
        base = orig['texs'][s] if s < len(orig['texs']) else last
        idx = np.zeros((256, 256), np.uint8)
        if s == 0:  # ASCII 칸(0~95) 보존
            for k in range(96):
                r, c = divmod(k, 11)
                idx[r * 22:r * 22 + 22, c * 22:c * 22 + 22] = base['idx'][r * 22:r * 22 + 22, c * 22:c * 22 + 22]
        nm = f"{last['name'][:-1]}{s}" if s >= len(orig['texs']) else base['name']
        texs.append(dict(head=base['head'], name=nm, pal=base['pal'], idx=idx))
    kg_pal = last['pal']  # korglyph 팔레트 번호 체계(11 흰색 등) = 일본어 시트 팔레트
    widths = bytearray(ow[:96])
    widths[0] = kg.SPACE  # 공백 폭(한글 간격에 맞춤)
    table = {}
    for j, ch in enumerate(chars):
        k = 96 + j
        s, c = divmod(k, 121); r, col = divmod(c, 11)
        dst_pal = texs[s]['pal']
        if ch in ' 　':
            g, gp, w = np.zeros((22, 22), np.uint8), dst_pal, (kg.ADV if ch == '　' else kg.SPACE)
        elif '가' <= ch <= '힣':
            g, w = kg.render(ch); gp = kg_pal
        else:
            og = orig_glyph(ch, name)
            if og:
                g, gp, w = og
            else:
                g, w = kg.render(ch); gp = kg_pal
        cell = idx_map(gp, dst_pal)[g]
        cell[0, :] = 0; cell[:, 0] = 0
        texs[s]['idx'][r * 22:r * 22 + 22, col * 22:col * 22 + 22] = cell
        widths.append(w)
        table[ch] = k
    (OUT / 'font').mkdir(parents=True, exist_ok=True)
    btfg.save(dict(hdr=orig['hdr'], texs=texs), OUT / 'font' / f'{name}.btf')
    open(OUT / 'font' / f'{name}.wdf', 'wb').write(bytes(widths))
    return table, nsheets


def encode(text, table):
    out = []
    for ch in text:
        if ch == '\n':
            out.append(10)
        elif is_ascii(ch):
            out.append(ord(ch))
        else:
            out.append(code_of(table[ch]))
    return out


def write_str(sname, s, texts, table):
    for e, t in zip(s['ents'], texts):
        if t is not None:
            e['text'] = encode(t, table)
    (OUT / 'Strings').mkdir(parents=True, exist_ok=True)
    open(OUT / 'Strings' / sname, 'wb').write(strfile.build(s))


def main():
    paths.ensure_jp()
    ko = kolib.load_all()
    snames = sorted(p.name for p in (paths.JP_DATA / 'Strings').glob('*Japanese.str'))
    by_font = {}
    for sn in snames:
        by_font.setdefault(jpdec.font_of(sn), []).append(sn)
    gs, gtexts = texts_for('globjap.str', ko)
    glob_chars = chars_needed(gtexts)
    if '　' not in glob_chars:
        glob_chars.append('　')
    report = {}
    tables = {}
    fonts = sorted(p.stem for p in (paths.JP_DATA / 'font').glob('*.wdf'))
    for name in fonts:
        sns = by_font.get(name, [])
        loaded = [texts_for(sn, ko) for sn in sns]
        own = chars_needed([t for _, ts in loaded for t in ts])
        if is_story(name):
            chars = own + (['　'] if '　' not in own else [])
        else:
            chars = glob_chars + [c for c in own if c not in glob_chars]
        tables[name], ns = make_font(name, chars)
        report[name] = (96 + len(chars), ns)
        for sn, (s, ts) in zip(sns, loaded):
            write_str(sn, s, ts, tables[name])
    write_str('globjap.str', gs, gtexts, tables['frontend2'])  # 공통 글자는 모든 미션·메뉴 폰트에서 같은 칸
    big = max(report.items(), key=lambda x: x[1][0])
    print(f'  문자열 {len(snames) + 1}개, 장면 폰트 {len(report)}벌(공통 글자 {len(glob_chars)}자, 최대 {big[0]} {big[1][0]}칸·{big[1][1]}장)')


if __name__ == '__main__':
    main()
