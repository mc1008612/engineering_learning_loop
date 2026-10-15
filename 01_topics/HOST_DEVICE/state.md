---
schema: topic_state
topic: HOST_DEVICE
status: ACTIVE
current_gate: HOST_DEVICE-GATE-G1
master_review_required: false
master_review_reason: NONE
last_lesson_id: HOST_DEVICE-LSN-20261013-233205
---

# HOST_DEVICE State

## Master Directive

Objective:
实现从合成采样数据、设备协议到 Python Host 的可复现端到端数据链路，逐步进入连续流和真实采集。

Reason:
Host–Device Communication 当前 L0；已有 Verilog/STA/Python 实践基础。优先通过可运行的项目组合已学能力，降低反复在单点 Gate 打转的成本。

## Current Objective
G1（**最小可用范围**）：完成 Packet V1 契约的**独立审签**、**独立推导并复核 golden vectors**、以及**独立设计并判读**必要故障测试。代码实现可采用 AI 协作，但规格、向量与正确性判定由 Human 持有。

## Current Snapshot

Passed:
- NONE

In Progress:
- HOST_DEVICE-GATE-G1 保持 OPEN；已具备 Packet V1 规格候选、可运行 Python 解析器、10 组冻结 golden 帧与 12 类场景，26/26 软件测试通过；无 FPGA 实机证据。
- G1 独立性口径已由 Master 正式修订为「独立掌握正确性」（审签规格 / 独立推导并复核 golden vectors / 独立设计并判读故障测试），不再要求 Human 亲手编写 parser 代码；剩余验收为一次有界收尾会话。

Not Yet Verified:
- C1：Human 尚未完成规格的独立审签（当前为引导下审查），保持 PARTIAL。
- C2：Human 尚未独立推导并复核 golden vectors，也未给出 parser 关键分支自己的正确性论证与失败判据，保持 PARTIAL。
- C3：Human 尚未独立设计并判读必要故障测试（现有 26 项由 AI 编写执行），保持 PARTIAL。
- 真实板卡 / FPGA RTL / USB-UART 实机回环未实现或验证；不作为 G1 的前置验收。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `HOST_DEVICE-LSN-20261013-233205`
Status: `COMPLETE`
Gate: `HOST_DEVICE-GATE-G1`

Focus:
HOST_DEVICE-GATE-G1（Packet V1 与 Python Reference Client）。以最小可用范围讨论设备→Host 的字节流分帧、完整性检查、序号、重同步及可复现参考实现；课程结束时由 Human 主动请求 Close。

Work:
- Human 参与了协议取舍：SYNC=B5 62、VERSION=01、8-bit SEQ、LEN 为 2..32 偶数的载荷字节数、1..16 个有符号 int16 小端样本、CRC-16/IBM-3740；CRC 覆盖 VERSION/SEQ/LEN/PAYLOAD，CRC 小端传输。
- 定稿候选恢复策略：只有初始及失同步后需要两条紧邻、合法且 SEQ 连续的候选帧建立同步；确认成功后两帧均交付；已同步时单条 CRC 正确的完整帧立即交付。普通 read() 空结果不表示 EOF；仅由 Host 主动关闭调用 finish()，不增加 N 次超时退出、孤立末帧超时放行、ACK、重传或独立会话协议。
- Human 明确最小实机工程应采用 PC GUI 合成原始 int16 小端字节 → FPGA UART RX/拼接/16 样本分组 → Packet V1 封包/UART TX → 同一 PC GUI 解析。UART 物理链路双向，但 Packet V1 只用于 FPGA→PC；当前不检查 PC 发出的每个采样是否与返回值逐项一致。
- Tutor/AI 编写 Python reference_client、独立 golden vectors、协议候选规格、故障测试和报告；最终可复现软件审查包 `packet_v1_g1_final_review_20261015.zip`。自动化软件测试 26/26 通过，冻结帧向量 10 组、流/故障场景 12 组。独立小端示例 SEQ=7、sample=0x1234 的期望完整帧为 `B5 62 01 07 02 34 12 32 7F`（CRC=0x7F32）；未实施 FPGA RTL、GUI 实机、USB-UART 硬件验证。
- Human 解释并质询 13/14 在双帧恢复后都会交付，追问 sync_lost 与实际丢帧的区别；理解 8-bit SEQ 回绕不能准确计算丢帧数、CRC 与序号统计可能描述同一次异常；质疑冗余会话/超时设计，提出合理的系统简化取舍。Tutor 对术语 Golden Reference 做了迟到的解释，Human 指出双端同错时单看往返数值可仍一致。
- 故障审查说明：CRC 在 FPGA 封包之前发生输入错误时无法保证原始采样正确；合法长度的假头可延误有限流恢复；嵌套的两条合法伪帧也可能诱发误同步。明确这些是参考协议已知边界，不冒充已修复问题。
- Human 自主决定结束本 Lesson，明确不希望为 G1 继续增加重复的判断题、会话协议、ACK 或额外非前置硬件工作。

