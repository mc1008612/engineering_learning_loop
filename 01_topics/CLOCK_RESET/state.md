---
schema: topic_state
topic: CLOCK_RESET
status: ACTIVE
current_gate: CLOCK_RESET-GATE-G1
master_review_required: false
master_review_reason: NONE
last_lesson_id: NONE
---

# CLOCK_RESET State

## Master Directive

Objective:
建立可独立调用的 FPGA 时钟与复位架构能力，能为真实工程设计、约束并审查时钟生成/分发与复位体系。

Reason:
当前该能力为 L1，是 baseline 最弱项之一；Generated Clock/MMCM 是 STA_XDC 的遗留 defer 项，同时是后续 CDC、LVDS 与高速数据通路学习的直接前置。

## Current Objective
理解 7 系列时钟资源与 MMCM/PLL 结构，能在真实工程中正确约束 generated clock 并追踪 clock path。

## Current Snapshot

Passed:
- NONE

In Progress:
- CLOCK_RESET-GATE-G1：时钟生成与 Generated Clock 约束——MMCM/PLL 参数与时钟资源层级、create_generated_clock 建模、clock path 追踪。

Not Yet Verified:
- MMCM/PLL 结构与输出时钟关系的独立解释。
- 真实工程中 generated clock 的正确约束与源时钟关系说明。
- timing report / clock utilization 中 clock path、insertion delay 与 skew 的追踪。

## Current Blockers
- NONE

## Revalidation Flags
- NONE

## Last Lesson

Lesson ID: `NONE`
Status: `NONE`
Gate: `CLOCK_RESET-GATE-G1`

Focus:
NONE

Work:
NONE

Outcome:
NONE

Gate Progress:
NONE

Evidence:
NONE

Suggested Local Next:
开始第一堂 Lesson。

## Evidence Anchors
- NONE

## Open Questions / Deferred
- NONE
