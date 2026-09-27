"""일본어 글자번호 → 글자. 판독표 tools/data/labels.json({폰트: {칸: 글자}}) + 문맥 보정.

게임은 일본어를 문자 코드가 아니라 장면 폰트의 칸 번호로 저장한다(상위바이트 0xB0+시트, 하위바이트 0x40+칸).
판독표는 1편 판독과 픽셀이 같은 글자는 자동으로, 나머지는 사람이 검수 시트로 읽어 만들었다(docs/TECHNICAL.md).
모양이 같은 가타카나와 한자·히라가나(エ·工, オ·才, ロ·口, ー·一, ヘ·へ 등)는 앞뒤 글자로 정한다."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

_lab = {f: {int(k): v for k, v in d.items()} for f, d in json.load(open(paths.DATA / 'labels.json', encoding='utf-8')).items()}


def font_of(strname):
    """문자열 파일 이름 → 장면 폰트 이름"""
    b = os.path.basename(strname)
    if '_captions' in b or '_subtitles' in b:
        return b.split('_captions')[0].split('_subtitles')[0]
    if b == 'globjap.str':
        return 'frontend2'
    return b.replace('Japanese.str', '')


def cell(code):
    return ((code >> 8) - 0xB0) * 121 + (code & 0xFF) - 0x40


def labels():
    """{(폰트, 칸): 글자}"""
    return {(f, k): v for f, d in _lab.items() for k, v in d.items()}


KATA = {'ー': '一', 'ニ': '二', 'ロ': '口', 'エ': '工', 'カ': '力', 'タ': '夕', 'ハ': '八', 'ヘ': 'へ', 'ベ': 'べ', 'ペ': 'ぺ',
        'リ': 'り', 'ト': '卜', 'オ': '才', 'チ': '千'}
OTHER = {v: k for k, v in KATA.items()}


def _is_kata(ch):
    return ('ァ' <= ch <= 'ヺ' or ch == 'ー' or ch == 'ヴ') and ch not in OTHER


def _is_kana(ch):
    return 'ぁ' <= ch <= 'ゖ' or 'ァ' <= ch <= 'ヺ'


def _fix1(s):
    out = list(s)
    for i, ch in enumerate(out):
        if ch in KATA or ch in OTHER:
            kata = ch if ch in KATA else OTHER[ch]
            other = KATA[kata]
            prev = out[i - 1] if i else ''
            nxt = s[i + 1] if i + 1 < len(s) else ''
            if kata == 'ー':
                k = _is_kana(prev) or (prev in OTHER or prev in KATA) and _is_kata(nxt)
            elif kata in ('ヘ', 'ベ', 'ペ', 'リ'):  # 히라가나와 짝: 옆이 가타카나면 가타카나
                k = _is_kata(prev) or _is_kata(nxt)
            else:
                k = _is_kata(prev) or _is_kata(nxt) or (nxt in KATA and nxt != ch) or (prev in KATA and prev != ch and i and out[i - 1] in KATA)
            out[i] = kata if k else other
    return ''.join(out)


def _fix2(s):
    """영문 속 모양 혼동(I·!·l, O·0)과 영문 사이 전각 공백"""
    s = re.sub(r'(?<=[A-Z])！(?=[A-Z])|(?<=[A-Z])！(?=[A-Z]?\b)|\b！(?=[A-Z]{2})', 'I', s)
    s = re.sub(r'(?<=[a-z])[！I](?=[a-zI])|(?<=[a-z]I)I', 'l', s)
    s = re.sub(r'(?<=[!-~])　(?=[!-~©])', ' ', s)
    s = re.sub(r'(?<=[（(\d／/])O(?=[／/)）\d])', '0', s)
    return s


def fix_context(s):
    return _fix2(_fix1(_fix1(s)))


def dec(font, text, raw=False):
    """u16 목록 → 일본어 문자열"""
    out = []
    d = _lab.get(font, {})
    for c in text:
        if 0xB000 <= c < 0xC000:
            out.append(d.get(cell(c), '　'))  # 판독표에 없는 칸 = 빈 칸
        else:
            out.append(chr(c))
    s = ''.join(out)
    return s if raw else fix_context(s)
