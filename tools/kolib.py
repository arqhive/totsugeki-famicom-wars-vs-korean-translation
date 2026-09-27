"""translation/ko/*.json 읽기·쓰기.

파일 하나 = 게임 문자열 파일 하나(Data/Strings/<file>).
  {"file": "SP_0.1Japanese.str", "scene": "SP_0.1",
   "entries": [{"index": 1, "speaker": "Qalen", "ko": "..."}, ...]}
index 는 .str 항목 번호, speaker 는 음성 ID 기준 화자(없으면 생략). 원문은 넣지 않는다.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

# 음성 ID(예: SP_0.1_SE_QALEN_001)의 인물 부분 → 화자 코드
SPEAKERS = {'QALEN': 'Qalen', 'FERROK': 'Ferrok', 'HERMAN': 'Herman', 'RETIRED_HERMAN': 'RetiredHerman', 'BETTY': 'Betty',
            'WINDSOR': 'Windsor', 'PIERCE': 'Pierce', 'LEIQO': 'Leiqo', 'AQIRA': 'Aqira', 'UBEL': 'Ubel', 'VLAD': 'Vlad',
            'NOVA': 'Nova', 'GORGI': 'Gorgi', 'GHOST_GORGI': 'GhostGorgi', 'NELLY': 'Nelly', 'AUSTIN': 'Austin'}


def speaker_of(voice_id):
    v = voice_id.decode() if isinstance(voice_id, bytes) else voice_id
    if not v:
        return None
    toks = v.split('_')
    body = '_'.join(toks[1:-1]) if re.fullmatch(r'\d+', toks[-1]) else '_'.join(toks[1:])
    body = re.sub(r'^\d+(\.\d+)?_', '', body)
    for key in sorted(SPEAKERS, key=len, reverse=True):
        if re.search(r'(^|_)' + key + r'$', body):
            return SPEAKERS[key]
    return None


def scene_of(fname):
    if fname == 'globjap.str':
        return 'glob'
    return fname.replace('_Japanese.str', '').replace('Japanese.str', '')


def load_all():
    """→ {str 파일명: {index: ko}}"""
    out = {}
    for p in sorted(paths.KO.glob('*.json')):
        d = json.load(open(p, encoding='utf-8'))
        out[d['file']] = {e['index']: e['ko'] for e in d['entries']}
    return out


def save_from_entries(entries):
    """entries(file, index, speaker, ko) → translation/ko/<scene>.json"""
    paths.KO.mkdir(parents=True, exist_ok=True)
    by = {}
    for x in entries:
        by.setdefault(x['file'], []).append(x)
    for f, xs in by.items():
        ents = []
        for x in sorted(xs, key=lambda x: x['index']):
            e = {'index': x['index']}
            if x.get('speaker'):
                e['speaker'] = x['speaker']
            e['ko'] = x['ko']
            ents.append(e)
        d = {'file': f, 'scene': scene_of(f), 'entries': ents}
        with open(paths.KO / (scene_of(f) + '.json'), 'w', encoding='utf-8', newline='\n') as fp:
            json.dump(d, fp, ensure_ascii=False, indent=1)
            fp.write('\n')
    return len(by)
