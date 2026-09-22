---
schema: topic_state
topic: STA_XDC
status: ACTIVE
current_gate: STA_XDC-GATE-G1
master_review_required: false
master_review_reason: NONE
last_lesson_id: STA_XDC-LSN-20260920-223248
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
- NONE

In Progress:
- STA_XDC-GATE-G1：同步时序模型与 Timing Report 阅读；C2/C3 已通过真实 Vivado 实操验证，C1 尚缺常见路径类别的完整独立复测。

Not Yet Verified:
- C1 中 input-to-register、register-to-output、input-to-output 等常见路径类别的独立识别与对应 startpoint/endpoint 判断。

## Current Blockers

- NONE

## Revalidation Flags

- 初始 STA/XDC 能力来自自评；本 Lesson 已直接验证 C2/C3 与 C1 的 register-to-register 部分，C1 完整路径类别识别仍待复测。

## Last Lesson

Lesson ID: `STA_XDC-LSN-20260920-223248`
Status: `COMPLETE`
Gate: `STA_XDC-GATE-G1`

Focus:
建立同步时序分析的基本心智模型，并在 Vivado 2018.3 真实工程中阅读 Setup/Hold Timing Report。

Work:
从 launch/capture、setup/hold、arrival/required/slack 开始，补充 startpoint/endpoint、常见 Timing Path、SCD/DCD、Clock Skew、Clock Uncertainty、Cell/Route Delay、Logic Levels、Incr/Path 等概念。Human 新建独立 Artix-7 教学工程，使用 `create_clock -period 4.000`，对比 Post-Synthesis 与 Post-Route 报告，观察 unplaced estimated net delay 到 routed delay 的变化；随后加入 pipeline register，将 12 级 LUT 长路径拆成两段约 6 级路径，并检查真实 Setup/Hold 结果。Lesson 末还确认了 Timing Path 在 Schematic/Device 中的可视化入口，但未展开 placement/routing/fanout timing closure。

Outcome:
C2 与 C3 已有真实工程实操支持；C1 中 register-to-register、launch/capture、startpoint/endpoint 已表现稳定，但尚未低辅助独立复测 input-to-register、register-to-output、input-to-output 等全部常见路径类别。Human 已能从真实 Vivado 报告区分估计/实际 routing、Cell/Route 主导因素及证据边界；末尾对最差 Hold 路径的初始“route 更长”归因经报告核对后修正为 required-side（尤其 endpoint hold requirement）差异主导。

Gate Progress:
C1: PARTIAL
C2: VERIFIED
C3: VERIFIED
Gate remains OPEN；未请求 PASSED。

Evidence:
STA_XDC-EXP-001

Suggested Local Next:
下一 Lesson 开头用 A0 做一个很短的 C1 独立复测：给出 register-to-register、input-to-register、register-to-output、input-to-output 四类路径，让 Human 独立判断 path category、startpoint/endpoint 与 launch/capture（适用时）。若通过，可将 C1 标为 VERIFIED 并评估 STA_XDC-GATE-G1 PASSED。不要在 G1 内继续展开 placement/routing/fanout timing closure；该主题留待后续 Gate。

## Evidence Anchors

- STA_XDC-EXP-001

## Open Questions / Deferred

- Placement、Routing、Fanout 等系统化 timing closure 调试超出当前 G1，留待后续 Gate。
