---
schema: topic_state
topic: CLOCK_RESET
status: ACTIVE
current_gate: CLOCK_RESET-GATE-G2
master_review_required: false
master_review_reason: NONE
last_lesson_id: CLOCK_RESET-LSN-20260927-165006
---

# CLOCK_RESET State

## Master Directive

Objective:
建立可独立调用的 FPGA 时钟与复位架构能力，能为真实工程设计、约束并审查时钟生成/分发与复位体系。

Reason:
当前该能力为 L2，是 baseline 最弱项之一；Generated Clock/MMCM 是 STA_XDC 的遗留 defer 项，同时是后续 CDC、LVDS 与高速数据通路学习的直接前置。

## Current Objective
能为真实设计选择并实现正确的复位架构，并对其做约束与时序审查。

## Current Snapshot

Passed:
- CLOCK_RESET-GATE-G1：时钟生成与 Generated Clock 约束——C1/C2/C3 已通过低辅助最终验收。

In Progress:
- CLOCK_RESET-GATE-G2：C1 的复位释放与亚稳态因果模型已具直接对话理解证据；C2 架构/RTL 推理有进展但缺真实实现核查；C3 静态时序/例外约束推理有进展但缺真实 timing report。

Not Yet Verified:
- G2-C2：在 Vivado 2018.3 / XC7A35T-FGG484-2 中实现并核查两级异步断言/同步释放 synchronizer，以及高 fanout reset distribution 的实际结构。
- G2-C3：在真实 implemented design 中审查 reset 路径 P1/P2/P3、recovery/removal max/min timing、route delay、slack 与 timing exceptions，并独立识别/纠正错误约束。
- G2 的低辅助最终综合验收及当前 Gate PASS Evidence 尚未完成。

## Current Blockers

- NONE

## Revalidation Flags

- NONE

## Last Lesson

Lesson ID: `CLOCK_RESET-LSN-20260927-165006`
Status: `COMPLETE`
Gate: `CLOCK_RESET-GATE-G2`

Focus:
CLOCK_RESET-GATE-G2（Reset Architecture）。先闭合 C1 的异步释放/亚稳态物理机制，推进 C2 的两级复位同步器与 fanout 分发，最后进入 C3 的 STA 路径分类、false-path 范围及真实 Vivado timing review 入口。

Work:
Human 从交叉耦合反相器的差分电压与指数再生出发，纠正了把亚稳态归因于“reset wire 被采样”的模型，理解了异步控制释放如何把 FF 内部存储节点推近 metastable point，以及 FF1/FF2 如何隔离危险第一拍。以高有效 arst、两级 async-preset reset synchronizer 为例，对比了第一/第二级是否具 async preset 的 RTL 语义，并纠正 ASYNC_REG 不是“声明异步复位 FF”的误解。讨论了同一域内复制独立 synchronizer、工具物理驱动复制与 balanced registered reset tree 的结构差别，并由 Human 推导 local reset 的释放时刻。

进入 C3 后沿 P1=raw arst→FF/PRE、P2=FF1/Q→FF2/D、P3=FF2/Q→业务 FF/CLR 分析：P1 为需精确限制的 timing exception 候选；P2 必须做 setup/hold；P3 必须保留 recovery/removal。Human 曾误将 P2 归为 recovery/removal、又误判 -from FF2/Q 会遮蔽 P2，经讨论已纠正。课程已给出真实 Vivado 2018.3 工程查询和 max/min report_timing 的下一步，但未获得这些实际输出。

Outcome:
C1 的因果模型已有 Human 自主推导与迁移表现，可记录 VERIFIED；C2 的架构/RTL 推理已经建立，但未完成实际 implemented design 验证，保留 PARTIAL；C3 的路径类型、exception scope 已有阶段性理解，仍未完成真实 timing report 与低辅助独立审查，保留 PARTIAL。没有证据表明本次已在 Vivado 中完成 implementation / timing closure；不宣布 Gate PASS。

Gate Progress:
CLOCK_RESET-GATE-G1：此前 PASSED，不修改。
CLOCK_RESET-GATE-G2：OPEN；C1=VERIFIED，C2=PARTIAL，C3=PARTIAL。Gate Maximum Assistance=A1；本 Lesson 尚无满足最终 Gate PASS 条件的低辅助综合验收。

Evidence:
CLOCK_RESET-EXP-002 — LEARNING / PARTIAL / A2；记录实际对话表现与尚未验证的工程边界，不作为 Gate PASS Evidence。

Suggested Local Next:
下次直接承接 G2-C3，不重复 C1 选择题或 primitive 猜测。Human 在 Vivado 2018.3 / XC7A35T-FGG484-2 对最小两级 async-preset synchronizer + async-clear 8-bit counter 实施 Implement Design；提交 (1) rst_pipe/counter 实际 cell 查询，(2) counter CLR pin 查询，(3) FF2/Q→counter[*]/CLR 的 max/recovery 与 min/removal 完整 path summary + data path，并核对 timing exception 是否遮蔽 P3。先以真实结果补足 C3 和 C2 的 implementation Evidence，之后再做不泄露答案、Assistance≤A1 的 Gate 综合复测。依赖式 reset sequencing/reset controller 暂缓到 C3 闭合后。

## Evidence Anchors

- CLOCK_RESET-EXP-001
- CLOCK_RESET-EXP-002

## Open Questions / Deferred

- C3 实际实现中 FF2/Q → counter[*]/CLR 的 recovery/removal 报告如何显示，是否存在 exception 遮蔽或约束对象选空的情况？
- 待 C3 闭合后再处理 reset sequencing / reset controller：locked、init_done、ready 等依赖的有序释放和故障后的重新断言。
