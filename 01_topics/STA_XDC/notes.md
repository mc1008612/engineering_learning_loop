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
- I/O Delay Constraint 的作用是把 FPGA 看不到的外部世界接入内部 STA 模型：Input Delay 描述外部发送器数据相对于接口 Reference Clock Edge 到达 FPGA Input Port 的最早/最晚窗口；Output Delay 把外部接收器的 Setup/Hold Requirement 反推为 FPGA Output Port 必须满足的时序边界。
- STA 不需要现实世界的绝对时间戳，但必须知道 Clock Edge 之间的相对位置；相同 Frequency/Period 不等于相同 Phase/Edge Relationship。
- Constraint Coverage、当前 STA Model 下 Timing Pass 与 Constraint Truth 是三个不同层次：约束覆盖完整和 Slack 为正都不能单独证明 XDC 正确描述了真实硬件。
- Timing exceptions describe functional timing facts; they do not repair physical timing violations.
- Constraint Coverage, Timing Pass under the model, and Constraint Truth are separate questions.
- High fanout is a suspect indicator, not proof of a timing bottleneck; delay remains source-to-sink and placement dependent.
- Post-place net delay is estimated; post-route routed delay is the signoff-quality physical result.
- Driver replication helps primarily by changing driver-to-load physical topology and clustering loads, not merely by reducing a fanout number.
- An asynchronous origin does not make all descendant paths asynchronous: after the first synchronizer stage, same-clock paths remain real STA paths.

## Engineering Rules

- 使用真实 Timing Report 时区分路径类别〈如 register-to-register〉与 Vivado Path Type〈Setup (Max) / Hold (Min)〉。
- Vivado Summary 中的 Requirement 是路径时钟关系要求，不等同于 Data Required Time；后者还包含时钟路径、uncertainty、setup/hold arc 等因素。
- 使用 Data Path Delay 时不要再次单独叠加 Clock-to-Q；Vivado 的 Data Path Delay 已包含 launch register 的 Clock-to-Q 贡献。
- Route Delay 占比高本身不能证明 Router/Placement 有问题；应查看单段 Incr、Location、Fanout 和 routed 状态。
- 查看实际 route：Implemented Design 中选择 Timing Path，在 Device 窗口打开 Routing Resources 并使用 Auto-fit Selection；Schematic 用于查看同一路径的逻辑结构。
- 发送器 Clock-to-Output Min/Max 可直接形成同一参考时钟下的 set_input_delay -min/-max 数据到达窗口；Input -min 通常保持为发送器给出的正的最早到达时间。
- 外部接收器 Setup/Hold Requirement 在基础同边沿模型下对应 set_output_delay -max = Setup、set_output_delay -min = -Hold；负号是 Output Delay 坐标/建模语义，不代表物理负延迟。
- XDC Object Query 是否真正命中预期端口是 Constraint Review 的一部分；约束数值正确但 get_ports/get_pins 未选中目标对象，等价于约束没有正确落到设计上。
- For a true one-cycle setup violation, diagnose logic depth, route share, placement, fanout, and architecture before considering exceptions.
- Use MCP only when protocol or microarchitecture genuinely permits later capture; pair setup/hold semantics correctly.
- Use false path only for relationships that functionally must not be timed; audit matched objects and downstream scope.
- Evaluate physical optimization by timing and implementation quality, not by whether fanout counts look smaller.
- Pipeline is a legitimate architectural closure technique when added latency and control/data alignment are acceptable.

## Debug Checklist

- 先读 Timing Summary：Source、Destination、Path Type、Requirement、Slack、Data Path Delay、Logic Levels、Clock Path Skew、Clock Uncertainty。
- 再读 Timing Path Details：优先找最大的 Incr，判断它属于 Cell 还是 Net，并确认 Net 是 unplaced/estimated 还是 routed。
- 对于 Post-Route 物理问题，用 Timing path 与 Schematic/Device 交叉定位后，再决定是否需要调查 fanout、placement、routing、congestion 或物理优化。
- 基础 I/O Constraint Review 时同时核对真实接口方向、谁产生 Data、谁 Capture、Capture Reference Clock、Datasheet 的发送器输出时序或接收器 Setup/Hold、XDC 数值与对象查询，以及 check_timing 的 no_input_delay/no_output_delay/partial_input_delay/partial_output_delay。
- 看到 Timing Summary 全绿时，继续把 Datasheet/Board、RTL/Netlist、XDC 与 Timing Report 对齐；特别检查过于乐观的 input -max 等错误是否会人为虚增 Slack。
- Start from WNS/WHS and confirm the constraint/clock relationship being analyzed.
- Split Data Path Delay into logic and route; inspect Logic Levels and per-element Incr values.
- For route-dominated paths, inspect source/destination placement, fanout, sink distribution, and clock skew/CPR.
- After any closure action, rerun implementation as required and verify with post-route timing rather than assuming improvement.
- For CDC/false-path review, explicitly identify the asynchronous boundary, first synchronizer stage, second stage, and downstream synchronous logic.

## Common Failure Modes

- 把 Setup 负 Slack 读成数据早到，或把 Hold 负 Slack 读成数据晚到。
- 把 Vivado 的 Path Requirement 与 Data Required Time 混为同一个量。
- 把 Post-Synthesis 的 unplaced Route Delay 当成实际布线延迟。
- 仅凭 Logic Levels 最少就断定它一定是最差 Hold 路径，而忽略 endpoint hold requirement 与 clock path required-side 因素。
- 看到 Route Delay 占比高就直接归因于 Router，而没有继续检查单段 net、placement 和 fanout。
- 把寄存器 Clock Pin（时钟引脚）C 当作 register-to-register 或 register-to-output 路径的 Startpoint；应检查路径的数据端是否从 Q 发起。
- 把发送器的 Clock-to-Output Min（最早新数据出现时间）误当成接收器内部 Hold Requirement，从而错误地给 set_input_delay -min 添加负号。
- 看到 check_timing 全零或 All user specified timing constraints are met 就宣布真实硬件时序正确；这些结果只能在各自范围内证明 Coverage 或当前模型下的约束满足。
- 在基础 I/O 时序模型尚未稳定时过早混入 MMCM/Generated Clock 等未教学变量，会把当前验收问题变成对后续知识的隐性测试。
- Using false path or MCP because slack is bad rather than because functionality justifies the exception.
- Treating `report_high_fanout_nets` as a list of violations.
- Assuming a high-fanout optimization must run even when there is no setup violation.
- Comparing post-place estimated routing delay directly with post-route routed delay as if they were equivalent.
- Cutting synchronizer stage-to-stage or downstream synchronous timing because the original external signal is asynchronous.

## References Worth Reusing

- AMD/Xilinx UG906 v2018.3 — Vivado Design Analysis and Closure Techniques。
- AMD/Xilinx UG904 v2018.3 — Vivado Implementation。
- AMD/Xilinx UG893 v2018.3 — Using the Vivado IDE（Device/Schematic 可视化）。
- AMD/Xilinx UG888 v2018.1 — Design Flows Overview Tutorial（Timing Path 与 Device Routing Resources 交叉查看）。
- Vivado 2018.3 timing reports showing forced-placement setup/hold A/B behavior.
- Vivado 2018.3 high-fanout report and replica properties for `src_reg_reg` / `src_reg_reg_rep`.
- Vivado 2018.3 post-place `phys_opt_design -fanout_opt` log showing `No setup violation found. Fanout Optimization was not performed.`
- The 32-level combinational-path RTL simplification experiment as the canonical example of real closure versus timing-exception masking.
