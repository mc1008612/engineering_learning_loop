---
schema: topic_state
topic: HOST_DEVICE
status: ACTIVE
current_gate: HOST_DEVICE-GATE-G2
master_review_required: false
master_review_reason: NONE
last_lesson_id: HOST_DEVICE-LSN-20261017-110156
---

# HOST_DEVICE State

## Master Directive

Objective:
实现从合成采样数据、设备协议到 Python Host 的可复现端到端数据链路，逐步进入连续流和真实采集。

Reason:
Host–Device Communication 当前 L1（G1 软件契约已由 A1/PASS 证据支撑，实机链路未验证）；已有 Verilog/STA/Python 实践基础。优先通过可运行的项目组合已学能力，降低反复在单点 Gate 打转的成本。

## Current Objective
G2（**最小实机闭环**）：在确认可用的板载物理链路后，将 FPGA 合成 ramp/PRBS 样本按 Packet V1 从 UART 发送到 Python Host。首个 Lesson 先完成实际开发板/UART 物理链路确认，以及 UART RX/TX RTL 与功能仿真；未取得真实板卡运行证据前不声称实机通过。

## Current Snapshot

Passed:
- HOST_DEVICE-GATE-G1：C1/C2/C3 VERIFIED，依据 Human A1 独立判断与软件参考材料 PASSED；仅 SOFTWARE_ONLY，不代表 FPGA 实机完成。

In Progress:
- HOST_DEVICE-GATE-G2 已 OPEN：首个 Lesson 确认真实开发板型号、UART TX/RX 引脚、USB-UART 桥接器/电平/共地、单 COM 口双向访问；随后实现并仿真 UART RX/TX 与 16 个 int16 分组/Packet V1 封包。

Not Yet Verified:
- FPGA UART RX/TX RTL 功能仿真、板上引脚/USB-UART 物理连线、PC→FPGA→PC 实机回环与连续稳定性均未完成。
- 未来目标采样率、真实带宽与背压/FIFO 溢出边界未验证；G1 的 115200 baud、每 20 ms/16 样本仅为理论可行性预算。
- Packet V1 不保证 PC→FPGA 输入字节完整性、不保证零丢失，亦不保证不存在载荷内合法伪帧诱发的误同步。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `HOST_DEVICE-LSN-20261017-110156`
Status: `COMPLETE`
Gate: `HOST_DEVICE-GATE-G1`

Focus:
HOST_DEVICE-GATE-G1（Packet V1 与 Python Reference Client）的有界验收收尾；检验 Human 对协议审签、Golden Vectors、Parser 行为和故障判读的独立正确性责任。课程采用 PROJECT 模式，遵守已冻结的最小范围。

Work:
- Human 首次提交 Packet V1 书面审查意见，覆盖 `B5 62` 同步字、`VERSION=01`、8-bit SEQ、载荷长度、signed int16 小端、CRC-16/IBM-3740，以及双帧确认、不使用 ACK/重传/会话的业务理由。经教学纠正后，明确：LEN 仅取 2..32 的偶数，CRC 的 init 为 `FFFF`；已同步时 CRC 合法的 SEQ 跳号帧仍交付。
- Human 主动追问 CRC 计算机制、CRC-8 与 CRC-16、模二除法、初值、突发错误、补码和 Packet V1 帧开销。Tutor 讲解并先后示范相关例子；这些示范属于受指导学习，不作为独立计算证据。
- Human 独立提交新 Golden Vector：`SEQ=00`，样本 `0x1234,-1`，完整帧 `B5 62 01 00 04 34 12 FF FF BD 16`；与 CRC-16/IBM-3740（init=`FFFF`、CRC 计算值 `0x16BD`、CRC 小端 `BD 16`）相符。更早的 `SEQ=FF` 练习曾错用 init=`0000`，经 Tutor 纠正；不得把纠正前练习记为独立通过。
- Human 自主提出 Buffer 累积、按字节搜索、完整帧候选和已同步快速路径，并指出 `read()` 为空不构成失同步、读取分块不等于帧边界。Tutor 说明 `feed(bytes)` 是建议的 Parser 接口而非 pySerial 内置 API，纠正了未同步时首帧不能立即交付、一次调用可返回多帧等问题。
- Human 独立设计五类故障测试：A 的 Header 破坏；A 中插入垃圾字节；载荷内合法子帧/伪帧；分别破坏 A 或 B 的双帧建同步；已同步后破坏 C 的 LEN。Tutor 报告编写并运行新增 13 项注入测试，在当时参考实现上与既有 19 项合计报告 32/32 PASS；这是 Tutor 的 SOFTWARE_ONLY 测试结果，未在本次收课时取得源码重新执行，也非 Human 独立执行。
- 在外层 CRC 失败而内部存在连续合法子帧的反例后，Human 继续批准最小连续监测用途、接受误同步风险，不追加转义或第三帧确认。Tutor 纠正了“最多误交付两帧”“外层坏 CRC 必然立即再次失同步”的不可保证断言；Human 的风险接受决策保留，概率未量化。
- 最终综合黑盒验收：输入 SEQ `10,11,15,16,17,18`，仅 16 CRC 损坏；Human 独立回答交付 `10,11,15,17,18`，`bad_crc=1`、`sync_lost=1`、`sync_acquired=2`、`sequence_discontinuities=2`，并解释 CRC 合法的 15 跳号应交付、不能失同步。全部符合本课约定的 Parser 行为。Tutor 指出重同步在 Python Parser 中为按 **Byte** 而非按 Bit 搜索。

