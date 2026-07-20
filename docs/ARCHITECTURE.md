# 아키텍처

방법론·전략의 "무엇을/왜"는 `PROJECT_GUIDELINES.md`에 있다. 이 문서는 **코드가 어떻게 배치되는가**를 다룬다.

## 레이어 구조 (§3.1)

```
src/
├── layer1_data/        데이터 수집·정제·point-in-time 저장
│                        (marcap 로더, 종목 마스터, 향후 수급/뉴스)
├── layer2_signals/     신호 생성 — LLM이 들어가는 유일한 자리 (Phase 2~)
│                        (지금은 비어 있음. Phase 1은 정량 신호만)
├── layer3_strategy/    포트폴리오/매매 전략 — 결정론적 룰
│                        (universe filter, 랭킹, conviction, 청산, 회피 패턴)
└── layer4_execution/   백테스트 엔진 + (향후) 실행
                         (자체 엔진 "얇게", 지표, 거래비용, 3분할)
```

**의존 방향은 한 방향:** `layer4 → layer3 → layer2 → layer1`. 상위 레이어가 하위를 부른다.
하위가 상위를 참조하지 않는다. LLM은 layer2에서 멈춘다 — layer3(매매 결정)은 항상 결정론적 코드.

## 백테스트 데이터 흐름 (Phase 1, 정량만)

```
marcap (parquet)
  │  layer1: 로드(코드 6자리 정규화) + 상폐 종목 보존
  ▼
일별 전종목 패널 (date × symbol × [OHLCV, Amount, Marcap, Stocks, Dept])
  │  layer1: 거래 대상 아닌 종목 빼기 — exclusions.py (ADR-0003)
  │          스팩·KONEX·우선주·리츠·관리종목. 전략 무관하게 항상 참.
  ▼
거래 가능 종목 패널
  │  layer3: 전략 조건으로 추리기 — screening.py (§4.2)
  │          거래대금·시총·등락률. 튜닝 대상 = 전략 그 자체.
  │          → 신호 계산 (§4.3 Tier 1)
  ▼
일별 후보 + 신호 점수
  │  layer4: 진입(종가, ADR-0001) → 포지션 관리 → 청산 → 거래비용
  ▼
거래 원장 (trades)
  │  layer4: 3분할(§4.1) 위에서 지표 산출
  ▼
WRL / IC / Expectancy / Skewness / 분위수익률 (§6.1)
```

## 설계 원칙 (코드 레벨)

- **자체 엔진은 얇게.** 범용 백테스트 프레임워크를 만들지 않는다. 매일 필터→랭킹→포트폴리오
  실행 하네스만. 저수준 P&L 회계는 pandas/numpy. (CLAUDE.md)
- **oracle 대조.** backtesting.py로 단순 전략 하나를 같은 데이터에 돌려 P&L을 대조 →
  자체 엔진의 회계 버그를 값싸게 잡는다. oracle은 메인 엔진이 아니다.
- **look-ahead 불변식.** 모든 피처는 "as-of 시점" 이후 데이터를 보지 않는다.
  이걸 코드 계약으로 만들고 테스트로 강제한다 (ADR-0001).
- **임계값은 주입.** 시총 하한·z-score 창·손절 라인 등은 하드코딩하지 않고 설정으로 주입.
  전부 placeholder (§0.1).
- **결정론적 재현.** 같은 입력 → 같은 출력. LLM 도입 시엔 사전 크롤링 archive로 재현성 확보.

## 아직 없는 것 (의도적)

레이어 폴더는 `.gitkeep`만 있고 대부분 비어 있다. walking skeleton(정량 신호 1개 end-to-end)이
먼저 각 레이어를 얇게 관통한 뒤 살을 붙인다. 전체 레이어 동시 구현 ❌ (§3.13).
