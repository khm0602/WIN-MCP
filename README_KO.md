# windows-mcp-ko

[Windows-MCP](https://github.com/CursorTouch/Windows-MCP) 0.8.9 한국어 포크 (MIT).
Claude Code가 내 PC 화면을 보고 마우스·키보드로 직접 조작하게 해 주는 MCP 서버.

## 원본과 다른 점
- 화면 테두리 안내문·확인창 한글화 (맑은 고딕)
- 사람 같은 입력: 곡선 마우스 이동, 클릭 위치·누름 시간 흩뜨리기, 리듬 있는 타이핑·스크롤
- 시작 확인창 기본 꺼짐 (`consent_countdown_seconds = 0`)

## 설치 (윈도우, PowerShell)
```powershell
# 1) uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# 2) 설치 (원본을 깔았다면 먼저: uv tool uninstall windows-mcp)
uv tool install git+https://github.com/khm0602/windows-mcp-ko
# 3) Claude Code 등록 (끝의 serve 필수)
claude mcp add WIN-MCP -s user -e ANONYMIZED_TELEMETRY=false -- "$env:USERPROFILE\.local\bin\windows-mcp-ko.exe" serve
```
Claude Code를 다시 켜고 `/mcp`에서 `WIN-MCP`가 connected인지 확인.

업데이트: `uv tool upgrade windows-mcp-ko`

## 끄고 싶을 때 (환경변수)
- `WINDOWS_MCP_HUMAN_MOUSE=0` — 사람 같은 입력 끄기 (원본처럼 빠르게)
- `WINDOWS_MCP_DISABLE_FLASH=1` — 스크린샷마다 번쩍이는 테두리 끄기

## 주의
- 그 PC 앞에서 켠 Claude Code만 그 화면을 제어한다 (SSH로 켜면 멈춤).
- 사람이 마우스를 움직이면 AI가 10초 양보한다.
- 결제·발행·전송 버튼은 "누르기 전에 물어봐"라고 같이 말해 두기.
