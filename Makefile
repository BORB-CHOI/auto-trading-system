.PHONY: help install install-uv lint fmt typecheck test test-all check hooks clean

help:  ## 사용 가능한 명령 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## 개발 의존성 설치 (pip)
	python -m pip install -e ".[dev,oracle]"

install-uv:  ## 개발 의존성 설치 (uv, 권장)
	uv pip install -e ".[dev,oracle]"

lint:  ## ruff 린트
	ruff check src tests

fmt:  ## ruff 포맷 적용
	ruff format src tests
	ruff check --fix src tests

typecheck:  ## mypy 타입 검사
	mypy

test:  ## 빠른 테스트 (slow 제외)
	pytest -m "not slow"

test-all:  ## 전체 테스트 (slow 포함, 네트워크/데이터 필요)
	pytest

check: lint typecheck test  ## 커밋 전 전체 점검

hooks:  ## pre-commit 훅 설치
	pre-commit install

clean:  ## 캐시/빌드 산출물 정리
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
