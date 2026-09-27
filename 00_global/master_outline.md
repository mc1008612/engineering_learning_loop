---
schema: master_outline
current_topic: CLOCK_RESET
current_action: TUTOR
master_checkpoint: CLOCK_RESET-GATE-G2
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

## Scheduling Rule

只在以下情况重新排课：

- Master Checkpoint 达成；
- `master_review_required=true`；
- 没有合法 Current Topic；
- Revalidation/regression 需要全局决策；
- Human 明确要求调整当前 Long-Term Direction 内的 Topic 顺序/阶段性重点。

仅仅“今天不想学当前 Topic”属于 session-local 暂缓，不自动修改长期路线。完全替换学习领域不属于当前版本的普通 Master Review 事务。

Master 决定“下一步学什么”；Tutor 负责阶段内局部教学。
