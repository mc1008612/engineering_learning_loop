---
schema: topic_notes
topic: STA_XDC
mutation: CURATED
---

# STA/XDC Notes

## Durable Mental Models

- 建立检查〈Setup〉使用 Slack = Required - Arrival；负 Slack 表示数据来得太晚。保持检查〈Hold〉使用 Slack = Arrival - Required；负 Slack 表示新数据来得太早。
- Post-Synthesis 的 unplaced net delay 是估计值；Post-Route 的 routed net delay 才对应实际物理实现，最终 timing signoff 应看 Post-Route。
- Timing 诊断应逐层推进：Slack 是症状，Cell/Route 构成给出主导因素，Details 的 Incr 定位具体段，再结合 placement/fanout 等物理信息追根因；不要从一个 Summary 数字直接宣布根因。
- 流水线〈Pipeline〉通过插入寄存器把一条长组合路径拆成多条更短的时序路径；它增加功能 Latency，但填满后可保持每拍吞吐。后级重新汇合的各数据分支必须保持流水级对齐。
- 保持路径的危险程度不能仅由 Logic Levels 或 Route Delay 长短预测；必须同时比较 Data Arrival Time 与 Data Required Time，包括 endpoint hold requirement、clock skew/CPR 等 required-side 因素。
- 对于寄存器发起的数据时序路径，Data Timing Path（数据时序路径）的 Startpoint（起点）是寄存器 Q；寄存器 C 属于 Clock Path（时钟路径），不是数据路径 Startpoint。

## Engineering Rules

- 使用真实 Timing Report 时区分路径类别〈如 register-to-register〉与 Vivado Path Type〈Setup (Max) / Hold (Min)〉。
- Vivado Summary 中的 Requirement 是路径时钟关系要求，不等同于 Data Required Time；后者还包含时钟路径、uncertainty、setup/hold arc 等因素。
- 使用 Data Path Delay 时不要再次单独叠加 Clock-to-Q；Vivado 的 Data Path Delay 已包含 launch register 的 Clock-to-Q 贡献。
- Route Delay 占比高本身不能证明 Router/Placement 有问题；应查看单段 Incr、Location、Fanout 和 routed 状态。
- 查看实际 route：Implemented Design 中选择 Timing Path，在 Device 窗口打开 Routing Resources 并使用 Auto-fit Selection；Schematic 用于查看同一路径的逻辑结构。

## Debug Checklist

- 先读 Timing Summary：Source、Destination、Path Type、Requirement、Slack、Data Path Delay、Logic Levels、Clock Path Skew、Clock Uncertainty。
- 再读 Timing Path Details：优先找最大的 Incr，判断它属于 Cell 还是 Net，并确认 Net 是 unplaced/estimated 还是 routed。
- 对于 Post-Route 物理问题，用 Timing path 与 Schematic/Device 交叉定位后，再决定是否需要调查 fanout、placement、routing、congestion 或物理优化。

## Common Failure Modes

- 把 Setup 负 Slack 读成数据早到，或把 Hold 负 Slack 读成数据晚到。
- 把 Vivado 的 Path Requirement 与 Data Required Time 混为同一个量。
- 把 Post-Synthesis 的 unplaced Route Delay 当成实际布线延迟。
- 仅凭 Logic Levels 最少就断定它一定是最差 Hold 路径，而忽略 endpoint hold requirement 与 clock path required-side 因素。
- 看到 Route Delay 占比高就直接归因于 Router，而没有继续检查单段 net、placement 和 fanout。
- 把寄存器 Clock Pin（时钟引脚）C 当作 register-to-register 或 register-to-output 路径的 Startpoint；应检查路径的数据端是否从 Q 发起。

## References Worth Reusing

- AMD/Xilinx UG906 v2018.3 — Vivado Design Analysis and Closure Techniques。
- AMD/Xilinx UG904 v2018.3 — Vivado Implementation。
- AMD/Xilinx UG893 v2018.3 — Using the Vivado IDE（Device/Schematic 可视化）。
- AMD/Xilinx UG888 v2018.1 — Design Flows Overview Tutorial（Timing Path 与 Device Routing Resources 交叉查看）。
