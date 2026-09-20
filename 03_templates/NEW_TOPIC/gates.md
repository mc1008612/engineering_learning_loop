---
schema: topic_gates
topic: <TOPIC>
topic_completion_rule: ALL_MANDATORY_GATES_PASSED_AND_MASTER_CONFIRMED
---

# <TOPIC> Gates

## <GATE_ID> — <GATE_TITLE>

Status: `OPEN`
Mandatory: `YES`

### Objective
<GATE_OBJECTIVE>

### Prerequisites
- <PREREQUISITE>

### Mandatory Criteria
- C1 — <CRITERION_1>
- C2 — <CRITERION_2>
- C3 — <CRITERION_3>

### Stretch Criteria
- S1 — <OPTIONAL_STRETCH>

### Allowed Assistance
Maximum: `A1`

### Required Evidence
- 至少一条直接观察能力表现的 Evidence。
- 若要求独立性，最终验收 Evidence 的 Assistance 不得高于 Gate 上限。
- “讲过 / 看懂 / 跟着做完”不能单独支撑 PASS。

### Pass Rule
Mandatory Criteria 全部满足 + 至少一条当前 Gate 的 `PASS` Evidence + Assistance 不高于 Maximum，才可 `PASSED`。

### Criterion Progress
- C1: `NOT_VERIFIED`
- C2: `NOT_VERIFIED`
- C3: `NOT_VERIFIED`

### Evidence References
- NONE
