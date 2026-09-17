# 게임 운영 5년 → Data Analyst 포트폴리오

[English / 실행 안내](README.md) · [채용 준비 점검](docs/hiring_readiness_review.md)

**DA 70% + Analytics Engineer 30%:** 운영에서 접하는 문제를 분석 질문으로 바꾸고, 지표 정의와 데이터 정합성을 검증한 뒤 실행 가능한 실험을 제안하는 프로젝트입니다. 모든 데이터는 독립적으로 생성한 합성 데이터이며 실제 서비스 성과가 아닙니다.

**질문:** 유입 확대 이후 무엇을 확인해야 하는가? 보스 참여 저하는 진입 문제인가? 구독 출시 이후 상품 간 매출 구성이 어떻게 달라지는가? 장애 대응은 어떤 지표로 종료해야 하는가?

**데이터:** 2024–2025년 KR·JP·Global West 집계 시나리오 6개 테이블과, 별도의 합성 사용자 360명에 대한 등록·접속 로그 2개 테이블입니다. 두 모집단은 연결되지 않습니다. 기존 D30은 **중첩 체크포인트 대리지표**, 신규 SQL D7/D30은 **정확한 해당 날짜의 접속 리텐션**입니다.

| 합성 데이터에서 확인한 사실 | 제안하는 판단 / 검증 |
|---|---|
| Astra 코호트 규모 +50.07%, D30 대리지표 −2.44%p | 유입 확대 전 채널 구성 확인과 온보딩 실험 | <!-- claim:astra_crossover_2025_cohort_change_pct:50.07 claim:astra_crossover_2025_d30_change_pp:-2.44 -->
| Astra 일반 난이도 참여 지수 82.17 (기준 100) | 진입 자격·노출을 계측한 뒤 안내 실험; 난이도가 원인에서 배제된 것은 아님 | <!-- claim:astra_normal_participation_index:82.17 -->
| 구독 출시 구간 매출 +72.21%, 이후 14일 인접 상품의 payer-day당 매출 −13.32% | 전 지역 상품 혜택 차별화 실험; 개인 구매 전환은 확인 불가 | <!-- claim:subscription_revenue_change_pct:72.21 claim:adjacent_post14_change_pct:-13.32 -->
| 보상 구간 복귀자 지수 293.95, 매출 지수 56.19 | 기술 복구·활동·매출의 종료 기준 분리 | <!-- claim:compensation_returned_index:293.95 claim:compensation_revenue_index:56.19 -->

**검증:** 기존 테스트가 놓친 불가능한 PU를 상품별 구매자와 교차 확인해 보정했습니다. SQL↔pandas 대조, 비즈니스 불변조건, 생성 문서 점검, 재현 파이프라인을 갖췄습니다. [검증 전후 변화](docs/validation_changes.md).

**실행 제안:** 각 주요 발견에 대상·가설·실험·성공 KPI·가드레일·계속/중단/반복 기준을 명시했습니다. 실험을 실제 수행했다거나 효과를 입증했다고 주장하지 않습니다. [의사결정 계획](docs/decision_plan.md).

## 채용 관점에서 볼 증거

- **DA:** [질문과 지표 정의](docs/analysis_spec.md), [분석별 근거](README.md#analysis-details), [민감도와 불확실성](docs/sensitivity.md), [실험 설계](docs/decision_plan.md).
- **AE:** [데이터 모델](docs/data_model.md), [사용자 단위 SQL](sql/user_retention.sql), [독립 pandas 대조](src/user_retention.py), [시간 경계·중복·지연 테스트](tests/test_user_retention.py).
- **운영 경험 연결:** [개인 기여와 의사결정자 구분, 실제 증빙 준비표](docs/operations_to_da.md). 운영 5년을 DA 5년으로 표현하지 않으며, 구체적 업무 사례는 본인의 사실 확인이 필요합니다.

## 사용자 단위 분석

[정의](docs/user_retention.md)와 [생성 결과표](docs/user_retention_results.md)에서 사용자별 등록일 +7/+30일의 실제 합성 접속 로그를 확인할 수 있습니다. 관측이 끝난 사용자만 각 분모에 포함하며, 관측 대상이 0명이면 비율은 결측입니다. D7 미접속자가 D30에 돌아올 수 있습니다. 3월 D30은 일부만 성숙했으므로 지역 순위나 월 전체 리텐션으로 해석할 수 없습니다.

## 한계와 재현

기존 분석의 ‘회복’은 선언한 기준선 대비 지표 변화입니다. 동일 이용자의 신뢰 회복이나 인과효과를 측정하지 않았습니다. 실제 결제 로그·VOC/CS·실험 배정 정보는 없습니다. 새로운 사용자 예제도 기존 시나리오의 개인 행동을 입증하지 않습니다.

[설치·전체 실행 명령](README.md#reproduce) · [검증된 수치](docs/verified_claims.md) · [면접 질문과 남은 과제](docs/hiring_readiness_review.md)
