---
schema: topic_gates
topic: STA_XDC
topic_completion_rule: ALL_MANDATORY_GATES_PASSED_AND_MASTER_CONFIRMED
---

# STA/XDC Gates

## STA_XDC-GATE-G1 — 同步时序模型与 Timing Report 阅读

Status: `PASSED`
Mandatory: `YES`

### Objective
建立同步时序分析的基本心智模型，并能独立阅读基础 Timing Report。

### Prerequisites
- 能阅读基本同步 RTL，理解寄存器、组合逻辑和时钟边沿。

### Mandatory Criteria
- C1 — 能独立识别 launch/capture、startpoint/endpoint，并区分 register-to-register、input-to-register、register-to-output 等常见路径类型。
- C2 — 能解释 setup、hold、arrival time、required time 与 slack 的含义和关系，并据此判断违例性质。
- C3 — 能从一份基础 Timing Report 中定位关键约束、关键路径和潜在问题，给出有依据的初步诊断。

### Stretch Criteria
- S1 — 能比较同一路径在不同约束或实现条件下的报告变化。

### Allowed Assistance
Maximum: `A1`

### Required Evidence
- 至少一条直接观察能力表现的 Evidence。
- 若要求独立性，最终验收 Evidence 的 Assistance 不得高于 Gate 上限。
- “讲过 / 看懂 / 跟着做完”不能单独支撑 PASS。

### Pass Rule
Mandatory Criteria 全部满足 + 至少一条当前 Gate 的 `PASS` Evidence + Assistance 不高于 Maximum，才可 `PASSED`。

### Criterion Progress

- C1: `VERIFIED`
- C2: `VERIFIED`
- C3: `VERIFIED`

### Evidence References

- STA_XDC-EXP-001
- STA_XDC-EXP-002

## STA_XDC-GATE-G2 — Clock 与 I/O Constraints

Status: `DRAFT`
Mandatory: `YES`

### Objective
能够基于明确的接口时序假设编写和审查基本 Clock 与 I/O Constraints。

### Prerequisites
- STA_XDC-GATE-G1 `PASSED`

### Mandatory Criteria
- C1 — 能依据时钟规格正确建立基础时钟约束，并解释关键参数。
- C2 — 能把外部器件或接口时序关系转换为 input/output delay 约束。
- C3 — 能检查未约束路径和约束覆盖情况，识别明显遗漏或错误假设。

### Stretch Criteria
- S1 — 能说明生成时钟约束的适用场景和基本建模原则。

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

## STA_XDC-GATE-G3 — Exceptions 与 Timing Closure

Status: `DRAFT`
Mandatory: `YES`

### Objective
能够谨慎使用时序例外，并针对常见时序违例形成可验证的 closure 策略。

### Prerequisites
- STA_XDC-GATE-G2 `PASSED`

### Mandatory Criteria
- C1 — 能区分 false path、multicycle path 等常见例外的语义、风险和适用条件。
- C2 — 能从报告和设计结构出发定位常见 setup/hold 问题的主要来源。
- C3 — 能提出、实施或评审有针对性的 timing closure 措施，并用报告验证结果而非掩盖违例。

### Stretch Criteria
- S1 — 能对一个带有错误或过宽例外的约束集进行审查并说明风险。

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
