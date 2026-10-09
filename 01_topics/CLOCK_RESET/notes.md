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
- D 输入违反 setup/hold 与异步控制释放违反 recovery/removal，是两种让同一 FF 再生存储核心接近微小差分偏置的入口；亚稳态的核心是解析时间不确定，存储节点不是在 0/1 间不断振荡。
- 高有效 async preset 的两级 reset synchronizer：raw arst 同时到 FF1/FF2 的 PRE，FF1/D=0，FF2/D=FF1/Q，最终同步释放 reset 取 FF2/Q；两级 FF 均可具有异步控制引脚。
- 异步释放撞到首个 clock edge 时，FF1 可能亚稳，但 FF2 此拍正常从旧 Q1=1 保持 reset；后级采样 FF1/Q 的风险属于 D 输入的亚稳态传播，并非把 P2 改判成 recovery/removal。
- 普通 STA 按时序路径的 endpoint pin 选择检查：D 端做 setup/hold，PRE/CLR 等异步控制端释放做 recovery/removal；STA 不模拟 FF 亚稳造成的随机延长 clock-to-Q。

## Engineering Rules

- 标准 MMCM/PLL 输出已被 Vivado 正确 auto-derived 时，通常不要重复手写 create_generated_clock；只有工具不能正确推导或普通用户逻辑确实产生/修改 clock relationship 等场景才显式建模。
- 判断时钟使用 global 还是 regional network，优先结合 report_clock_utilization 的资源/driver 信息与 timing clock path 交叉确认。
- RTL 的 async reset/preset 语义决定 FF 功能；ASYNC_REG 表达同步链的工具意图，并不会给本来没有异步控制的 FF 添加 PRE/CLR。第一拍要异步断言到最终输出，不能只让第一级具 async preset 而第二级是普通 FF。
- 同一时钟域内、具有启动依赖的模块应共享可信的 reset-release event；不要仅为 fanout 任意复制独立 raw-async synchronizer。工具 driver replication 不等于人工增加一级 registered reset tree。
- 若为分发而增加 local reset register，需要审查分支是否平衡、整体新增 latency、以及 local reset 是否仍满足必需的 async assertion 语义。
- 精确区分 P1=raw arst→synchronizer PRE（窄范围 exception 候选），P2=FF1/Q→FF2/D（保留 setup/hold），P3=FF2/Q→业务 FF/CLR（保留 recovery/removal）。

## Debug Checklist

- 检查 generated clock 时同时确认 master/source、definition point、period/edge relationship，以及是否为 auto-derived 或 user-defined。
- 分析 clock skew 时先区分 SCD、DCD、CPR，再检查公共路径分叉后的非公共 clock path 差异。
- C3 下一步在 Vivado 2018.3 的 implemented design 查询实际 rst_pipe 与 counter FF cell、counter 的 CLR pin；然后分别用 report_timing 的 max/min 检查 P3，核对 path group、route delay、slack 与 timing exception 是否生效。
- XDC selector 应核对实际匹配对象；可先 get_cells -hier 再以 get_pins -of_objects 与 REF_PIN_NAME 查特定 pin，不能仅凭预想 RTL 层次名推断约束命中。

## Common Failure Modes

- 把 BUFG 记成普通逻辑网络的“增强驱动中继器”，从而忽略其接入专用 global clock network 的架构角色。
- 用时钟频率高低直接决定 BUFG/BUFR，而忽略 clock region 覆盖需求。
- 把 clock path 中每一段累计 delay 直接等同于 skew，忽略 launch/capture 公共路径与差分到达时间。
- 在已有正确 auto-derived generated clock 的定义点重复手写约束，造成不必要的覆盖或错误模型。
- 把所有涉及亚稳态的路径都误称 recovery/removal：FF1/Q→FF2/D 仍然是 setup/hold；raw arst→FF2/PRE 才属于 async-control release 检查。
- 使用无终点约束的 set_false_path -from FF2/Q，会遮蔽从 FF2/Q 发出的 P3 reset distribution 检查；不会沿网表逆向遮蔽 FF1/Q→FF2/D。
- 将普通 RTL 功能仿真 PASS 当作复位释放亚稳态安全性证据，或把已讨论过的 reset architecture 当成已经完成 Vivado timing closure。

## References Worth Reusing

- Vivado 2018.3：report_clocks、report_clock_utilization、report_timing 可联合用于 generated clock、clock primitive/network 与 SCD/DCD/skew/CPR 的工程核查。
- Vivado 2018.3 / 7 Series：UG901（RTL inference / ASYNC_REG）、UG953（FDPE/FDCE primitive）、UG903/UG906（XDC、setup/hold 与 recovery/removal timing review）、XPM_CDC_ASYNC_RST。
