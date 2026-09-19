# 게임 운영 5년 → Data Analyst 포트폴리오

[English / 실행 안내](README.md)

게임 운영 5년의 경험을 바탕으로 데이터 분석 직무 전환을 준비하고 있습니다. 이 프로젝트에서는 가상의 수집형 RPG를 대상으로 유입, 보스 참여, 수익화, 장애 이후 지표를 분석했으며, 데이터는 모두 독립적으로 생성한 합성 데이터입니다.

**질문:** 유입 확대 이후 무엇을 확인해야 하는가? 보스 참여 저하는 진입 문제인가? 월정액 구독 출시 이후 상품 간 매출 구성이 어떻게 달라지는가? 장애 대응은 어떤 지표로 종료해야 하는가?

**데이터:** 2024–2025년 KR·JP·Global West의 전체 시나리오 데이터 6개 테이블과, 별도의 합성 사용자 360명에 대한 등록·접속 로그 2개 테이블입니다. 두 모집단은 서로 관련되지 않으며, 기존 D30은 합성 리텐션 지표, 신규 SQL D7/D30은 정확한 해당 날짜의 접속 리텐션입니다.

**사용 기술:** Python/pandas로 분석하고, SQLite로 집계 및 사용자 단위 쿼리를 작성했습니다. 차트는 Matplotlib/Seaborn으로 만들었으며 SQL 결과는 pandas와 대조했습니다.

| 주요 발견 | 다음에 확인할 것 |
|---|---|
| Astra 콜라보레이션 이벤트 코호트 규모 +50.07%, D30 합성 리텐션 지표 −2.44%p | 유입 확대 전 채널 구성 확인과 온보딩 실험 | <!-- claim:astra_crossover_2025_cohort_change_pct:50.07 claim:astra_crossover_2025_d30_change_pp:-2.44 -->
| Astra 콜라보레이션 이벤트 일반 난이도 참여 지수 82.17 (기준 100) | 진입 자격·노출을 계측한 뒤 안내 실험 | <!-- claim:astra_normal_participation_index:82.17 -->
| 구독 출시 구간 매출 +72.21%, 이후 14일 인접 상품의 결제자 1인당 일매출 −13.32% | 전 지역 상품 혜택 차별화 실험 | <!-- claim:subscription_revenue_change_pct:72.21 claim:adjacent_post14_change_pct:-13.32 -->
| 보상 기간 동안 복귀 이용자는 장애 이전 기준의 293.95%까지 증가했지만, 매출은 56.19% 수준에 그침 | 기술 복구·활동·매출의 종료 기준 분리 | <!-- claim:compensation_returned_index:293.95 claim:compensation_revenue_index:56.19 -->

**다음 단계:** 노출·진입 자격·결제 로그를 수집한 뒤 제안한 변경을 소규모로 시험하는 것입니다. [실험 계획](docs/decision_plan.md)에 성공 지표와 중단 기준을 정리했습니다.

## 분석과 구현

- **분석:** [질문과 지표 정의](docs/analysis_spec.md), [분석별 근거](README.md#analysis-details), [민감도와 불확실성](docs/sensitivity.md), [실험 설계](docs/decision_plan.md).
- **데이터 처리와 검증:** [데이터 모델](docs/data_model.md), [사용자 단위 SQL](sql/user_retention.sql), [독립 pandas 대조](src/user_retention.py), [시간 경계·중복·지연 테스트](tests/test_user_retention.py).
- **운영 경험:** [운영 업무와 분석 역량을 연결하는 사례 준비표](docs/operations_to_da.md).

## 사용자 단위 분석

[정의](docs/user_retention.md)와 [생성 결과표](docs/user_retention_results.md)에서 사용자별 등록일 +7/+30일의 실제 합성 접속 로그를 확인할 수 있습니다. 관측이 끝난 사용자만 각 분모에 포함하며, 관측 대상이 0명이면 비율은 결측입니다. D7 미접속자가 D30에 돌아올 수 있습니다.

## 검증 과정

상품별 구매자와 대조하는 과정에서 일부 날짜의 고유 결제자 수(PU)가 상품별 구매자 합보다 큰 것을 발견했습니다. 기존 테스트에는 이 관계를 확인하는 조건이 없었습니다. PU 보정 후 관련 지표와 해석을 수정했고, SQL↔pandas 대조와 테이블 간 정합성 검사를 추가했습니다. [검증 전후 변화](docs/validation_changes.md).

## 한계와 재현

이 프로젝트는 합성 데이터를 사용하므로 실제 서비스의 효과나 인과관계를 입증하지 않습니다. 
개인 단위 결제·VOC/CS·실험 배정 정보가 없기 때문에 상품 전환이나 보스 진입 이탈을 사용자 수준에서 확인할 수 없습니다. 
별도의 로그인 예제는 exact-day 리텐션 계산 방법을 보여주기 위한 것이며, 기존 시나리오 데이터와 연결되지 않습니다.

[설치·전체 실행 명령](README.md#reproduce) · [검증된 수치](docs/verified_claims.md)
