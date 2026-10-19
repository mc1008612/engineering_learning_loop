---
schema: master_outline
current_topic: HOST_DEVICE
current_action: TUTOR
master_checkpoint: HOST_DEVICE-GATE-G2
---

# Master Outline

## Purpose

长期能力路线与当前全局学习焦点。它不是按天/按周的课程表，也不记录 Lesson 历史。

## Routing Fields

当前全局路由事实只保存在本文件 frontmatter：

- `current_topic`；
- `current_action`；
- `master_checkpoint`。

不要在正文重复维护第二份 Current Learning Focus。Tutor Context 会把这些 frontmatter 与当前 Topic `state.md / Master Directive` 动态组合成人类可读的当前学习焦点。

Base Repo 初始没有 Live Topic；第一次运行由 Master 根据能力基线、依赖、长期目标与 Human 当次偏好提出首个 Topic 计划。

## Long-Term Direction

长期目标：高速数据采集 / FPGA + 板级硬件 + Host 链路的系统工程能力。

### A. FPGA Implementation

#### A1. STA / XDC
同步时序模型、Timing Path、Setup/Hold、Clock/I/O Constraints、Exceptions、Timing Closure。

#### A2. Clock / Reset
Clock tree、MMCM/PLL、Generated Clock、reset architecture、async assert / sync deassert。

#### A3. CDC
Synchronizer、pulse/toggle/handshake、multi-bit transfer、async FIFO、CDC report/constraints。

### B. Host–Device System

#### B1. Device Protocol
Byte stream vs packet、framing、length、sequence、CRC、resync、command/response/stream、timeout/error recovery。

#### B2. Host Communication Architecture
Blocking I/O、queue/buffer、resource lifecycle、LabVIEW VISA、Python reference client。

### C. Data Path / Buffer
Producer/consumer、throughput/latency、FIFO depth、overflow/underflow、backpressure、width conversion、packetization。

### D. High-Speed I/O
Source-synchronous LVDS、SDR/DDR、IDDR/ISERDES/IDELAY、skew、sampling window、I/O timing、hardware debug。

### E. Measurement / DSP
Sampling、aliasing、DFT/FFT、window/leakage、RMS/dBFS、SNR/THD/SINAD/SFDR/ENOB、后续 FIR/IIR。

### F. Memory / DDR
Bandwidth/latency、burst、AXI memory-mapped、MIG、DDR buffering。

### G. Ethernet
MAC/Ethernet/ARP/IPv4/UDP、MTU、loss、socket buffer、transport replacement。

### H. PCIe / DMA / Linux
Topology、Config Space、BAR/MMIO、TLP、DMA、descriptor、interrupt、host memory、driver/mmap/ioctl。

### I. C++ / Qt
Modern C++、RAII、threading、Qt event loop/signal-slot/thread affinity、重写同一 Host protocol。

### J. Cross-cutting：RTL Reading / Design Review
将陌生 RTL 的状态/下一状态、组合逻辑、时钟与复位域、控制优先级、不变量与最小反例分析嵌入每个真实工程 Gate；不新增专门刷题 Gate。先由 Human 选择检查目标，再借助仿真、综合网表、Timing/CDC 报告；报告 MET 不自动等于具备独立工程判断。该能力贯穿多个 Topic，不单独设 Gate 或 Topic。

## Project-anchored milestones (候选计划；Gate 是唯一状态来源)

North Star：能独立设计、实现、调试、度量一条从可重复采样源到 Host 的端到端数据链路，能够区分协议正确、实现可复现、板上真实运行与目标性能达标。

- **Demo Profile**：先以 ramp/PRBS 产生可核对的样本；采样率应适配已有链路，不把低速接口误当高速最终方案。
- **Target Profile**：实际 ADC 型号、采样通道数、采样率、位宽、外设物理接口与最大允许丢样率仍为 `TBD`；拿到板卡约束和指标后再决定 LVDS、DDR、Ethernet/PCIe 路线。

| 里程碑 | Owner Gate（当前唯一验收者） | 完成定义 | 可能影响的能力 |
|---|---|---|---|
| M0 Packet Contract + Host Reference | `HOST_DEVICE-GATE-G1` | Protocol V1、Python parser、golden vectors、故障注入，Human 可低辅助解释错误恢复 | Host–Device Communication / Python Engineering / RTL Review 方法迁移 |
| M1 FPGA→Host Demo | `HOST_DEVICE-GATE-G2` | 板上现有链路发送可预测合成采样，Host 复原并对照，不把仿真冒充实机 | Host–Device / Verilog RTL / FPGA Debug |
| M2 Reliable Streaming | `HOST_DEVICE-GATE-G3` | 连续流丢样/重同步/背压边界与测量报告；不隐含复杂 CDC 已验证 | Host–Device / Data Path / Python Engineering |
| M3 多时钟采样集成（待规划） | 后续 `CDC` Topic 的 Gate，由 Master 在具备平台条件时建立 | CDC/FIFO/Reset 边界的独立可复现验证 | CDC / Clock Reset / STA |
| M4 真实 ADC/性能扩展（待规划） | 按真实平台选取后续 Topic/Gate | 实际测量指标/数据率触发相关模块学习 | LVDS / DSP / DDR / DMA 等 |

各行只是 **稳定的目标和能力候选**，不是当前 Gate 状态或 Ability 等级。实时 `OPEN/PASSED` 以各 Topic `gates.md` 为准；Ability 仅由 Master 基于真实 Evidence 审批升级。一个 Lesson 的 Evidence 不可跨 Topic 自动变成多个 Gate 的 PASS。

### 技术触发条件（何时才需要进入该方向）

以下只定义"进入条件"，不是当前计划，也不代表已具备前置能力。所有数值（采样率、带宽、缓冲容量、丢样率）在拿到真实 ADC 型号与板卡约束前保持 `TBD`，由 Master 依据实测数据填写，不预先编造阈值。

- **DDR / 缓冲**：当「采样率 × 位宽 × 可接受缓冲时长」超过片上可用 RAM/BRAM 容量时进入；前置为 Data Path/Buffer 与 Memory 基础；交付物为带宽/延迟预算、缓冲方案与实测吞吐。
- **PCIe / DMA**：当现有物理链路（USB-UART / Ethernet）的实测吞吐或延迟成为端到端瓶颈，且需要更低 CPU 开销或更高确定性时进入；前置为 Ethernet 或 Host 通信架构与 Linux Driver 基础；交付物为描述符/中断闭环与实测带宽。
- **LVDS / 源同步**：当接入的真实 ADC 接口本身即为源同步或高速串行时进入；前置为 STA 的 I/O 约束能力与 SelectIO/ISERDES；交付物为采样窗口与 I/O 时序验证。
- **Ethernet**：当需求要求网络化传输、远距离链路或多 Host 接入时进入；前置为 Device Protocol 完成；交付物为可复现的网络传输链路。
- **DSP / 测量**：当需要给出 SNR/THD/SFDR/ENOB 等指标，或采样链路频域行为成为设计约束时进入；前置为 Measurement/DSP 基础。

## Scheduling Rule

只在以下情况重新排课：

- Master Checkpoint 达成；
- `master_review_required=true`；
- 没有合法 Current Topic；
- Revalidation/regression 需要全局决策；
- Human 明确要求调整当前 Long-Term Direction 内的 Topic 顺序/阶段性重点。

仅仅“今天不想学当前 Topic”属于 session-local 暂缓，不自动修改长期路线。完全替换学习领域不属于当前版本的普通 Master Review 事务。

Master 决定“下一步学什么”；Tutor 负责阶段内局部教学。
