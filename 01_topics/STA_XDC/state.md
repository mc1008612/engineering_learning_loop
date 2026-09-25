---
schema: topic_state
topic: STA_XDC
status: ACTIVE
current_gate: STA_XDC-GATE-G3
master_review_required: true
master_review_reason: TOPIC_LIFECYCLE
last_lesson_id: STA_XDC-LSN-20260923-213152
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
- STA_XDC-GATE-G3

In Progress:
- NONE

Not Yet Verified:
- NONE

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `STA_XDC-LSN-20260923-213152`
Status: `COMPLETE`
Gate: `STA_XDC-GATE-G3`

Focus:
STA/XDC G3：Timing Exception 安全使用、Setup/Hold 诊断、真实 Timing Closure、placement/routing/high-fanout 物理机制，以及 exception audit。

Work:
完成 false path 与 multicycle path 的真实实验；诊断 32-level setup violation 并通过 RTL 代数化简完成真实 closure；完成 forced-far placement A/B；完成 high-fanout 报告、replicated driver 属性检查、post-place `phys_opt_design -fanout_opt` 实验；最后独立完成 CDC/false-path 过宽审计。

Outcome:
G3 mandatory criteria C1/C2/C3 均 VERIFIED；stretch S1 通过最终独立 CDC exception audit 补齐为 VERIFIED。Gate 可判 PASSED。用户已形成“exception 描述功能事实而非修复 violation”“coverage/pass/truth 分离”“logic/route/placement/fanout 分层诊断”的稳定模型。

Gate Progress:
STA_XDC-GATE-G3 PASSED。用户在 A0/A1 下完成真实 report 驱动的 closure 判断，并能拒绝用 false path/MCP 隐藏真实单周期违例。

Evidence:
STA_XDC-EXP-004：G3 综合证据，包含 MCP/false-path masking、真实逻辑 closure A/B、物理 placement A/B、high-fanout/replication/phys_opt 实验及独立 CDC exception audit。

Suggested Local Next:
进入综合 signoff 场景：一个同时包含 multiple clocks、CDC、I/O delays、timing exceptions 和真实 timing violation 的小设计，按 `check_timing → constraint audit → report_timing → closure → post-route verification` 完成端到端审计；减少基础判断题，增加陌生 report/约束的工程诊断与独立决策。

## Evidence Anchors

- STA_XDC-EXP-001
- STA_XDC-EXP-002
- STA_XDC-EXP-003
- STA_XDC-EXP-004

## Open Questions / Deferred

- Generated Clock/MMCM、Virtual Clock 与复杂源同步接口的约束建模留待后续专门安排；STA_XDC Topic 完成确认将在 G3 PASSED 后由 Master Review 处理。
