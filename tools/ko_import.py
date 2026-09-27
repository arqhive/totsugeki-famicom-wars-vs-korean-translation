"""번역 전량 JSON(export_text.py 형식: id, 음성, ko …)의 ko 를 translation/ko/*.json 으로 넣는다.
사용: python tools/ko_import.py work/BW2_텍스트_전량.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kolib


def main(path):
    D = json.load(open(path, encoding='utf-8'))
    ents = []
    for x in D:
        f, i = x['id'].rsplit('#', 1)
        if 'ko' not in x:
            continue
        ents.append(dict(file=f + '.str', index=int(i), speaker=kolib.speaker_of(x.get('음성', '')), ko=x['ko']))
    n = kolib.save_from_entries(ents)
    print(f'번역 {len(ents)}항목 → translation/ko/ {n}개 파일')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1])
