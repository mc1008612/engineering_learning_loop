---
schema: topic_state
topic: HOST_DEVICE
status: ACTIVE
current_gate: HOST_DEVICE-GATE-G1
master_review_required: false
master_review_reason: NONE
last_lesson_id: NONE
---

# HOST_DEVICE State

## Master Directive

Objective:
实现从合成采样数据、设备协议到 Python Host 的可复现端到端数据链路，逐步进入连续流和真实采集。

Reason:
Host–Device Communication 当前 L0；已有 Verilog/STA/Python 实践基础。优先通过可运行的项目组合已学能力，降低反复在单点 Gate 打转的成本。

## Current Objective
G1（**最小可用范围**）：制定 Packet V1 协议契约，并由 Human 独立完成 Python 字节流解析、必要的错误检测/重同步与 golden-vector 验收。只做最小可用协议，不追求完整协议功能。

## Current Snapshot

Passed:
- NONE

In Progress:
- HOST_DEVICE-GATE-G1 OPEN；优先完成协议契约和 Host Reference Client 的第一个可执行结果。

Not Yet Verified:
- C1 协议规格、C2 解析与重同步、C3 错误注入/独立判读均尚无本 Topic Evidence。

## Current Blockers
- NONE

## Revalidation Flags
- NONE

## Last Lesson

Lesson ID: `NONE`
Status: `NONE`
Gate: `HOST_DEVICE-GATE-G1`

Focus:
NONE

Work:
NONE

Outcome:
NONE

Gate Progress:
NONE

Evidence:
NONE

Suggested Local Next:
在真实工作项目中选择 Protocol V1 的最小帧格式并输出第一个可复现解析测试；由 Human 主导工程判断。

## Evidence Anchors
- NONE

## Open Questions / Deferred
- 真实 FPGA 板卡、USB-UART/其他物理连接和目标 ADC 采样参数尚未确认；G1 不以假设实机硬件存在为前提。
- 进入 G2 实机前，检查是否有可用物理链路；无硬件则将仿真结果标为 SIM_VALIDATED，不声称 HARDWARE_VERIFIED。
- **G1 范围边界（防止局部最优）**：仅做最小可用协议、可复现解析器、必要错误恢复；不做完整命令/响应协议与多版本兼容（属 S1）、不做性能/吞吐优化、不做连续流与背压（属 G3）。
- **早期环境确认（非前置 Gate）**：G1 期间尽早确认实际 FPGA 板卡型号与可用 Host 物理链路（USB-UART/其它），作为真实观察记录供 G2 选型。该确认不构成独立 Gate，也不阻塞 G1。