Outcome:
已形成可复现的 Packet V1 **软件候选契约和参考测试材料**，并记录真实的业务设计判断、故障理解和已知限制。Lesson COMPLETE；未将软件自测等同于 Human 原始独立验收。保留原始 OSI 七层表格及 FIFO/UART/SEQ/会话/Golden Reference 的项目实例于 Notes Delta。

Gate Progress:
- C1=PARTIAL：书面规格及当前/未来链路带宽区别齐备，但未留下符合原 Gate 独立性口径的完整 Human 最终审签。
- C2=PARTIAL：可运行 Python Parser、冻结独立 golden vectors 和复现方法已存在，但核心代码由 AI（A3）编写，不满足 C2「Human 独立实现」及 Gate Assistance≤A1 的要求。
- C3=PARTIAL：AI 已执行短帧、截断、垃圾、bit flip、丢字节/整帧、重启/回绕、随机读取分块及伪帧等 26 项软件测试；Human 有故障统计及边界的部分理解表现，但缺独立设计和执行测试的低辅助 Evidence。
- Resulting Gate：HOST_DEVICE-GATE-G1 仍 OPEN，不请求 PASSED 或能力等级提升。

Evidence:
新增 HOST_DEVICE-EXP-001、HOST_DEVICE-EXP-002、HOST_DEVICE-EXP-003 三条 PARTIAL Evidence，分别记录 Human 架构/业务判断、Human 故障统计判断与 AI 软件自测。没有满足 Gate Assistance≤A1 的最终 PASS Evidence；没有 HARDWARE_VERIFIED 证据。

Suggested Local Next:
优先由 Master Review 处理 C2 原始「Human 独立编码、A1」与 Human 当前「AI 写代码、本人审业务逻辑」方式的冲突，并决定保持原 Gate 验收或正式修改能力目标和评估方式；Tutor 不擅自改写原 Gate 标准。下一阶段若进入硬件链路，先核实实际板卡 UART 管脚/USB-UART 桥接器/电平及单 COM 口双向访问，再开展 FPGA UART RX/TX RTL 仿真和实机 PC→FPGA→PC 回环。G1 不以实机、GUI、性能/背压优化为前置条件。

## Evidence Anchors

- HOST_DEVICE-EXP-001
- HOST_DEVICE-EXP-002
- HOST_DEVICE-EXP-003

## Open Questions / Deferred

- 已解决（原 Master Review 问题，2026-10-15）：G1 的独立性口径正式修订为「独立掌握正确性」——独立审签规格、独立推导并复核 golden vectors、独立设计并判读故障测试。**不降低**独立工程判断要求，只是把「独立」的落点从"亲手写代码"移到"独立定义正确性 / 判读故障 / 说明边界"。
- 非 Gate 早期确认项（G2 前置，不阻塞 G1）：实际开发板型号、UART 引脚、USB-UART 桥接器、电平，以及单个 COM 口的双向访问能力。
- V1 不扩展：PC→FPGA 为无分帧原始 int16 流，输入侧丢字节/错误无法由输出 Packet V1 CRC 反推；留待 G2/G3 或显式 V2 讨论。真实回环如何上报输入 RX 丢字节与 FIFO 溢出一并留待该阶段决定。
