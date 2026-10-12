"""시작 로고 영상(BWii_Intro.thp 4:3, BWii_Intro_w.thp 16:9)의 일본어 타이틀 로고 → 한글 로고.
→ work/build/files/Data/Video/  (프레임 수·크기·위치 그대로, 파일 크기 같음, 소리는 원본)

한글판 프레임: tools/assets/video/<영상 이름>/NNNN.png (640×480, 로고가 나오는 137~323번만)
  GPT가 원본 연출(이동·낙하·바운스·축소 위치)을 측정해 한글 로고를 프레임마다 합성한 결과.
  로고 레이어는 tools/assets/video/로고_레이어/.
각 PNG 를 원본 THP 의 같은 번호 프레임 칸 안에 JPEG 로 넣는다(칸에 맞을 때까지 품질을 낮춤).
사용: python tools/build_video.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import thp

VIDEO = paths.JP_FILES / 'Data' / 'Video'
OUT = paths.BUILD / 'files' / 'Data' / 'Video'
FRAMES = paths.ASSETS / 'video'
NAMES = ['BWii_Intro', 'BWii_Intro_w']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        d = bytearray((VIDEO / f'{name}.thp').read_bytes())
        fr = thp.frames(d)
        pngs = sorted((FRAMES / name).glob('*.png'))
        qs = [thp.replace(d, fr[int(p.stem)], Image.open(p).convert('RGB')) for p in pngs]
        (OUT / f'{name}.thp').write_bytes(d)
        print(f'  {name}.thp: 로고 프레임 {len(qs)}장 교체(JPEG 품질 {min(qs)}~{max(qs)})')


if __name__ == '__main__':
    main()
