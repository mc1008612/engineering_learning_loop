---
schema: topic_state
topic: STA_XDC
status: ACTIVE
current_gate: STA_XDC-GATE-G3
master_review_required: false
master_review_reason: NONE
last_lesson_id: STA_XDC-LSN-20260922-151406
---

# STA/XDC State

## Master Directive

Objective:
建立可独立调用的 STA/XDC 工程能力，能约束、审查并关闭常见同步设计时序问题。

Reason:
当前该能力为 L2，同时是后续 Clock/Reset、CDC、LVDS 和高速数据通路学习的共同基础。

## Current Objective
能够谨慎使用时序例外，并针对常见时序违例形成可验证的 closure 策略。

## Current Snapshot

Passed:
- STA_XDC-GATE-G1：同步时序模型与 Timing Report 阅读已完成验收。
- STA_XDC-GATE-G2：基础 Clock 与 I/O Constraints、约束覆盖检查已完成验收。

In Progress:
- STA_XDC-GATE-G3：Exceptions 与 Timing Closure——时序例外语义、违例定位与可验证的 closure 策略。

Not Yet Verified:
- STA_XDC-GATE-G3 C1–C3：时序例外语义与适用条件、常见 setup/hold 问题定位、closure 措施与报告验证均未验收。
- Generated Clock/MMCM、Virtual Clock 与更复杂 Source-Synchronous Interface 的系统约束建模尚未验证，超出 G3 Mandatory 范围。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `STA_XDC-LSN-20260922-151406`
Status: `COMPLETE`
Gate: `STA_XDC-GATE-G2`

Focus:
完成 STA_XDC-GATE-G2 的基础 Clock Constraint（时钟约束）、I/O Delay Constraint（输入输出延迟约束）与 Constraint Coverage（约束覆盖）学习和验收；重点建立“外部接口时序如何接入 FPGA 内部 STA 模型”的工程心智模型，并在 Vivado 2018.3 / XC7A35T-FGG484-2 环境中实际观察约束覆盖问题。

Work:
Lesson 前半段从 ADC → FPGA 的 Input-to-Register（输入到寄存器）接口出发，区分发送器 Output Timing Guarantee（输出时序保证）与接收器 Setup/Hold Requirement（建立/保持要求），建立 Reference Clock Edge（参考时钟边沿）、Clock-to-Output Delay（时钟到输出延迟）、Input Delay Min/Max（最小/最大输入延迟）的关系。Human 能推导数据最早/最晚到达窗口、下一 Capture Edge（捕获边沿）以及 Setup/Hold Budget（建立/保持时间预算），并主动指出“STA 不需要现实绝对时间戳，但需要时钟边沿间相对关系”。期间 Tutor 曾过早引入未教学的 MMCM / Generated Clock（生成时钟）故障题，且早期 Mermaid 因果图存在误导；Human 主动质疑并推动模型修正，该题不计入验收。

随后转到 Output Delay（输出延迟），Human 能从 DAC Setup/Hold Requirement 推导 `set_output_delay -max` 与 `-min` 的数值，最终独立填写：
`input max = +4.5 ns`、`input min = +1.2 ns`、`output max = +2.0 ns`、`output min = -0.5 ns`。Human 已能区分 Input Delay 是把外部发送器的数据到达窗口接入 STA，而 Output Delay 是把外部接收器的 Setup/Hold 要求反推到 FPGA 输出边界。最终解释中曾把 Input `-min` 误称为描述 FPGA 内部 Capture Register Hold，Tutor 以少量纠正收紧为“发送器最早数据到达保证”；数值转换本身正确。

Vivado 实操阶段，Human 在真实小型工程中自行经历只有 Clock Constraint、补齐 I/O Delay、再故意删除一个 `-min` 的 Coverage Fault（覆盖故障）。实际 `check_timing` 观察到无 I/O Delay 时 `no_input_delay/no_output_delay` 报 HIGH，补齐后相关项归零，故意漏掉 Output `-min` 后观察到 `partial_output_delay` HIGH。Human 还实际发现 `[get_ports {sensor_data[3:0]}]` 未匹配预期对象并改用 `[get_ports {sensor_data[*]}]`，认识到 XDC Object Query（对象查询）是否真正选中目标对象本身就是约束审查的一部分。

最终综合 Review 中，Human 能正确说明 `check_timing` 全零主要支持 Coverage 完整性而不证明约束事实正确；WNS/WHS > 0 只表示当前 STA 模型和约束假设下被分析路径通过；不能仅凭 Timing Summary 全绿宣布真实硬件时序正确，仍需把 Datasheet / Board / RTL-Netlist / XDC / Timing Report 对齐。面对 ADC datasheet `tCO max = 4.5 ns` 而 XDC 写成 `input -max 3.0 ns`，Human 正确识别其会虚增 Setup Slack 并制造 False Timing Pass（虚假时序通过）。Human 首轮同时错误怀疑 `input -min +1.0 ns` 符号，Tutor 纠正后进行了最后一次符号复测并正确填写四个数值。

Outcome:
C1、C2、C3 均达到 VERIFIED。Human 已能在明确接口时序假设下建立基础 Clock Constraint，完成 Input/Output Delay 的基本数值转换，并在真实 Vivado 2018.3 工程中检查完整遗漏与部分遗漏；最终 Review 还能区分 Constraint Coverage、当前模型下 Timing Pass 与 Constraint Truth（约束是否真实）。本 Lesson 产生一条 A1 PASS Evidence，符合当前 Gate Maximum A1，因此请求将 STA_XDC-GATE-G2 标记为 PASSED。该结论不扩展到 Generated Clock/MMCM 的系统建模、Virtual Clock（虚拟时钟）的系统使用、复杂 Source-Synchronous Interface（源同步接口）或 Placement/Routing/Fanout timing closure。

Gate Progress:
C1: VERIFIED
C2: VERIFIED
C3: VERIFIED
S1: NOT_VERIFIED
STA_XDC-GATE-G2: PASSED

Evidence:
STA_XDC-EXP-003

Suggested Local Next:
当前 Mandatory Criteria 已全部 VERIFIED，且已有符合 Assistance ceiling 的当前 Gate PASS Evidence，请 Master Review 处理 G2 PASSED 后的课程路由；不要在本 Lesson 本地继续扩展 S1。教学过程反馈也请 Master 纳入下一 Lesson 设计：本 Lesson 前半段概念问答重复度偏高、推进量偏少，且曾在基础模型尚未稳定时提前引入 MMCM/Generated Clock；下一 Lesson 建议提高单课信息与任务密度，在概念经一次或两次低辅助验证后尽早切换到真实 Vivado 2018.3 工程，以真实 report / schematic / device / Tcl Console 为主要教学载体，减少连续同型口头推导。仍保持“预测 → 操作 → 观察 → 解释”，但让预测直接服务于即将执行的工程动作。

## Evidence Anchors

- STA_XDC-EXP-001
- STA_XDC-EXP-002
- STA_XDC-EXP-003

## Open Questions / Deferred

- Generated Clock/MMCM、Virtual Clock 与复杂源同步接口的约束建模留待后续专门安排；STA_XDC Topic 完成确认将在 G3 PASSED 后由 Master Review 处理。
