---
schema: topic_gates
topic: HOST_DEVICE
topic_completion_rule: ALL_MANDATORY_GATES_PASSED_AND_MASTER_CONFIRMED
---

# HOST_DEVICE Gates

## HOST_DEVICE-GATE-G1 — Packet V1 与 Python Reference Client

Status: `PASSED`
Mandatory: `YES`

### Objective
以**最小可用范围**独立设计并检验一份设备→Host 参考协议：完成分帧、序号、必要的错误检测与重新同步，产出一份可复现的 Python 解析器与 golden reference，供后续 FPGA 实机链路复用。本 Gate 不追求完整协议功能，只要求最小可用闭环。

### Prerequisites
- 已有 Python 基础；不要求先关闭 CLOCK_RESET-GATE-G2。

### Mandatory Criteria
- C1 — 书面定义并**独立审签** frame boundary、version、length、sequence、payload、CRC/checksum、异常帧与重新同步原则；说明现有物理链路与未来目标带宽的区别，并指出规格中**已知边界与被有意接受的取舍**。
- C2 — **独立掌握参考实现的正确性**：独立推导并复核 golden vectors（含手工构造帧与 CRC 计算），并对 parser 的关键分支（任意分块、同步/失同步、SEQ 回绕）给出**自己的正确性论证与失败判据**。实现代码可由 AI 协作产出，但规格、向量与判定责任由 Human 持有。
- C3 — 能**独立设计并判读**必要故障测试（短帧、截断、插入垃圾字节、bit flip、丢字节/整帧、重启/回绕、伪帧），解释错误统计口径（`bad_crc` / `sync_lost` / `sync_acquired` / `sequence_discontinuities` **不可相加**）以及未覆盖边界与验证等级。

### Stretch Criteria
- S1 — 支持简单命令/响应与协议版本不兼容处理。

### Allowed Assistance
Maximum: `A1`

### Required Evidence
- `protocol/PROTOCOL_V1.md`（Human 独立审签）、Human **独立推导并复核**的 golden vectors、故障测试与判读报告；`host/reference_client.py` 可由 AI 协作实现，但规格、向量与正确性判定由 Human 持有并说明设计取舍。
- 范围边界：不包含完整命令/响应协议与多版本兼容（属 S1）、性能/吞吐优化、连续流与背压（属 G3）；FPGA 实机链路确认不作为本 Gate 的前置条件。
- 至少一条直接观察能力表现的 Evidence。
- 若要求独立性，最终验收 Evidence 的 Assistance 不得高于 Gate 上限。
- “讲过 / 看懂 / 跟着做完”不能单独支撑 PASS。

### Pass Rule
Mandatory Criteria 全部满足 + 至少一条当前 Gate 的 `PASS` Evidence + Assistance 不高于 Maximum，才可 `PASSED`。

### Criterion Progress

- C1: `VERIFIED`
- C2: `VERIFIED`
- C3: `VERIFIED`

### Evidence References

- HOST_DEVICE-EXP-001
- HOST_DEVICE-EXP-002
- HOST_DEVICE-EXP-003
- HOST_DEVICE-EXP-004
- HOST_DEVICE-EXP-005
- HOST_DEVICE-EXP-006
- HOST_DEVICE-EXP-007
- HOST_DEVICE-EXP-008

## HOST_DEVICE-GATE-G2 — FPGA→Host 最小实机数据闭环

Status: `OPEN`
Mandatory: `YES`

### Objective
将 FPGA 合成样本通过**板上确实存在且可用**的物理数据链路传到 Python Host，复原序号、内容并明确带宽与边界。

### Prerequisites
- HOST_DEVICE-GATE-G1 `PASSED`。
- Master 已知目标平台为 Vivado 2018.3 / XC7A35T-FGG484-2；取得实机 Evidence 前必须在本 Gate 首个 Lesson 确认实际开发板型号、UART TX/RX 引脚、USB-UART 桥接器、电平/共地与同一 COM 口双向访问。未确认前只允许 RTL/TB 仿真与 Host 离线验证。

### Mandatory Criteria
- C1 — FPGA 可重复输出 ramp/PRBS 样本；RTL/TB 与实际发送格式遵守 Packet V1 契约。
- C2 — 在真实设备链路上用 Host 解析实际帧，给出端到端样本一致性与计数统计；模拟/实现/硬件证据明确区分。
- C3 — 人工制造至少一种链路/恢复异常，Human 能独立定位最小故障域，并解释实际吞吐、丢样与未验证的时序/复位边界。

### Stretch Criteria
- S1 — 可复现重置设备后的 Host 重同步过程。

### Allowed Assistance
Maximum: `A1`

### Required Evidence
- 可定位的 FPGA RTL/TB/约束、Host CLI 与真实设备运行日志；未跑过的实机结果不得声称通过 C2。
- 与最终 Criteria 相符的低辅助 PASS Evidence；严禁用“代码存在/看过演示”代替实机观察。

### Pass Rule
Mandatory Criteria 全部满足 + 至少一条当前 Gate 的 `PASS` Evidence + Assistance 不高于 Maximum，才可 `PASSED`。

### Criterion Progress
- C1: `NOT_VERIFIED`
- C2: `NOT_VERIFIED`
- C3: `NOT_VERIFIED`

### Evidence References
- NONE

## HOST_DEVICE-GATE-G3 — 连续流与故障恢复

Status: `DRAFT`
Mandatory: `YES`

### Objective
在已有 FPGA→Host 数据链上量化持续传输、缓冲与错误恢复的边界，为未来跨域 FIFO 和高速物理接口提供真实瓶颈。

### Prerequisites
- HOST_DEVICE-GATE-G2 `PASSED`。

### Mandatory Criteria
- C1 — 为持续流建立数据率、缓存、帧头/有效载荷开销预算，给出来源与边界。
- C2 — 在 Host 阻塞、突发输入或丢包时能记录并定位缺失，说明不可暂停采样源的 overflow/数据丢失策略。
- C3 — 提供可复现的端到端性能/故障注入对照报告，Human 能解释下一次架构升级应该针对哪个瓶颈。

### Stretch Criteria
- S1 — 给出但不冒充实现验证的多时钟 FIFO/CDC 集成需求清单。

### Allowed Assistance
Maximum: `A1`

### Required Evidence
- 连续流日志、golden samples、误包/丢样/吞吐指标与分析脚本；标明所使用的真实硬件。
- 本 Gate 的低辅助独立诊断 Evidence。

### Pass Rule
Mandatory Criteria 全部满足 + 至少一条当前 Gate 的 `PASS` Evidence + Assistance 不高于 Maximum，才可 `PASSED`。

### Criterion Progress
- C1: `NOT_VERIFIED`
- C2: `NOT_VERIFIED`
- C3: `NOT_VERIFIED`

### Evidence References
- NONE
