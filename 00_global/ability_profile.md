---
schema: ability_profile
scale: L0-L6
source: initial_self_report_baseline
last_master_review: 2026-09-22
---

# Ability Profile

## Level Semantics

- `L0`：尚未形成稳定可调用能力。
- `L1`：能解释/识别基本问题，独立执行不足。
- `L2`：能在示例、文档或明显提示下完成标准任务。
- `L3`：能独立完成熟悉范围内标准工程任务。
- `L4`：条件变化或故障时能独立定位、修复并完成变式任务。
- `L5`：能迁移到陌生系统并做架构取舍。
- `L6`：能审查复杂系统、形成方法论并稳定指导他人。

只允许严格单值 `L0..L6`。不使用范围、半级、置信度或 capability dimensions。

## Current Baseline

| Ability | Level | Baseline note |
|---|---:|---|
| Verilog RTL / FSM | L3 | UART/FSM 等中小 RTL 可独立完成 |
| Verilog TB / Functional Simulation | L3 | 能写 TB、做 Vivado 功能仿真 |
| STA / XDC | L2 | 路径模型与 Timing Report 阅读已验证（STA_XDC-EXP-001/002）；XDC 约束编写与 timing closure 尚未建立（G2/G3） |
| Clock / Reset | L1 | 接触多时钟；reset architecture 薄弱 |
| CDC | L2 | 双触发器/async FIFO 可用；系统化 CDC 分析不足 |
| AXI / IP Integration | L2 | XDMA/MIG/SmartConnect 功能仿真经历；缺硬件闭环 |
| FPGA Debug / ILA | L2 | 用过 ILA；独立配置/debug strategy 不稳定 |
| Source-Synchronous LVDS / SelectIO | L1 | 做过 8-lane 300 MHz 设计但未硬件闭环；ISERDES 未掌握 |
| Board Power / PCB | L3 | 6 层板、电源、DCDC/LDO/上电验证、高速差分布局 |
| Python Engineering | L3 | ROS、threading/asyncio/queue 有实践；完整设备 GUI 不足 |
| C / Build Tooling | L2 | C、Make/CMake/Git 基础可用；无大型系统级 C 工程 |
| LabVIEW Architecture | L2 | Event/Queue/State/SubVI 基础；无真设备闭环 |
| Host–Device Communication | L0 | 尚未完成真实设备协议/连续流闭环 |
| Measurement / DSP | L1 | 学过但碎片化，需要重建 FFT/ADC 指标体系 |
| Linux Driver / DMA | L0 | 尚无真实实践 |
| C++ / Qt | L0 | 尚未系统学习 |

这些是初始 baseline，不是假装已经被新鲜 Evidence 严格验证的结论。
