---
schema: topic_gates
topic: CLOCK_RESET
topic_completion_rule: ALL_MANDATORY_GATES_PASSED_AND_MASTER_CONFIRMED
---

# CLOCK_RESET Gates

## CLOCK_RESET-GATE-G1 — 时钟生成与 Generated Clock 约束

Status: `OPEN`
Mandatory: `YES`

### Objective
理解 7 系列时钟资源与 MMCM/PLL 结构，能在真实工程中实例化时钟原语并正确约束生成时钟。

### Prerequisites
- STA_XDC 核心能力（Timing Report 阅读、基础约束、closure 判断）已建立（STA_XDC-EXP-001~004）。

### Mandatory Criteria
- C1 — 能解释 MMCM/PLL 的关键参数与输出时钟关系（频率/相位/占空比/jitter），并说明时钟资源层级（BUFG/BUFR/MMCM/PLL）的角色与适用。
- C2 — 能在真实 Vivado 工程中为 MMCM/PLL 输出创建 generated clock（create_generated_clock）并解释其与 source clock 的关系，包括自动推导与手动约束的差异。
- C3 — 能在 timing report 与 clock utilization 中追踪 clock path（insertion delay、skew、clock network 类型），识别 clock 相关的路径差异。

### Stretch Criteria
- S1 — 能对比 Clock Wizard 自动约束与手写 XDC 的差异并说明各自风险。

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

## CLOCK_RESET-GATE-G2 — Reset Architecture

Status: `DRAFT`
Mandatory: `YES`

### Objective
能为真实设计选择并实现正确的复位架构，并对其做约束与时序审查。

### Prerequisites
- CLOCK_RESET-GATE-G1 `PASSED`

### Mandatory Criteria
- C1 — 能区分同步/异步复位的优缺点与适用条件，解释 async assert / sync deassert 的语义。
- C2 — 能设计并实现 reset synchronizer（异步断言、同步释放），并处理 reset 树的 fanout 与分发。
- C3 — 能对复位结构做约束与时序审查（reset 路径按 data path 还是例外处理），并识别常见错误。

### Stretch Criteria
- S1 — 能审查一个存在复位架构缺陷的真实设计并提出可验证的修正。

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

## CLOCK_RESET-GATE-G3 — 多时钟系统与时钟域边界

Status: `DRAFT`
Mandatory: `YES`

### Objective
能在多时钟系统中审查时钟域边界，识别跨时钟路径并制定正确的约束策略（综合 signoff 场景）。

### Prerequisites
- CLOCK_RESET-GATE-G2 `PASSED`

### Mandatory Criteria
- C1 — 能解读 clock interaction / inter-clock 报告，识别设计中真实的时钟域边界。
- C2 — 能识别跨时钟路径并制定正确约束策略（例外 vs 真实同步结构），不做过宽 exception。
- C3 — 能完成一个多时钟 + I/O + exceptions 小设计的端到端 signoff 审计（check_timing → constraint audit → report_timing → closure → post-route verification）。

### Stretch Criteria
- S1 — 能说明 CDC 同步结构选择（两拍同步器/handshake/async FIFO）的适用条件，为后续 CDC Topic 铺垫。

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
