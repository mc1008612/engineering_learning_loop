---
schema: topic_notes
topic: CLOCK_RESET
mutation: CURATED
---

# CLOCK_RESET Notes

## Durable Mental Models

- MMCM/PLL 负责时钟生成与管理；BUFG/BUFR 负责把已有时钟接入相应的专用分发网络。BUFG/BUFR 的选择首先取决于覆盖范围与网络资源，而不是单纯取决于频率。
- MMCM 共享 VCO：F_VCO = F_IN * M / D，各输出再由各自 O 分频得到 F_OUT = F_VCO / O；M 属于反馈路径关系，D 为输入分频，O 为输出分频。
- Generated clock 不是与源时钟无关的独立 create_clock；它保留与 master clock 的频率、相位/边沿等派生关系。标准 MMCM/PLL primitive 通常可由 Vivado 自动派生。
- Clock delay 看每一侧时钟到达经历了多少有效延迟；clock skew 看 launch/capture 两侧的到达差。公共路径自身有延迟，不等于产生同等大小的真实 skew。
- CPR 是 STA 数学修正而非物理电路：它消除 common clock path 在 launch/capture 两侧分别套用不利 max/min 条件时产生的虚假悲观差异。

## Engineering Rules

- 标准 MMCM/PLL 输出已被 Vivado 正确 auto-derived 时，通常不要重复手写 create_generated_clock；只有工具不能正确推导或普通用户逻辑确实产生/修改 clock relationship 等场景才显式建模。
- 判断时钟使用 global 还是 regional network，优先结合 report_clock_utilization 的资源/driver 信息与 timing clock path 交叉确认。

## Debug Checklist

- 检查 generated clock 时同时确认 master/source、definition point、period/edge relationship，以及是否为 auto-derived 或 user-defined。
- 分析 clock skew 时先区分 SCD、DCD、CPR，再检查公共路径分叉后的非公共 clock path 差异。

## Common Failure Modes

- 把 BUFG 记成普通逻辑网络的“增强驱动中继器”，从而忽略其接入专用 global clock network 的架构角色。
- 用时钟频率高低直接决定 BUFG/BUFR，而忽略 clock region 覆盖需求。
- 把 clock path 中每一段累计 delay 直接等同于 skew，忽略 launch/capture 公共路径与差分到达时间。
- 在已有正确 auto-derived generated clock 的定义点重复手写约束，造成不必要的覆盖或错误模型。

## References Worth Reusing

- Vivado 2018.3：report_clocks、report_clock_utilization、report_timing 可联合用于 generated clock、clock primitive/network 与 SCD/DCD/skew/CPR 的工程核查。
