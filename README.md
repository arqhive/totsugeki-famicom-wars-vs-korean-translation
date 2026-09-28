# 돌격!! 패미컴 워즈 VS (Wii) 한글 패치

*Totsugeki!! Famicom Wars VS* (Wii, 일본판 `RBWJ01`) 비공식 한국어 팬 패치입니다.
대사는 일본어판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v0.1.1](../../releases/tag/v0.1.1)**

- 대사 전체를 한글화했습니다(캠페인 미션 20개와 대전 맵의 무전 대사·목표, 스토리 영상 자막 12편).
- 메뉴 전체를 한글화했습니다(메인 메뉴, 설정, 저장 메시지, 유닛 도감, 설정 자료, 크레딧).
- 타이틀 로고, 뒤로 버튼, 리모컨 스트랩 경고 화면, Wii 메뉴 채널 배너, 세이브 데이터 로고를 한글화했습니다.
- 장면마다 쓰인 한글만 모아 게임 폰트를 새로 만들었습니다. 1편 한글 패치와 같은 흰 글씨·검은 테두리·그림자 모양입니다.
- **파일 단위 패처라 덤프·변환 형태가 달라도 적용되고, 패치 크기는 약 7MB입니다.**

> 이 저장소에는 **게임 데이터(롬·디스크 이미지, 추출한 원문 대사, 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 디스크 이미지(게임 ID `RBWJ01`). 북미판(Battalion Wars 2)·유럽판에는 적용할 수 없습니다.
  - ISO, WBFS, WBFS에서 변환한 ISO 모두 됩니다. 덤프·변환 방법에 따라 MD5가 달라도 게임 파일만 같으면 적용됩니다.
  - RVZ는 Dolphin에서 ISO로 바꾼 뒤 적용하세요.
- Windows 10 이상. 패처에 필요한 도구(wit, xdelta3)가 들어 있어 따로 설치할 것이 없습니다.
- 빈 공간 약 10GB(풀어 둔 파일과 결과 이미지).

### 적용 방법

1. [배포 페이지](../../releases/latest)에서 `TotsugekiFamicomWarsVS_KO_v0.1.1.zip`을 받아 압축을 풉니다.
2. 원본 이미지를 `패치하기.bat` 위에 끌어다 놓습니다. 원본을 같은 폴더에 두고 더블클릭해도 됩니다.
3. 1분 정도 지나면 원본과 같은 폴더에 `Totsugeki!! Famicom Wars VS (Korean) [RBWJ01].iso`가 생깁니다. 원본이 WBFS면 결과도 WBFS입니다.

패처는 이미지를 풀어 바뀐 게임 파일 199개에만 파일별 차분을 적용하고 다시 묶습니다. 파일마다 적용 전후 MD5를 검사하므로, 원본이 다르거나 이미 패치한 이미지면 멈추고 알려 줍니다.
결과 이미지의 MD5는 원본 덤프에 따라 달라질 수 있지만 게임 내용은 같습니다.

자세한 방법은 [`README_한국어.txt`](release/README_한국어.txt)를 참고하세요.

### 실행 환경

- **확인함**: Dolphin, Wii U vWii(USB Loader GX).

### 알려진 문제

- 한글이 일본어보다 길어 일부 대사가 상자 테두리를 조금 벗어납니다. 글자 크기를 줄이지 않고 가독성을 우선했습니다. 미션 설명 화면의 문장은 상자 안에 들어가도록 다듬었습니다.
- 승리·패배 연출 글자(VICTORY, DEFEAT)는 일본판 원본부터 영문 디자인이라 그대로 두었습니다.
- 이름 입력 화면의 글자판은 원본대로 가나입니다.

## 개발자용: 직접 빌드

### 요구 사항

- Python 3.11 이상. `pip install -r requirements.txt`로 numpy, Pillow를 설치합니다.
- 일본판 ISO. 저장소 루트나 `iso/`에 `Totsugeki!! Famicom Wars VS (Japan) [RBWJ01].iso`로 두거나 환경 변수 `BW2_JP_ISO`로 지정합니다.
- 맑은 고딕(`C:/Windows/Fonts/malgun.ttf`). 한글 글자를 그리는 데 씁니다.
- [Dolphin](https://dolphin-emu.org/)의 `DolphinTool`. 원본 추출과 결과 검증에 씁니다. 바탕화면의 `Dolphin-x64` 폴더에 있거나 환경 변수 `DOLPHIN_TOOL`로 지정합니다.
- [wit](https://wit.wiimm.de/)(Wiimms ISO Tools). 원본 배치를 유지한 ISO를 만들 때 씁니다. `tools/bin/wit-v3.05a-r8638-cygwin64/`에 두거나 PATH, 환경 변수 `WIT`로 지정합니다.
- xdelta3 3.1.0. 배포용 패처를 만들 때만 필요하며, `tools/bin/xdelta3.exe`나 PATH, 환경 변수 `XDELTA3`로 둡니다.

### 빌드

```bash
# 한글 ISO 만들기 (work/TotsugekiFamicomWarsVS_KO.iso)
python tools/build.py

# 배포용 패처: 바뀐 파일별 차분 + 패처 스크립트 + wit·xdelta3 → release/TotsugekiFamicomWarsVS_KO_v0.1.1.zip
python tools/make_patcher.py 0.1.1

# (v0.1 방식) ISO 통째 xdelta. 특정 원본 ISO에만 맞아 배포에는 쓰지 않음
python tools/make_patch.py 0.1
```

처음 실행하면 일본판 ISO를 `work/jp`에 추출합니다. 문자열 71개, 장면 폰트 58벌, 이미지 13장(텍스처 34곳과 세이브 로고, 채널 배너), `main.dol` 패치를 만든 뒤 원본 배치를 유지한 ISO를 조립하고, 결과 ISO의 파일 7,279개를 모두 원본·빌드 결과와 비교해 검증합니다.
Windows Git Bash에서는 `PYTHONIOENCODING=utf-8`을 붙이세요.

### 번역 수정

- 번역: [`translation/ko/*.json`](translation/ko)의 `ko` 값을 고친 뒤 빌드합니다. 파일 하나가 게임 문자열 파일 하나이고, `index`는 항목 번호, `speaker`는 화자입니다.
- 원문 대조: `python tools/export_text.py`를 실행하면 일본어 원문·영어·번역을 나란히 담은 `work/BW2_텍스트_전량.json`이 만들어집니다. 이 파일의 `ko`를 고친 뒤 `python tools/ko_import.py work/BW2_텍스트_전량.json`으로 되돌려 넣을 수 있습니다.
- 미리보기: `python tools/preview_text.py 출력.png 폰트:문자열파일:항목번호`로 빌드한 폰트와 문자열을 그려 볼 수 있습니다.
- 표기·말투 원칙은 [`translation/GLOSSARY.md`](translation/GLOSSARY.md)를 참고하세요.
- 그림 글씨: [`tools/assets/`](tools/assets)의 PNG를 원본과 같은 크기로 고친 뒤 빌드합니다.

`translation/ko/*.json`에는 **번역문만** 들어 있습니다(항목 번호, 화자, 한국어).
일본어·영어 원문은 게임 데이터라 넣지 않았습니다. 이 게임은 일본어를 글자 그림 번호로 저장하므로, 원문은 [`tools/data/labels.json`](tools/data/labels.json)의 판독표로 폰트를 읽어 복원합니다.

### 폴더 구조

```
tools/             빌드·원문 내보내기 도구 (paths.py가 기준 경로를 잡음)
patcher/           사용자용 패처 스크립트(패치하기.bat, patch.ps1)
  data/            일본어 판독표(폰트 칸 → 글자)
  assets/          한글화 이미지 13장
  bin/             (git 제외) wit, xdelta3
translation/
  ko/              번역 JSON (항목 번호, 화자, 한국어)
  GLOSSARY.md      인물·용어·표기 원칙
docs/
  TECHNICAL.md     파일 포맷과 한글화 방식
  releases/        릴리즈 노트 사본
release/           사용자 설명서(패처 zip은 릴리즈에만 첨부)
work/              (git 제외) 추출본·빌드 결과·원문
```

### 기술 문서

파일 포맷, 게임의 글자 그리기 방식, 원본 배치 유지 ISO 조립은 [`docs/TECHNICAL.md`](docs/TECHNICAL.md)에 정리했습니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- 패처에 동봉하는 [wit](https://wit.wiimm.de/)은 GPL-2.0, [xdelta3](https://github.com/jmacd/xdelta)는 Apache-2.0입니다.
- `tools/inplace.py`, `tools/wiidisc.py`는 같은 제작자의 「죄와 벌 우주의 후계자」 한글 패치 도구를 바탕으로 했습니다.

## 면책

비공식 팬 번역이며 Nintendo와 관련이 없습니다. 「돌격!! 패미컴 워즈 VS」 관련 상표·저작권은 Nintendo와 Kuju Entertainment에 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