Outcome:
本 Lesson 由 Human 明确要求收课，状态 COMPLETE。Tutor 根据本次独立书面规格/风险审签、独立正确 Golden Vector、独立故障设计以及无提示综合统计判读，判断 G1 的 C1/C2/C3 达到 VERIFIED，提交 Gate `PASSED` 请求。代码允许 AI 协作，但没有把 AI 写码或自动测试等同于 Human 独立能力。此结论只覆盖 Packet V1 软件契约与参考 Parser 的正确性，不代表 FPGA、USB-UART 实机回环或未来吞吐已经验证。

Gate Progress:
- C1 = VERIFIED：Human 对最小协议、适用业务、CRC/同步规则及已知风险作出了最终工程审签。教学中曾纠正参数与异常行为；最终独立裁决与取舍有可观察证据。
- C2 = VERIFIED：Human 独立提交并核对 `SEQ=00` 的完整 Golden Vector，并在先前独立构思 Buffer/Parser 设计的基础上，于综合场景正确判断 CRC、SEQ 与双帧交付行为。Human 未独立重写/逐行审核 Python Parser；Gate 明文允许 AI 协作实现。
- C3 = VERIFIED：Human 独立提出五组故障注入思路，并正确判读最终故障事件下的全部交付序号与四种统计，能区分 CRC 损坏与 SEQ 跳号，接受有条件且未量化的伪帧风险。
- S1 未实施；属于 Stretch，不阻塞 G1。G1 验证等级为 SOFTWARE_ONLY；真实 FPGA RTL、GUI、连续流和背压等仍属后续工作。

Evidence:
新增 `HOST_DEVICE-EXP-004` 至 `HOST_DEVICE-EXP-008`。其中独立判定相关记录为 A1 / PASS；Tutor 讲解及软件实现/测试另用 A2/A3 / PARTIAL 记录，避免混淆来源和独立性。原历史 `HOST_DEVICE-EXP-001..003` 保留。本次 Gate PASSED 请求由 A1 / PASS Evidence 支撑。

Suggested Local Next:
由 Master Review 审阅新 G1 PASS 证据是否影响 Host–Device Communication 能力评价，并决定下一 Gate 规划；Tutor 不擅自修改 Ability Profile 或 Topic current_gate。后续最小 PC→FPGA→PC 硬件闭环先确认真实开发板/USB-UART 芯片、管脚、电平、共地、单 COM 双向能力，再验证 UART RX/TX RTL、16 个 int16 分组封装与 Python Host 接收。平台为 Vivado 2018.3 / XC7A35T-FGG484-2；不要把 FPGA 实机作为已完成或 G1 的补验要求。

## Evidence Anchors

- HOST_DEVICE-EXP-001
- HOST_DEVICE-EXP-002
- HOST_DEVICE-EXP-003
- HOST_DEVICE-EXP-004
- HOST_DEVICE-EXP-005
- HOST_DEVICE-EXP-006
- HOST_DEVICE-EXP-007
- HOST_DEVICE-EXP-008

## Open Questions / Deferred

- 后续实机阶段：确认开发板 UART TX/RX 对应管脚、USB-UART 桥接器、电平、共地与同一 COM 口双向使用条件。
- 未来若目标从可容许少量丢帧的连续监测改为可靠交付或高吞吐，再重新评估协议/流控与防伪帧风险。
