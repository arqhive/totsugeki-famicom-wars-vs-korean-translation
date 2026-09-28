돌격!! 패미컴 워즈 VS 한글패치 v0.1.1 (Wii / 일본판 기준)
============================================================

■ 준비물
  - 일본판 디스크 이미지 (게임 ID RBWJ01)
  - Windows 10 이상 (따로 설치할 프로그램은 없습니다)
  - 빈 공간 약 10GB (풀어 둔 파일 약 5GB + 결과 이미지)

■ 지원 형식
  원본                                   결과
  ISO (정본 덤프, WBFS에서 변환한 ISO)   → ISO
  WBFS                                   → WBFS
  CISO, WIA, WDF                         → ISO
  RVZ   ×  Dolphin에서 ISO로 변환한 뒤 적용
  NKit  ×  NKit 도구로 원본 ISO로 복원한 뒤 적용

  덤프·변환 방법에 따라 MD5가 달라도 게임 파일만 같으면 적용됩니다.
  북미판(Battalion Wars 2)·유럽판에는 적용할 수 없습니다.

■ 적용 방법
  1) 압축을 풉니다.
  2) 원본 이미지(ISO 또는 WBFS)를 "패치하기.bat" 위에 끌어다 놓습니다.
     - 원본을 이 폴더에 넣고 "패치하기.bat"을 더블클릭해도 됩니다.
     - 이미지가 여러 개 있으면 경로를 물어봅니다. 파일을 창에 끌어다 놓고 Enter.
  3) "완료"가 나올 때까지 기다립니다(1~3분). 진행 중에는 창을 닫지 마세요.
  4) 원본과 같은 폴더에 결과 파일이 생깁니다. 원본은 바뀌지 않습니다.
       ISO 원본  → Totsugeki!! Famicom Wars VS (Korean) [RBWJ01].iso
       WBFS 원본 → Totsugeki!! Famicom Wars VS (Korean) [RBWJ01].wbfs

  ※ 결과 형식 바꾸기 (예: ISO 원본 → WBFS 결과)
     이 폴더에서 PowerShell을 열고 결과 파일 확장자를 지정합니다.
       powershell -ExecutionPolicy Bypass -File patch.ps1 "원본.iso" "결과.wbfs"

  ※ 결과 파일의 MD5는 원본에 따라 달라질 수 있습니다. 게임 내용은 같습니다.

■ 실행 방법
  - Dolphin: 결과 ISO나 WBFS를 게임 목록 폴더에 넣거나 직접 엽니다.
  - Wii·Wii U vWii (USB Loader GX): WBFS를 권합니다(FAT32 USB는 4GB 넘는 파일 불가).
      wbfs/Totsugeki!! Famicom Wars VS (Korean) [RBWJ01]/RBWJ01.wbfs
    처럼 넣습니다. ISO를 쓰려면 NTFS USB를 쓰세요.

■ 오류가 날 때
  - "일본판 … (RBWJ01)가 아닙니다": 북미판·유럽판이거나 다른 게임입니다.
  - "원본 게임 파일이 다릅니다": 이미 패치한 이미지거나 손상된 덤프입니다.
  - "RVZ는 지원하지 않습니다": Dolphin 게임 목록에서 우클릭 → 파일 변환 → ISO.
  - "wit.exe 실행 실패": 빈 공간이 모자라거나 원본 파일이 손상됐습니다.

■ 한글화 범위
  - 대사: 캠페인 미션 20개와 대전 맵의 무전 대사·목표, 스토리 영상 자막 12편
  - 메뉴: 메인 메뉴, 설정, 저장 메시지, 유닛 도감, 설정 자료, 크레딧
  - 그래픽: 타이틀 로고, 뒤로 버튼, 리모컨 스트랩 경고 화면, Wii 메뉴 채널 배너, 세이브 데이터 로고

■ 확인 환경
  - Dolphin 에뮬레이터
  - Wii U vWii (USB Loader GX)

■ 알려진 문제
  - 일부 대사가 상자 테두리를 조금 벗어납니다. 가독성을 우선했습니다.
  - 승리·패배 연출 글자(VICTORY, DEFEAT)는 원본부터 영문이라 그대로 두었습니다.
  - 이름 입력 화면의 글자판은 원본대로 가나입니다.

■ 동봉 도구
  - wit (Wiimms ISO Tools, GPL-2.0, https://wit.wiimm.de/) — bin/wit-gpl-2.0.txt
  - xdelta3 (Apache-2.0, https://github.com/jmacd/xdelta)

■ 기타
  비공식 팬 번역이며 Nintendo와 관련이 없습니다.
  패치를 적용한 게임 파일의 배포를 금지합니다.
