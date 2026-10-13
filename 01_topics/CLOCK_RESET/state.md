---
schema: topic_state
topic: CLOCK_RESET
status: ACTIVE
current_gate: CLOCK_RESET-GATE-G2
master_review_required: true
master_review_reason: OTHER
last_lesson_id: CLOCK_RESET-LSN-20261013-140247
---

# CLOCK_RESET State

## Master Directive

Objective:
建立可独立调用的 FPGA 时钟与复位架构能力，能为真实工程设计、约束并审查时钟生成/分发与复位体系。

Reason:
当前该能力为 L2，是 baseline 最弱项之一；Generated Clock/MMCM 是 STA_XDC 的遗留 defer 项，同时是后续 CDC、LVDS 与高速数据通路学习的直接前置。

## Current Objective
能为真实设计选择并实现正确的复位架构，并对其做约束与时序审查。

## Current Snapshot

Passed:
- CLOCK_RESET-GATE-G1：时钟生成与 Generated Clock 约束——C1/C2/C3 已通过低辅助最终验收。

In Progress:
- CLOCK_RESET-GATE-G2 仍 OPEN：C1=VERIFIED；C2/C3=PARTIAL。真实 Vivado P2/P3 实现与时序证据已取得，但最终低辅助综合验收尚未完成。

Not Yet Verified:
- G2-C2：两级 FDPE 的 PRE/连接及异步断言结构已有间接实现证据，仍缺最终实现的 ASYNC_REG 属性读回、完整 reset 请求/分发结构核对和扩展扇出情形的独立取舍证据。
- G2-C3：P2 Setup/Hold、P3 Recovery/Removal 实际报告均 MET；P1 输入复位路径/时序例外范围与约束覆盖尚未完成完整低辅助审查；早期 exceptions 报告不代表最终改版的独立审查。
- G2：尚无覆盖全部 Mandatory Criteria 且 Assistance<=A1 的当前 Gate PASS Evidence，不得机械标为 PASSED。
- G2-S1：能发现部分复位/控制缺陷，但陌生多寄存器并发设计的低辅助审查稳定性未证实。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `CLOCK_RESET-LSN-20261013-140247`
Status: `COMPLETE`
Gate: `CLOCK_RESET-GATE-G2`

Focus:
CLOCK_RESET-GATE-G2 的真实复位同步器实现、P2/P3 物理时序核查；并根据 Human 反馈转向 RTL 阅读、硬件结构识别与并发控制缺陷 Review。

Work:
Human Review 了既有 200/50 MHz 复位 RTL，指出敏感事件与复位判断不一致的问题；在 Tutor 明确指导下修改同步器与 Counter 并完成 Vivado 2018.3 Implementation。首轮 Counter 为 FDRE，异步路径未出现；修正后确认 16 个 FDCE/CLR。实际报告核对了 FF1→FF2 的 Setup/Hold 与 FF2→业务 FF/CLR 的 Recovery/Removal，所有已列路径 MET。人机交互式 RTL Review 覆盖 FF 控制端、en/tick、burst_ctrl 的多 always 并发缺陷，但并发审查仍有误报与遗漏。Human 多次反馈重复 Tcl/看 Slack、低难度问答与人工逐拍猜测没有带来足够学习价值，明确希望改进长期 Outline。本轮结尾 Human 要求停止 RTL 练习、Handoff，并希望 G2 Close。

Outcome:
工程层面 P2/P3 已取得真实、正 Slack 的 STA 证据（P2 Setup：200 MHz +3.960 ns / 50 MHz +18.839 ns；Hold：+0.375 / +0.434 ns。P3 Recovery：+3.815 / +18.641 ns；Removal：+0.345 / +0.413 ns。）。不把 Tutor 指导下的 MET、结构映射与零散 Review 答题冒充 G2 最终 A0/A1 综合 PASS；同步器 ASYNC_REG 读回、P1/约束例外最终审查及规模化 reset 分发判断仍不充分。Lesson 结课 COMPLETE，但当前 Gate 维持 OPEN。Master Review 以 OTHER 路由，请审查教学结构与后续节奏。

Gate Progress:
CLOCK_RESET-GATE-G1 维持 PASSED；CLOCK_RESET-GATE-G2 保持 OPEN，C1=VERIFIED，C2=PARTIAL，C3=PARTIAL，S1=PARTIAL（Stretch）。未产出符合全部 Mandatory Criteria 的 Gate PASS Evidence，因此不能按协议请求 PASSED。

Evidence:
本次追加 CLOCK_RESET-EXP-003（真实 Vivado P2/P3 工程证据，DEBUG/PARTIAL/A2）和 CLOCK_RESET-EXP-004（RTL 阅读与并发 Review 的独立表现，ASSESSMENT/PARTIAL/A0）。

Suggested Local Next:
不重复运行已经 MET 的 P2/P3，也不立即让 Human 做更多“鬼脑”穷举。Master 优先审查 Outline：将“读陌生 RTL -> 提取硬件结构/下一状态/协议不变量 -> 工具化验证”纳入长期跨 Topic 能力；为 G2 剩余属性/P1/例外与最终 A1 验收设计一次聚焦、低负担的真实工程审查，或确定何时恢复 G2。Human 要求尽快关闭 G2，但不得在缺少 Gate PASS Evidence 时虚构通过，也不由 Tutor 自行改写 Repo 或 Ability Profile。

## Evidence Anchors

- CLOCK_RESET-EXP-001
- CLOCK_RESET-EXP-002
- CLOCK_RESET-EXP-003
- CLOCK_RESET-EXP-004

## Open Questions / Deferred

- 请 Master 审查长期 Outline：是否将陌生 RTL 阅读、结构推断、优先级/并发协议审查、性质驱动验证作为贯穿多个 Topic 的明确能力目标。
- Human 请求停止低价值的脑内事件穷举练习，并希望当前 G2 尽快结束；Master 应决定剩余 G2 低辅助验收如何精简或安排后续 Topic，而不将 OPEN 伪记为 PASS。
