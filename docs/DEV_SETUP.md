# 개발 환경 셋업

## 요구사항

- **Python 3.12+** (pyproject `requires-python`)
- **uv** 권장 (빠른 패키지 매니저) 또는 pip
- git

## uv 설치 (권장)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
```

## 프로젝트 설치

```bash
# uv
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,oracle]"

# 또는 pip
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,oracle]"
```

## pre-commit 훅

```bash
make hooks     # pre-commit install
```

## 자주 쓰는 명령 (`make help`)

| 명령 | 하는 일 |
|------|---------|
| `make fmt` | ruff 포맷 + 자동수정 |
| `make lint` | ruff 린트 |
| `make typecheck` | mypy |
| `make test` | 빠른 테스트 (slow 제외) |
| `make test-all` | 전체 (네트워크/데이터 필요) |
| `make check` | lint + typecheck + test (커밋 전) |

## 데이터 준비 (marcap)

가격/시총 데이터는 커밋하지 않는다 (`.gitignore`의 `*.parquet`, `data/`). 로컬에 clone:

```bash
# 리포 밖 또는 data/ 아래(무시됨)에 clone. 약 3.4GB.
git clone https://github.com/FinanceData/marcap.git data/marcap
```

수급(외인/기관/개인)은 아직 미정 (ADR-0002). KIS API 도입 시 별도 안내.

## 비밀정보

- API 키·토큰은 **절대 커밋하지 않는다.** `.env`, `*.key`, `kis_token.json` 등은 `.gitignore`+
  `.claude/settings.json` deny로 이중 차단.
- KIS 인증정보는 `.env`(로컬)로 주입. 예시는 `.env.example`(도입 시 추가) 참조.

## MCP (선택, 개발 보조용)

- **실행 경로엔 넣지 않는다** (CLAUDE.md). API 검색·이슈 관리 등 개발 보조로만.
- **Linear** (이슈 관리): 대화형 세션에서 `/mcp` → linear 인증. 엔드포인트는
  `https://mcp.linear.app/mcp` (HTTP). `/sse`는 폐기됨(404).
- **KIS Code Assistant** (API 검색 보조): `uv` + Python 3.12 필요.
  ```bash
  claude mcp add kis-code-assistant -- npx -y @koreainvestment/kis-code-assistant-mcp
  ```
- MCP 인증(OAuth)은 브라우저 상호작용이 필요해 **대화형 세션에서 사용자가 직접** 해야 한다.
