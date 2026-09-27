---
schema: topic_evidence
topic: CLOCK_RESET
mutation: APPEND_ONLY
---

# CLOCK_RESET Evidence Ledger

> Evidence 是历史事实账本，只允许在末尾追加。
>
> 新 Lesson 只追加新的 Evidence Entry，不用最新 Handoff 覆盖旧 Evidence。
> 旧解释被推翻时，追加新的 Evidence / Amendment 语义条目并引用旧 ID，不静默重写历史。

## Evidence Entries

<!-- 在这里继续追加新的 Evidence Entry。 -->

### CLOCK_RESET-EXP-001 — G1 时钟生成、Generated Clock 与 Clock Path 低辅助复测

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `CLOCK_RESET-GATE-G1`
Lesson: `CLOCK_RESET-LSN-20260925-234151`

References:
- NONE

Artifacts:
- NONE

#### Observation
Human 在真实 Vivado 2018.3 / XC7A35T 时钟工程学习后完成低辅助复测：能审查“MMCM 只是倍频器、BUFG 只是增强驱动、按频率选择 BUFG/BUFR”等错误模型，说明 MMCM/PLL 的时钟管理角色、BUFG/BUFR 的 global/regional 分发角色及 M/D/O 与 VCO/输出关系；能说明标准 MMCME2_ADV 输出通常由 Vivado auto-derived 为 generated clock、重复手写 create_generated_clock 通常无必要且可能替代自动模型，并识别普通用户逻辑产生/修改时钟等显式建模需求；能从 timing/clock utilization 识别 MMCM -> BUFG -> global clock routing -> FF/C，区分 clock delay 与 skew，并在最终 A1 CPR 题中独立得到无 CPR skew=-0.35 ns、CPR=+0.18 ns、最终 skew=-0.17 ns，说明 CPR 消除 common clock path 上 max/min 独立建模产生的虚假悲观，剩余 skew 主要来自非公共路径的有效 delay difference。

#### Interpretation
该表现直接覆盖 G1 的 C1/C2/C3，且最终 PASS Evidence 的 assistance=A1，不高于 Gate Maximum=A1，因此支持 CLOCK_RESET-GATE-G1 PASSED。该 Evidence 不证明 reset recovery/removal、metastability 传播或 reset synchronizer 物理机制已经独立掌握。
