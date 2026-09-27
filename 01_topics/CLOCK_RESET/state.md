---
schema: topic_state
topic: CLOCK_RESET
status: ACTIVE
current_gate: CLOCK_RESET-GATE-G1
master_review_required: true
master_review_reason: CURRICULUM_CHECKPOINT
last_lesson_id: CLOCK_RESET-LSN-20260925-234151
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
- CLOCK_RESET-GATE-G1：时钟生成与 Generated Clock 约束——C1/C2/C3 已通过低辅助最终验收。

In Progress:
- NONE

Not Yet Verified:
- Reset architecture 的 recovery/removal、metastability 传播与 reset synchronizer 物理安全边界尚未形成独立验收 Evidence。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `CLOCK_RESET-LSN-20260925-234151`
Status: `COMPLETE`
Gate: `CLOCK_RESET-GATE-G1`

Focus:
完成 CLOCK_RESET-GATE-G1：建立 7 Series MMCM/PLL、BUFG/BUFR 的时钟架构模型；在 Vivado 2018.3 / XC7A35T-FGG484-2 真实工程中理解 generated clock 的自动推导与手写建模；从 timing report / clock utilization 追踪 clock path、SCD/DCD、skew、CPR 与 clock network。期间由真实时钟工程延伸讨论了 reset synchronizer、recovery/removal 与 metastability，但该支线不作为 G1 PASS 的主要依据。

Work:
从已有 STA 能力做迁移探测；补齐 MMCM/PLL、VCO、M/D/O、BUFG/BUFR 与 global/regional clock network；使用 Clock Wizard 建立 100 MHz -> 200 MHz / 50 MHz 最小工程并完成仿真、implementation；观察 report_clocks、report_clock_utilization 和 report_timing；验证 auto-derived generated clocks，并实际手写 create_generated_clock；分析 MMCM -> BUFG -> global clock routing -> FF/C、SCD/DCD、clock skew 与 CPR。课程后段回到 G1，以 A0/A1 低辅助方式完成 C1/C2/C3 独立复测。

Outcome:
G1 mandatory criteria C1/C2/C3 均达到 VERIFIED。最终复测中，Human 能区分 MMCM 时钟管理与 BUFG/BUFR 分发角色，解释 M/D/O 与输出关系；能判断标准 MMCME2_ADV 输出通常由 Vivado 自动派生 generated clock、重复手写可能覆盖自动模型，并指出普通用户逻辑产生/修改时钟等需要显式建模的场景；能解释 clock delay 与 skew 的区别、识别 global clock network，并在 A1 最终题中正确计算 CPR 对公共时钟路径悲观的修正。Gate 达到 PASS 条件。

Gate Progress:
CLOCK_RESET-GATE-G1: PASSED. C1=VERIFIED, C2=VERIFIED, C3=VERIFIED.

Evidence:
CLOCK_RESET-EXP-001 — PASS / ASSESSMENT / A1.

Suggested Local Next:
G1 已通过并到达当前 curriculum checkpoint。交回 Master Review 决定 CLOCK_RESET 的下一 Gate / Lesson。后续若继续 reset architecture，应从本课尚未完全闭环的 recovery/removal 与 metastability 物理机制继续，而不要重新讲已通过的 BUFG/MMCM/generated-clock 基础。

## Evidence Anchors

- CLOCK_RESET-EXP-001

## Open Questions / Deferred

- 后续 CLOCK_RESET Gate 应如何承接 reset architecture，由 Master Review 决定。
