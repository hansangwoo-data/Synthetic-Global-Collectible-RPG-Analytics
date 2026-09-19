# Connecting Game Operations experience to analysis

The table connects operations tasks with analytical skills demonstrated in this project. It is a guide for preparing real work examples, not a record of completed workplace projects. Each example separates my own work from decisions made by other teams or managers.

| Operations example to substantiate | DA capability | Verifiable portfolio artifact | Personal contribution / stakeholder boundary to confirm |
|---|---|---|---|
| QA or server cross-check found inconsistent logs | Question metric semantics; reconcile independent sources | [Payer-bound correction](audit_review.md), [contracts](../src/data_contracts.py) | Describe the comparison you ran and discrepancy you reported; distinguish who decided remediation |
| Prioritized issues by affected users and monetization exposure | Define denominator and decision criteria | [Decision plan](decision_plan.md) | Document your triage recommendation; do not claim final priority ownership unless true |
| Grouped repeated VOC/CS contacts | Normalize frequency by exposed users; avoid confusing contacts with unique users | Proposed extension only: current data has no VOC/CS records | Provide a permitted, redacted category definition and your aggregation; do not invent contact counts |
| Escalated a payment-related incident | Separate revenue, payer count and revenue per payer | [Incident analysis](findings/analysis_05_incident.md) | Explain detection/escalation you performed versus decisions made by leads |
| Checked a deployed fix | Define pre/post observation windows and regression guardrails | [Validation change log](validation_changes.md), tests | Identify your validation checklist, QA evidence and remaining uncertainty; deployment authority may belong to development |
| Worked with planning, QA and development | Translate a question into instrumentation and acceptance criteria | [Exact-day metric specification](user_retention.md) | Name the deliverable you authored, reviewers and decisions they owned |

## Before using an example in an application

For two or three **real** episodes, privately record: date/context → business risk → exact action personally performed → permitted evidence → finding → recommendation → who made the decision → follow-up observation. Use redacted checklists, ticket references or an explanation of the method where company policy permits. Never publish proprietary logs or private identifiers.

Safe sentence template (fill only with verified facts):

> I compared [source A] with [source B], identified [defined discrepancy], and shared [evidence/recommendation] with [team]. [Responsible role] decided [action]. I subsequently checked [metric/window] and reported [observed result and limitation].

Avoid “I improved retention by X%” unless there is a documented intervention, credible attribution and a clear personal role. “I detected, analyzed, recommended and validated” is strong when supported. The portfolio demonstrates those analytical methods using fictional data; it cannot establish a production impact or senior DA tenure.
