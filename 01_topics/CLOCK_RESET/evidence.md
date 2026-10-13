---
schema: topic_evidence
topic: CLOCK_RESET
mutation: APPEND_ONLY
---

# CLOCK_RESET Evidence Ledger

> Evidence 是历史事实账本，只允许在末尾追加。
>
> 新 Lesson 只追加新的 Evidence Entry，不用最新 Handoff 覆盖旧 Evidence。
> 旧解释被推翻时，追加新的 Evidence / Amendment 语义条目并引用旧 ID，不静默重写历史。

## Evidence Entries

<!-- 在这里继续追加新的 Evidence Entry。 -->

### CLOCK_RESET-EXP-001 — G1 时钟生成、Generated Clock 与 Clock Path 低辅助复测

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `CLOCK_RESET-GATE-G1`
Lesson: `CLOCK_RESET-LSN-20260925-234151`

References:
- NONE

Artifacts:
- NONE

#### Observation
Human 在真实 Vivado 2018.3 / XC7A35T 时钟工程学习后完成低辅助复测：能审查“MMCM 只是倍频器、BUFG 只是增强驱动、按频率选择 BUFG/BUFR”等错误模型，说明 MMCM/PLL 的时钟管理角色、BUFG/BUFR 的 global/regional 分发角色及 M/D/O 与 VCO/输出关系；能说明标准 MMCME2_ADV 输出通常由 Vivado auto-derived 为 generated clock、重复手写 create_generated_clock 通常无必要且可能替代自动模型，并识别普通用户逻辑产生/修改时钟等显式建模需求；能从 timing/clock utilization 识别 MMCM -> BUFG -> global clock routing -> FF/C，区分 clock delay 与 skew，并在最终 A1 CPR 题中独立得到无 CPR skew=-0.35 ns、CPR=+0.18 ns、最终 skew=-0.17 ns，说明 CPR 消除 common clock path 上 max/min 独立建模产生的虚假悲观，剩余 skew 主要来自非公共路径的有效 delay difference。

#### Interpretation
该表现直接覆盖 G1 的 C1/C2/C3，且最终 PASS Evidence 的 assistance=A1，不高于 Gate Maximum=A1，因此支持 CLOCK_RESET-GATE-G1 PASSED。该 Evidence 不证明 reset recovery/removal、metastability 传播或 reset synchronizer 物理机制已经独立掌握。

### CLOCK_RESET-EXP-002 — G2 复位释放物理模型、同步器与时序分类的学习证据

Schema: `evidence_entry`
Type: `LEARNING`
Result: `PARTIAL`
Assistance: `A2`
Gate: `CLOCK_RESET-GATE-G2`
Lesson: `CLOCK_RESET-LSN-20260927-165006`

References:
- NONE

Artifacts:
- NONE

#### Observation
Human 通过自建交叉耦合存储核心的差分电压/指数再生模型，解释了异步复位释放与时钟边沿接近时为何可能造成 FF 内部解析时间不确定；进一步独立推导 FF1 承受 release 风险、FF2 隔离第一拍的危险、两级 async-preset FF 的输出在无时钟时也可 assert。在 RTL 结构比较中准确指出只有两级均具异步控制语义的版本能实现最终输出的 async assertion，并能区分 ASYNC_REG 的同步链属性与 FF 异步预置的功能语义。对 fanout，能识别复制多个独立 raw-async synchronizer 会引入周期级释放差异，能推导 balanced registered reset tree 的共同释放及一拍延迟。C3 中能识别 raw async 输入可为窄范围 exception、同步器输出至业务 FF async-control pin 应保留 recovery/removal，但曾把 FF1/Q→FF2/D 误归为 recovery/removal，并误认从 FF2/Q 开始的 false path 会遮蔽上游 P2；经纠正后能表达按 endpoint pin 分类、STA 不模拟随机亚稳态延长。本 Lesson 没有提交 Vivado implemented-design cell/pin 查询或 P3 max/min 报告。

