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

### STA_XDC-EXP-002 — 常见同步时序路径类别独立复测

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A0`
Gate: `STA_XDC-GATE-G1`
Lesson: `STA_XDC-LSN-20260922-132735`
Observed At: `2026-09-22T06:40:00Z`

References:
- STA_XDC-EXP-001

Artifacts:
- NONE

#### Observation
Human 在最终 A0 独立复测中，对 input-to-register、register-to-output、register-to-register 三条变式路径均正确判断 Timing Path Category（时序路径类别）、Startpoint（起点）、Endpoint（终点）以及内部 Launch/Capture Clock（发射/捕获时钟）是否存在；其中寄存器发起的路径均正确使用 Q 作为 Startpoint，不再将 Clock Pin（时钟引脚）C 与 Data Timing Path（数据时序路径）起点混淆。此前同一 Lesson 对四类常见路径的首轮判断中，Human 已正确识别 register-to-register、input-to-register、register-to-output、input-to-output 的类别、终点和 Launch/Capture 关系。

#### Interpretation
该表现直接补齐 C1 对常见路径类别以及 launch/capture、startpoint/endpoint 的低辅助独立验收，可将 C1 标为 VERIFIED。结合既有 STA_XDC-EXP-001 对 C2/C3 的 PASS 证据，当前 Gate 的 Mandatory Criteria 已全部满足，且本 Evidence 为 A0，不高于 Gate Maximum A1，因此支持 STA_XDC-GATE-G1 PASSED。该 Evidence 不支撑 Placement、Routing、Fanout 或更广泛 timing closure 能力。

### STA_XDC-EXP-003 — 基础 Clock/I-O Constraints 与 Vivado 约束覆盖综合验收

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `STA_XDC-GATE-G2`
Lesson: `STA_XDC-LSN-20260922-151406`
Observed At: `2026-09-23T15:07:00+02:00`

References:
- STA_XDC-EXP-001
- STA_XDC-EXP-002

Artifacts:
- NONE

#### Observation
Human 能依据 100/125 MHz 接口时钟独立确定 Clock Period 与参考边沿语义；能把 ADC Clock-to-Output Min/Max 转换为正的 set_input_delay -min/-max，把 DAC Setup/Hold Requirement 转换为 set_output_delay -max 与负的 -min，并在最终复测中正确填写 input max=4.5 ns、input min=1.2 ns、output max=2.0 ns、output min=-0.5 ns。Human 在 Vivado 2018.3 / XC7A35T 小型 I/O 工程中实际运行 check_timing，观察无 I/O Delay 时 no_input_delay/no_output_delay 报告、补齐约束后的归零，以及故意删除 Output -min 后 partial_output_delay 报 HIGH；同时发现并修正 get_ports 总线对象查询未命中的问题。最终 Timing Review 中，Human 能区分 Coverage、当前 STA Model 下 Timing Pass 与真实 Constraint Truth，并正确识别 ADC datasheet max=4.5 ns 而 XDC input -max=3.0 ns 会虚增 Setup Slack、制造 False Timing Pass。最终符号解释仍有一处把 input -min 归因于内部 Capture Register Hold 的表述偏差，经 Tutor 一次少量纠正后收紧。

#### Interpretation
该表现直接支持 G2 C1、C2、C3 达到 VERIFIED：Human 已具备在明确接口假设下建立基础时钟约束、转换基本 Input/Output Delay、使用真实 Vivado check_timing 检查完整/部分约束遗漏并审查明显错误假设的能力。最终综合任务仅需 A1 级少量语义纠正，不高于 Gate Maximum A1，因此支持 STA_XDC-GATE-G2 PASSED。该 Evidence 不支撑 Generated Clock/MMCM、Virtual Clock、复杂源同步接口或系统化 timing closure 能力。

### STA_XDC-EXP-004 — G3 Timing Exceptions and Timing Closure Integrated Verification

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `STA_XDC-GATE-G3`
Lesson: `STA_XDC-LSN-20260923-213152`

References:
- NONE

Artifacts:
- NONE

#### Observation
User independently distinguished false path and multicycle semantics; rejected exception-based masking of a true one-cycle violation; diagnosed a 32-level setup path and algebraically removed the serial dependency with functionally equivalent RTL, improving post-route slack from -2.500 ns to +9.158 ns and data path from 12.455 ns to 0.759 ns. User then isolated physical routing effects with forced placement: setup route delay changed from 0.380 ns to 3.370 ns and returned to 0.380 ns after removing LOC, while hold slack moved consistently with minimum-route delay. In the high-fanout experiment, user identified fanout as a diagnostic clue rather than proof, inspected an implementation-created replica (`IS_ORIG_CELL=0`, `ORIG_CELL_NAME=src_reg_reg`), and observed post-place `phys_opt_design -fanout_opt` deliberately perform zero optimization because WNS was already +0.139 ns. Final independent CDC audit correctly identified only the asynchronous input-to-first-synchronizer boundary as asynchronous and required first-to-second synchronizer plus downstream synchronous paths to remain timed; user identified an overbroad false path as a false PASS that can hide real hardware risk.

#### Interpretation
C1 verified: user understands false-path/MCP semantics, protocol preconditions, paired MCP hold behavior, and masking risk. C2 verified: user can diagnose setup/hold using slack, logic/route composition, skew/CPR, placement, fanout, and max/min routing behavior. C3 verified: user can choose and verify targeted closure actions with post-route reports rather than exceptions. S1 verified by independent rejection of overbroad CDC false-path scope. Gate G3 passes at acceptable assistance.
