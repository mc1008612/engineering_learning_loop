# Project-first Gate Workflow (兼容性扩展)

本流程**不增加任何新的持久化实体、状态枚举、Evidence 类型或自动能力分数**。系统项目是规划/教学视角；长期事实仍由 Topic、Gate、Evidence、State、Notes、Ability Profile 组成。

## 1. 核心对应关系

| 系统视角 | 唯一事实来源 | 约束 |
|---|---|---|
| 工程项目的近期路线 | `master_outline.md` 的长期方向/里程碑映射 | 不写第二份 current_topic/action/checkpoint；状态以 Gate 为准 |
| 单个里程碑 | 某个 `01_topics/<TOPIC>/gates.md` 中的一条 Gate | ID/当前 Gate/Pass Rule/Assistance 规则不变 |
| 一次推进 | 当前 Topic/Gate 的 Lesson | 同一个 Lesson 不跨 Topic 自动写 Evidence |
| 工程结果 | `evidence.md` 的观察、产物链接和结果 | 高辅助结果也可记 PARTIAL；不能据此直接 PASS |
| 跨域能力综合判断 | `ability_profile.md` | 仅经 Master Plan、人审和 commit 更新，严格 L0..L6 |

系统项目不需要新增 `PROJECT` Status、`PROJECT-EXP` ID 或并行的“里程碑 PASS”表。一个里程碑应有**且仅有**一个明确的 owner Gate，其他能力域用其 own Gate 验收，避免跨 Topic 改写 Evidence。

## 2. Master 怎么拆项目

1. 定义 *North Star*、Demo Profile 与 Target Profile。硬件/带宽参数不明时写 `TBD`，不得声称可用。
2. 在 Master Outline 列出稳定的交付里程碑、**owner Topic/Gate**、前置依赖与候选影响的能力项；不在此登记每堂课的实时进展。
3. 为当前里程碑建立或选择一个 Topic，并以 `03_templates/NEW_TOPIC/` 建立四文件。Gate criteria 用交付物/诊断行为/证据边界表达，而非纯术语熟练度。
4. 同时只允许一个 `current_topic` + `current_gate` 进入 Tutor 路由；未完成的旧 Gate 可以仍 `OPEN`，Topic 设置 `PAUSED` 并记录恢复条件，绝不伪装成 `PASSED`。恢复条件应绑定真实工程风险（例如实际引入复位架构或多时钟），而不是通用前置依赖；暂停不构成 Ability 升级理由。
5. 非当前 Topic 的预定 Gate 保持 `DRAFT`；接手时由 Master 依据证据和依赖决定是否改成 `OPEN`。

## 3. 项目证据的验证范围

项目进展仍通过当前 Gate 的 Lesson 和 Evidence 记录。没有实际运行实机测试时，不能把结果标成实机验证；可在 Evidence 的 `Observation`/`Interpretation` 中注明 `SIM_VALIDATED`、`IMPLEMENTED`、`HARDWARE_VERIFIED`、`PERFORMANCE_MEASURED` 等说明性验证范围（不新增 schema/enum）。

Tutor 教学行为参照共同教学规范与选中的 Project Mode；Evidence 字段、Gate PASS 与 Assistance ceiling 以现有 Gate/Handoff 机械协议为准。

## 4. Ability Profile 怎么更新

Ability 表示长期、粗粒度的独立能力，不是 Gate 完成数量的函数。

| 观察 | 正确动作 |
|---|---|
| 项目实施中新增一次有效实验但能力仍受明显引导 | 记录 `DEBUG/PARTIAL/A2` 等 Evidence；Ability 可以不变 |
| 低辅助独立完成某 Gate 的全部 Mandatory Criteria | Tutor 提供 PASS Evidence；按 Gate 路由触发 Master Review |
| Gate 仍 OPEN，但出现新的可迁移独立证据 | Tutor 可设置 `POSSIBLE_LEVEL_CHANGE` 触发 Master Review；仅 Master/Human 有权调整 Ability |
| 结果明显可迁移到多个能力项，或含陌生变式诊断 | Master 综合 Evidence 后提出受影响 Ability Level 的**候选变更**，逐项给理由 |
| 没有新独立证据 / 仅实现通过 | 不自动升级等级；可更新 Baseline note，但仍须 Master Plan 获批 |
| 旧 Gate 遗留缺口，项目暂时不依赖 | Gate 保持 `OPEN`、Topic `PAUSED`；当确实用到该能力时恢复独立验收 |

跨域迁移若需要正式新证据，由相关 Topic 通过后续 Lesson 产生 `TRANSFER` / `REVALIDATION`，不让 Master 编造 Tutor Evidence。

## 5. 和严格 Repo 协议的关系

- 原 `CURRENT_STATE`、优先级、pending transaction、fingerprint、Append-only、Gate PASS 规则全部不变。
- `PENDING_LEARNING_CHANGES` 时必须先处理既有工作区差异（包括 `TEACHING_MODE_ROUTE.md`）；不能绕过状态机新建 Topic 或开课。
- 本流程为 Repo maintenance 规则说明；**不是**某个 Master Plan 的默许批准。`master_outline/ability_profile/01_topics` 仍遵循独立的 `MASTER PLAN → Human 批准 → 审核 diff → Human commit 批准`。
- 可以在隔离测试仓库模拟变更和 Git commit；不得把这种演练视为 Human 已批准真实能力变化。

## 6. 可行的最小闭环示例（规划示意，不是当前事实）

- `HOST_DEVICE-GATE-G1`：Packet V1/Host Python reference、错误注入、golden vectors。
- `HOST_DEVICE-GATE-G2`：FPGA 合成样本 → 板上现有低速链路 → Host 字节流还原，软硬证据分级。
- `HOST_DEVICE-GATE-G3`：背压/连续流/丢帧恢复、吞吐与故障定位；复杂 CDC 可由后续 CDC Topic 独立验收。
- 原 `CLOCK_RESET-GATE-G2` 不必强制在上述与其无依赖的任务之前关闭；涉及真实时钟/复位的实施必须遵守其未验证边界，不能宣布相关功能已获安全证明。

**完成标准**：Human 面对新的采集约束，能独立提出设计与测量方案，做出可复现的端到端工程产物，并清楚说明结果没证明什么。不是“全部 Topic 绿灯”。
