# Connecting Game Operations experience to analysis

The table connects operations tasks with analytical skills demonstrated in this project. It is a guide for preparing real work examples, not a record of completed workplace projects. Each example separates my own work from decisions made by other teams or managers.

| Work example | What it demonstrates | Portfolio evidence | What I personally handled |
|---|---|---|---|
| QA or server cross-check for inconsistent logs | Checking whether metrics and source data match correctly | Payer correction and validation checks [Payer-bound correction](audit_review.md), [contracts](../src/data_contracts.py) | DCompared the available logs, reported the discrepancy, and left the final remediation decision to the relevant team |
| Prioritized issues by affected users and monetization exposure | Using user impact and revenue impact to decide what should be checked first | [Decision plan](decision_plan.md) | Recommended issue priority based on impact; final priority was decided by leads |
| Grouped repeated VOC/CS contacts | Grouping repeated issues and separating contact volume from affected users | Proposed extension; current dataset has no VOC/CS records | Defined issue categories and summarized repeated contacts without inventing missing counts |
| Escalated a payment-related incident | Separating revenue, payer count, and revenue per payer when reviewing an incident | [Incident analysis](findings/analysis_05_incident.md) | Detected and escalated the issue; final response decisions were made by leads |
| Checked a deployed fix | Comparing before/after results and checking whether the issue returned | [Validation change log](validation_changes.md), tests | Checked the fix against logs and QA evidence; deployment authority belonged to development |
| Worked with planning, QA and development | Turning an operational question into measurable checks | [Exact-day metric specification](user_retention.md) | Defined the checks and deliverable I owned, while separating reviewer and decision-maker roles |

## Before using an example in an application

For two or three **real** episodes, privately record: date/context → business risk → exact action personally performed → permitted evidence → finding → recommendation → who made the decision → follow-up observation. Use redacted checklists, ticket references or an explanation of the method where company policy permits. Never publish proprietary logs or private identifiers.

Safe sentence template (fill only with verified facts):

> I compared [source A] with [source B], identified [defined discrepancy], and shared [evidence/recommendation] with [team]. [Responsible role] decided [action]. I subsequently checked [metric/window] and reported [observed result and limitation].

Avoid “I improved retention by X%” unless there is a documented intervention, credible attribution and a clear personal role. “I detected, analyzed, recommended and validated” is strong when supported. The portfolio demonstrates those analytical methods using fictional data; it cannot establish a production impact or senior DA tenure.
