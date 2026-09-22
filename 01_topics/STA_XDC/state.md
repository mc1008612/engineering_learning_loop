---
schema: topic_state
topic: STA_XDC
status: ACTIVE
current_gate: STA_XDC-GATE-G1
master_review_required: true
master_review_reason: CURRICULUM_CHECKPOINT
last_lesson_id: STA_XDC-LSN-20260922-132735
---

# STA/XDC State

## Master Directive

Objective:
建立可独立调用的 STA/XDC 工程能力，能约束、审查并关闭常见同步设计时序问题。

Reason:
当前该能力为 L1，同时是后续 Clock/Reset、CDC、LVDS 和高速数据通路学习的共同基础。

## Current Objective
建立同步时序分析的基本心智模型，并能独立阅读基础 Timing Report。

## Current Snapshot

Passed:
- STA_XDC-GATE-G1：同步时序模型与 Timing Report 阅读已完成验收。

In Progress:
- NONE

Not Yet Verified:
- NONE

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `STA_XDC-LSN-20260922-132735`
Status: `COMPLETE`
Gate: `STA_XDC-GATE-G1`

Focus:
完成 STA_XDC-GATE-G1 的 C1 独立复测，验证常见 Timing Path Category（时序路径类别）、Startpoint（起点）/Endpoint（终点）以及内部 Launch/Capture Clock（发射/捕获时钟）的识别能力。

Work:
先对 register-to-register、input-to-register、register-to-output、input-to-output 四类路径做 A0 复测。Human 首轮能正确判断四类 Path Category、Endpoint 与 Launch/Capture 关系，但在 register-originated path 中两次把寄存器 Clock Pin（时钟引脚）C 写成 Startpoint。Tutor 仅指出 C 属于 Clock Path（时钟路径）、Q 才是 Data Timing Path（数据时序路径）的 Startpoint，并要求立即再次独立复测。随后 Human 在不依赖进一步提示的三类变式中，正确给出 input-to-register、register-to-output、register-to-register 的 Category、Startpoint、Endpoint 以及内部 Launch/Capture Clock 有无关系。

Outcome:
C1 由 PARTIAL 提升为 VERIFIED。结合既有 STA_XDC-EXP-001 对 C2/C3 的真实 Vivado 实操验证，STA_XDC-GATE-G1 的 Mandatory Criteria（强制验收项）现已全部满足；本 Lesson 新产生 A0 PASS Evidence，可满足 Gate Assistance ceiling，因此请求将 STA_XDC-GATE-G1 标记为 PASSED。本结论不扩展到 Placement（布局）、Routing（布线）、Fanout（扇出）等 timing closure（时序收敛）能力。

Gate Progress:
C1: VERIFIED
C2: VERIFIED
C3: VERIFIED
STA_XDC-GATE-G1: PASSED

Evidence:
STA_XDC-EXP-002

Suggested Local Next:
当前 Gate 已到达 Curriculum Checkpoint（课程检查点），请求 Master Review 处理 G1 PASSED 后的课程路由与下一 Gate 选择；不要在本 Lesson 本地继续扩展 Placement/Routing/Fanout timing closure。

## Evidence Anchors

- STA_XDC-EXP-001
- STA_XDC-EXP-002

## Open Questions / Deferred

- Placement、Routing、Fanout 等系统化 timing closure 调试超出当前 G1，留待后续 Gate。
