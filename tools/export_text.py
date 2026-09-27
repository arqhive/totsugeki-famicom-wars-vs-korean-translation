"""원문 대조용 전량 JSON: 일본어 원문(판독표로 해독)·영어(같은 디스크의 영어 파일)·화자·번역을 나란히 → work/BW2_텍스트_전량.json
사용: python tools/export_text.py
이 파일의 ko 를 고친 뒤 python tools/ko_import.py work/BW2_텍스트_전량.json 으로 되돌려 넣을 수 있다."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpdec
import kolib
import paths
import strfile

OUT = paths.WORK / 'BW2_텍스트_전량.json'
KO_NAME = {'Qalen': '콰렌', 'Aqira': '아퀼라', 'Leiqo': '레이쿼', 'Ferrok': '페록', 'Herman': '허먼', 'RetiredHerman': '허먼(퇴역)',
           'Betty': '베티', 'Windsor': '윈저', 'Pierce': '피어스', 'Austin': '오스틴', 'Nova': '노바', 'Gorgi': '고르기',
           'GhostGorgi': '고르기(망령)', 'Vlad': '블라드', 'Ubel': '우벨', 'Nelly': '넬리'}
ORDER = {'공통': 0, '메뉴': 1, '캠페인 미션': 2, '영상 자막': 3, '영상 캡션': 4, '대전 맵': 5, '유닛 도감': 6, '설정 자료': 7, '크레딧': 8}


def category(b):
    if b == 'globjap.str': return '공통'
    if '_subtitles' in b: return '영상 자막'
    if '_captions' in b: return '영상 캡션'
    if b.startswith('frontend2'): return '메뉴'
    if b.startswith('SP_'): return '캠페인 미션'
    if b.startswith('MP'): return '대전 맵'
    if b.startswith('fe_units'): return '유닛 도감'
    if b.startswith('fe_concept'): return '설정 자료'
    if b.startswith('credits'): return '크레딧'
    return '기타'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    S = paths.ensure_jp() / 'Strings'
    ko = kolib.load_all()
    files = sorted({p.name for p in S.glob('*Japanese.str')} | {'globjap.str'}, key=lambda b: (ORDER.get(category(b), 9), b))
    out = []; first = {}
    for b in files:
        enf = S / b.replace('globjap', 'globeng').replace('Japanese', 'English')
        en = strfile.load(enf)['ents'] if enf.exists() else []
        font = jpdec.font_of(b)
        for i, e in enumerate(strfile.load(S / b)['ents']):
            if not e['text']:
                continue
            jp = jpdec.dec(font, e['text'])
            if jp.strip(' 　!') == '' or jp == 'EMPTY':
                continue
            eid = f'{b[:-4]}#{i}'
            item = {'id': eid, '분류': category(b), 'jp': jp}
            sp = kolib.speaker_of(e['voice_id'])
            if sp:
                item['화자'] = KO_NAME[sp]
            if i < len(en) and en[i]['text']:
                item['en'] = ''.join(map(chr, en[i]['text'])).replace('\\n', '\n')
            if e['voice_id']:
                item['음성'] = e['voice_id'].decode()
            if jp in first:
                item['같은문장'] = first[jp]
            else:
                first[jp] = eid
            if i in ko.get(b, {}):
                item['ko'] = ko[b][i]
            out.append(item)
    json.dump(out, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(f'{OUT}: {len(out)}항목(고유 원문 {len(first)}개, 번역 {sum("ko" in x for x in out)}항목)')


if __name__ == '__main__':
    main()
