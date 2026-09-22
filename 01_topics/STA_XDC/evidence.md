---
schema: topic_evidence
topic: STA_XDC
mutation: APPEND_ONLY
---

# STA/XDC Evidence Ledger

> Evidence 是历史事实账本，只允许在末尾追加。
>
> 新 Lesson 只追加新的 Evidence Entry，不用最新 Handoff 覆盖旧 Evidence。
> 旧解释被推翻时，追加新的 Evidence / Amendment 语义条目并引用旧 ID，不静默重写历史。

## Evidence Entries

<!-- 在这里继续追加新的 Evidence Entry。 -->

### STA_XDC-EXP-001 — Vivado STA 报告实操与初步诊断

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `STA_XDC-GATE-G1`
Lesson: `STA_XDC-LSN-20260920-223248`
Observed At: `2026-09-22T03:07:46Z`

References:
- NONE

Artifacts:
- NONE

#### Observation
Human 在 Vivado 2018.3 / XC7A35T 教学工程中实际创建 4 ns 主时钟约束，读取并比较 Post-Synthesis 与 Post-Route timing report，能解释 setup/hold 的 arrival/required/slack 关系及负 slack 的物理意义；能识别 register-to-register 的 launch/capture、startpoint/endpoint，区分 Cell/Route Delay、Logic Levels、Clock Path Skew、Clock Uncertainty、Incr/Path，并能说明 unplaced estimated net delay 与 routed delay 的区别。Human 还通过加入流水线寄存器把 12 级 LUT 路径拆成两段约 6 级路径，并基于真实 Post-Route Setup/Hold 报告做初步诊断，能够指出证据支持的结论与尚不能宣布的根因。Tutor 对术语、个别符号和一次 Hold required-side 误判做了少量纠正。

#### Interpretation
该表现直接支持 C2 与 C3 达到 VERIFIED，并支持 C1 中 register-to-register、launch/capture、startpoint/endpoint 的理解。尚未低辅助独立验证 input-to-register、register-to-output、input-to-output 等全部常见路径类别，因此 C1 保持 PARTIAL，Gate 不请求 PASSED。该 Evidence 不支撑 placement/routing/fanout timing closure 能力。
