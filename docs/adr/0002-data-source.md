# ADR-0002: 데이터 소스

- **상태:** 부분 수락 (가격/시총 = 수락, 수급 = 미정)
- **날짜:** 2026-07-10
- **관련:** PROJECT_GUIDELINES §5(데이터 소스), §4.2(universe filter), §4.3(Tier 1 feature), CLAUDE.md

## 맥락 (Context)

백테스트(빌드 단계 1~2)에 필요한 데이터는 **최소** 범위로 확정(v3.8):
일별 OHLCV + 거래대금 + 시총/상장주식수 + point-in-time 종목 마스터(상폐 포함) + 수급(외인/기관/개인).

핵심 제약(CLAUDE.md, 타협 불가):
- **Survivorship bias 제거** — 상장폐지 종목이 자기 시절 데이터에 남아 있어야 함.
- **Point-in-time universe** — 각 시점에 실제 상장·거래되던 종목만.
- 2017-01 ~ 현재 (초기 백테스트 구간).

조사 과정에서 확인한 사실:
- **pykrx(웹 스크래핑)는 깨졌다** — KRX가 로그인 게이트를 걸어 구 스크래핑 경로가 `LOGOUT` 반환.
  신규 의존 대상에서 제외.
- **KRX 공식 OPEN API**(openapi.krx.co.kr)는 일별매매정보·종목기본정보는 있으나
  **종목별 투자자 수급이 없다.**
- **수급은 직접 계산 불가** — 외인/기관/개인 구분은 거래소가 계좌 주체별로 집계한 정보라
  OHLCV에서 역산할 수 없다.

## 검토한 선택지 (Options)

### 가격 / 시총 / 상폐

**A. FinanceData/marcap (채택)**
- GitHub 공개 데이터셋, 1995~현재, 일별, parquet, 1천만+ 행, 매일 갱신.
- 컬럼: Open/High/Low/Close/Volume/**Amount(거래대금)**/**Marcap(시총)**/**Stocks(상장주식수)**/Rank/Market/Name/Changes/Code.
- **날짜별 전종목 스냅샷** 구조 → 상폐 종목이 자기 시절에 그대로 존재 = survivorship + point-in-time 자동 해결.
- 조달 = `git clone` 1회(약 3.4GB). API 콜 폭발 없음.
- 리스크: 서드파티 데이터셋(정합성은 우리가 검증), 용량.

**B. KRX 공식 OPEN API** — 인증키+서비스 신청, 키당 10,000콜/일, 2010~. 가격/종목정보엔 쓸 수 있으나
marcap 대비 이점 적고 백필 콜 부담. **보조/교차검증용으로만 보류.**

### 수급 (외인 / 기관 / 개인)

**C. KIS API `investor-trade-by-stock-daily` (유력)**
- `/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily`, 종목별 일별 투자자매매동향.
- 공식 레포 예제 확인됨. KIS는 무료 모의투자·주문까지 한 곳 → 주문 창구도 KIS로 확정(별도).
- **문제:** 종목 하나씩 호출 → 전종목 백필 시 콜 폭발.
  → marcap으로 유니버스를 먼저 좁힌 뒤 **후보 종목에만** 수급 콜. 과거 이력 제공 한도 미확인.

**D. 준비된 수급 데이터셋** — marcap 같은 clone형 수급 데이터셋은 아직 못 찾음. 계속 조사.

**E. 토스증권** — `investor-trading`이 시장 전체(KOSPI/KOSDAQ) 집계만. 종목별 없음 → **부적합.**

## 결정 (Decision)

- **가격/시총/거래대금/상폐/종목마스터 = FinanceData/marcap 채택.** 백테스트 데이터의 기반.
- **수급 = 미정.** 유력 후보는 KIS `investor-trade-by-stock-daily`(유니버스 축소 후 백필).
  clone형 준비 데이터셋 존재 여부 추가 조사.
- 초기 백테스트 골격은 **수급 없이 marcap만으로 착수**하고, 수급은 두 번째 신호로 붙인다
  (§3.13 modular: baseline → 단독 layer 순서와 일치).

## 결과 (Consequences)

- marcap을 clone → 로드/무결성 검증(상폐 종목 존재, 거래대금·시총 정합성) 후 DATA_SCHEMA.md 확정.
- 수급 콜 예산은 유니버스 크기에 종속 → universe filter 확정 후 재산정.
- KIS 수급 과거 이력 한도가 백테스트 구간(2017~)에 못 미치면 대체 소스 재탐색.

## 미해결 (Open questions)

1. KIS `investor-trade-by-stock-daily`가 과거 몇 년치까지 주는가?
2. 키움 REST API에 종목별 수급이 있는가? (미조사)
3. clone형 수급 데이터셋 존재 여부.
