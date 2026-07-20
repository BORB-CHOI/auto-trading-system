# Architecture Decision Records (ADR)

되돌리기 어렵거나 방법론에 영향을 주는 결정을 한 건씩 기록한다.
"왜 이렇게 정했는가"를 나중에 추적하기 위한 것. `docs/PROJECT_GUIDELINES.md`(방법론)와
`docs/CHANGELOG.md`(지침서 버전 이력)와는 별개 — ADR은 **구현 결정**을 다룬다.

## 작성 규칙

- 새 결정은 `NNNN-제목.md` (4자리 일련번호). `0000-template.md` 복사해서 시작.
- 상태: `제안(proposed)` → `수락(accepted)` → (뒤집히면) `대체됨(superseded by ADR-XXXX)`.
- 결정을 **뒤집을 때 기존 ADR을 지우지 않는다.** 상태만 `대체됨`으로 바꾸고 새 ADR을 쓴다.
- 정량 임계값은 placeholder로 명시 (지침서 §0.1). 확정 사양으로 못 박지 않는다.

## 목록

| ADR | 제목 | 상태 |
|-----|------|------|
| [0001](0001-close-entry-lookahead.md) | 종가 진입의 look-ahead 처리 | 제안 (오너 입력 대기) |
| [0002](0002-data-source.md) | 데이터 소스 (가격/시총 = marcap, 수급 = 미정) | 부분 수락 / 수급 미정 |
| [0003](0003-universe-exclusions.md) | 유니버스 제외 종목 (KONEX·스팩·우선주·리츠) | 수락 |
