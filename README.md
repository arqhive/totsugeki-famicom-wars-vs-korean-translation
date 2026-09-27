# 돌격!! 패미컴 워즈 VS (Wii) 한글 패치

*Totsugeki!! Famicom Wars VS* (Wii, 일본판 `RBWJ01`) 비공식 한국어 팬 패치입니다.
대사는 일본어판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v0.1](../../releases/tag/v0.1)**

- 대사 전체를 한글화했습니다(캠페인 미션 20개와 대전 맵의 무전 대사·목표, 스토리 영상 자막 12편).
- 메뉴 전체를 한글화했습니다(메인 메뉴, 설정, 저장 메시지, 유닛 도감, 설정 자료, 크레딧).
- 타이틀 로고, 뒤로 버튼, 리모컨 스트랩 경고 화면, Wii 메뉴 채널 배너, 세이브 데이터 로고를 한글화했습니다.
- 장면마다 쓰인 한글만 모아 게임 폰트를 새로 만들었습니다. 1편 한글 패치와 같은 흰 글씨·검은 테두리·그림자 모양입니다.
- **원본 디스크의 파일 배치를 그대로 유지해 패치 크기를 줄였습니다.**

> 이 저장소에는 **게임 데이터(롬·디스크 이미지, 추출한 원문 대사, 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 ISO. 북미판(Battalion Wars 2)·유럽판에는 적용할 수 없습니다. RVZ·WBFS 등으로 갖고 있다면 Dolphin으로 ISO로 바꾼 뒤 적용하세요.
- xdelta 패치 도구. [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher)(GUI)나 [xdelta3](https://github.com/jmacd/xdelta-gpl/releases)(명령줄)를 쓰면 됩니다.

### 적용 방법

1. [배포 페이지](../../releases/latest)에서 `TotsugekiFamicomWarsVS_KO_v0.1.xdelta`를 받습니다.
2. 일본판 원본 ISO에 패치를 적용합니다. xdelta3에서는 다음처럼 실행합니다.

   ```
   xdelta3 -d -s "Totsugeki!! Famicom Wars VS (Japan).iso" TotsugekiFamicomWarsVS_KO_v0.1.xdelta "Totsugeki!! Famicom Wars VS (Korean).iso"
   ```

3. 결과 파일의 확인값을 아래 표와 비교합니다.

자세한 방법은 [`README_한국어.txt`](release/README_한국어.txt)를 참고하세요.

### 파일 확인값

| 항목 | 원본 일본판 | 패치 적용 결과 (v0.1) |
|---|---|---|
| 크기 | 4,699,979,776 바이트 | 4,699,979,776 바이트 |
| CRC32 | `4C124B4F` | `8CB91FE6` |
| MD5 | `67dc3eb745ce470f3a452caa6679b161` | `c08176901c677d3000d8963d967c5521` |
| SHA-1 | `97a8f24213d08ac9fd8546bd31f3ce7f1020b77d` | `693384046f15084f901f22f9c25abacc3d0e70c7` |
| SHA-256 | `ffcb88c7bf39e126a89557f6660132e3c506c3b136cf37f8bc6eeba8beee3962` | `7ec6fb745a392ff2ba81550ff6c5bb7b112a1b2eab503e6ac1aea16da1a07e81` |

원본 파일명 예: `Totsugeki!! Famicom Wars VS (Japan).iso`

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
- xdelta3. 배포용 패치를 만들 때만 필요하며, `tools/bin/xdelta3.exe`나 PATH, 환경 변수 `XDELTA3`로 둡니다.

### 빌드

```bash
# 한글 ISO 만들기 (work/TotsugekiFamicomWarsVS_KO.iso)
python tools/build.py

# 배포용 패치까지: 빌드, xdelta 패치 생성, 적용 결과 해시 검증
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
  data/            일본어 판독표(폰트 칸 → 글자)
  assets/          한글화 이미지 13장
  bin/             (git 제외) wit, xdelta3
translation/
  ko/              번역 JSON (항목 번호, 화자, 한국어)
  GLOSSARY.md      인물·용어·표기 원칙
docs/
  TECHNICAL.md     파일 포맷과 한글화 방식
  releases/        릴리즈 노트 사본
release/           사용자 설명서(xdelta 패치는 크기 때문에 릴리즈에만 첨부)
work/              (git 제외) 추출본·빌드 결과·원문
```

### 기술 문서

파일 포맷, 게임의 글자 그리기 방식, 원본 배치 유지 ISO 조립은 [`docs/TECHNICAL.md`](docs/TECHNICAL.md)에 정리했습니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- `tools/inplace.py`, `tools/wiidisc.py`는 같은 제작자의 「죄와 벌 우주의 후계자」 한글 패치 도구를 바탕으로 했습니다.

## 면책

비공식 팬 번역이며 Nintendo와 관련이 없습니다. 「돌격!! 패미컴 워즈 VS」 관련 상표·저작권은 Nintendo와 Kuju Entertainment에 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