#### Interpretation
支持将 C1 的物理因果与同步/异步释放模型标为 VERIFIED；支持 C2、C3 已取得真实学习进展但仅标为 PARTIAL。本条属于带明显导师解释/引导的学习证据，assistance=A2、result=PARTIAL；它不证明 C2 的实际实现通过，不证明 C3 的独立约束及时序审查能力，更不能作为 G2 的低辅助 PASS Evidence。

### CLOCK_RESET-EXP-003 — Vivado 复位同步链 P2 与复位分发 P3 的真实实现/时序报告

Schema: `evidence_entry`
Type: `DEBUG`
Result: `PARTIAL`
Assistance: `A2`
Gate: `CLOCK_RESET-GATE-G2`
Lesson: `CLOCK_RESET-LSN-20261013-140247`

References:
- CLOCK_RESET-EXP-002

Artifacts:
- g2_p2_setup.rpt
- g2_p2_hold.rpt
- g2_p3_max.rpt
- g2_p3_min.rpt
- g2_summary.rpt
- g2_exceptions.rpt
- g2_fanout.rpt

#### Observation
Human 在 Vivado 2018.3 / XC7A35T-FGG484-2 中改造双时钟域复位 RTL 并执行 Implementation。首版 Counter 推导 FDRE，导致异步路径报告为空；在 Tutor 指出原因并给出修改方向后，Human 修改 RTL 并提交 16 个 FDCE Counter、16 个 CLR 引脚的查询输出。P2 报告存在 rst200_meta_reg -> rst200_sync_reg 与 rst50_meta_reg -> rst50_sync_reg 两条 FDPE/Q->D 路径，分别完成 Setup/Hold 检查；P3 报告存在 rst200_sync_reg/rst50_sync_reg 到 16 个 FDCE/CLR 的路径，属于 async_default 的 Recovery/Removal。P2 Setup：200 MHz +3.960 ns / 50 MHz +18.839 ns；Hold：+0.375 / +0.434 ns。P3 Recovery：+3.815 / +18.641 ns；Removal：+0.345 / +0.413 ns。 Human 能将 reset fanout 风险指向 Recovery/Removal 与负载引脚，但路径命令、报告分类与关键缺陷定位主要由 Tutor 提供。

#### Interpretation
证明本次工程里 P2/P3 的已报告时序路径得到实际分析，且上述 Slack 为正；支持 C2/C3 的工程进展。不能单独证明 ASYNC_REG 属性、P1/例外范围最终正确、高扇出扩展方案或 Human 独立约束审查能力。Tutor 辅助超过 Gate 最终验收上限，不能作为 PASS Evidence。

### CLOCK_RESET-EXP-004 — RTL 结构识别、控制优先级与并发行为的独立 Review 表现

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PARTIAL`
Assistance: `A0`
Gate: `CLOCK_RESET-GATE-G2`
Lesson: `CLOCK_RESET-LSN-20261013-140247`

References:
- CLOCK_RESET-EXP-003

Artifacts:
- NONE

#### Observation
Human 在不依靠逐拍事件穷举的若干 RTL Review 中，能识别 FDCE/FDPE/FDRE/FDSE 的主要复位语义、从 if(en) 的更新条件定位 tick 保持高电平的脉冲缺陷，并指出 burst 控制器的 done 仅同步清零违反停钟异步复位契约，以及最后一拍 start 无法同拍启动新事务。同时，Human 曾将同步复位 done 误认作 FDCE、误将无条件赋值视为 CE 控制、误报 else-if(!busy) 之后 beat_ok 会在空闲时消耗单位，并漏掉 abort 与 finish 同拍时 done 错误置位。Human 明确反馈机械题与反复脑内枚举学习价值低，要求训练读 RTL/推导硬件结构，之后停止继续练习并请求结课。

#### Interpretation
说明基础结构识别和性质驱动缺陷定位有实际进步，也表明对跨 always 块、非阻塞赋值及事件优先级的陌生设计 Review 尚不稳定。属于一次局部低辅助表现记录，但 result=PARTIAL；不能作为 G2 的完整低辅助综合 PASS Evidence。
