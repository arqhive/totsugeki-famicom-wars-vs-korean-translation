"""저장소 안팎 경로와 외부 도구 위치(어느 폴더에서 실행해도 같게 동작)."""
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
DATA = TOOLS / 'data'                 # 일본어 판독표(폰트 칸 → 글자)
ASSETS = TOOLS / 'assets'             # 한글화 이미지
TRANS = ROOT / 'translation'
KO = TRANS / 'ko'                     # 번역 JSON
RELEASE = ROOT / 'release'
DOCS = ROOT / 'docs'
WORK = ROOT / 'work'                  # 추출본·빌드 결과·원문 등 커밋하지 않는 작업 폴더
JP = WORK / 'jp'                      # 일본판 ISO 추출본(DATA 파티션)
JP_FILES = JP / 'DATA' / 'files'
JP_DATA = JP_FILES / 'Data'
JP_SYS = JP / 'DATA' / 'sys'
BUILD = WORK / 'build'                # 바뀐 파일만 모아 두는 곳(files/…, sys/main.dol)
ISO_NAME = 'Totsugeki!! Famicom Wars VS (Japan) [RBWJ01].iso'


def _find(env, name):
    p = os.environ.get(env)
    if p:
        return Path(p)
    for d in (ROOT, ROOT / 'iso', ROOT.parent):
        if (d / name).exists():
            return d / name
    return None


def jp_iso():
    p = _find('BW2_JP_ISO', ISO_NAME)
    if not p:
        raise SystemExit(f'일본판 ISO를 찾을 수 없습니다. 저장소 루트에 "{ISO_NAME}"를 두거나 환경 변수 BW2_JP_ISO로 지정하세요.')
    return p


def tool(env, exe, local):
    """외부 도구: 환경 변수 → tools/bin → PATH."""
    for p in (os.environ.get(env), TOOLS / 'bin' / Path(*local) if local else None):
        if p and Path(p).is_file():
            return str(p)
    p = shutil.which(exe)
    if p:
        return p
    raise SystemExit(f'{exe}를 찾을 수 없습니다. tools/bin 이나 PATH에 두거나 환경 변수 {env}로 지정하세요.')


def wit():
    return tool('WIT', 'wit', ('wit-v3.05a-r8638-cygwin64', 'bin', 'wit.exe'))


def xdelta3():
    return tool('XDELTA3', 'xdelta3', ('xdelta3.exe',))


def dolphin_tool():
    for p in (os.environ.get('DOLPHIN_TOOL'), Path.home() / 'Desktop' / 'Dolphin-x64' / 'DolphinTool.exe'):
        if p and Path(p).is_file():
            return str(p)
    return tool('DOLPHIN_TOOL', 'DolphinTool', None)


def rel(p):
    """cygwin wit·xdelta 헤더에 절대경로(한글·사용자 폴더명)가 남지 않게 ROOT 기준 상대경로로"""
    return os.path.relpath(str(p), str(ROOT))


def ensure_jp():
    """work/jp 가 없으면 일본판 ISO 의 DATA 파티션을 추출한다(DolphinTool, work/jp/DATA/{sys,files})."""
    if not (JP_DATA / 'Strings').exists():
        print('일본판 ISO 추출 중… (work/jp)')
        subprocess.run([dolphin_tool(), 'extract', '-i', str(jp_iso()), '-o', str(JP), '-g', '-q'], check=True)
    return JP_DATA
