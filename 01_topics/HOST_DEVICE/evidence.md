---
schema: topic_evidence
topic: HOST_DEVICE
mutation: APPEND_ONLY
---

# HOST_DEVICE Evidence Ledger

> Evidence 是历史事实账本，只允许在末尾追加。
>
> 新 Lesson 只追加新的 Evidence Entry，不用最新 Handoff 覆盖旧 Evidence。
> 旧解释被推翻时，追加新的 Evidence / Amendment 语义条目并引用旧 ID，不静默重写历史。

## Evidence Entries

<!-- 在这里继续追加新的 Evidence Entry。 -->

### HOST_DEVICE-EXP-001 — Human 对 UART 回环架构及最小协议边界的业务判断

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PARTIAL`
Assistance: `A2`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261013-233205`

References:
- NONE

Artifacts:
- packet_v1_g1_final_review_20261015.zip
- protocol/PROTOCOL_V1.md

#### Observation
Human 依据项目目标主动要求 PC→FPGA→PC 的最小实机回环，指出 PC→FPGA 可发送原始 int16 小端采样，FPGA→PC 才用 Packet V1；认为 GUI 产生样本可自由配置内容/速率，并明确不加入 ACK、重传、逐采样回环比对。Human 多次质询并最终删除不必要的自动会话超时与末帧特判；接受初始/失同步阶段双帧确认会舍弃孤立有效候选。

#### Interpretation
支持 C1 中协议边界和工程取舍的部分实际理解表现；讨论中存在 Tutor 的明显引导，规格文件也由 AI 撰写，不能证明全部 C1 内容已由 Human 在 A1 下独立审签，不能构成 Gate PASS。

### HOST_DEVICE-EXP-002 — Human 对重同步、序号回绕和错误统计的部分独立判读

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PARTIAL`
Assistance: `A2`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261013-233205`

References:
- HOST_DEVICE-EXP-001

Artifacts:
- packet_v1_g1_final_review_20261015.zip
- C3_ADDENDUM.md

#### Observation
看到 SEQ 10/11/12(坏 CRC)/13/14 的观察结果时，Human 主动指出 13 在等待后可与 14 一起成功解包，并追问 sync_lost 为什么仍为 1；经解释后讨论 CRC 失败、同步切换与 SEQ 不连续可能属于同一事件，认识到 8-bit SEQ 回绕使真实丢帧数可能为 1+256k 而不能直接统计。Human 也质疑双端同样使用错误大端编码/解码仍可得到正确业务数值，引出独立 Golden Reference 的必要性。

#### Interpretation
支持 C3 的故障行为解释及测试盲区意识已有进展；并未观察到 Human 低辅助地独立设计、运行、核验完整故障矩阵，故仅 PARTIAL，不标 PASS。

### HOST_DEVICE-EXP-003 — AI 编写 Packet V1 参考软件与可复现测试结果

Schema: `evidence_entry`
Type: `LEARNING`
Result: `PARTIAL`
Assistance: `A3`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261013-233205`

References:
- HOST_DEVICE-EXP-001
- HOST_DEVICE-EXP-002

Artifacts:
- packet_v1_g1_final_review_20261015.zip
- protocol/PROTOCOL_V1.md
- host/reference_client.py
- golden/golden_vectors.json
- tests/test_packet_v1.py
- TEST_REPORT.md
- TEST_LOG.txt
- C3_ADDENDUM.md

#### Observation
Tutor/AI 生成 Packet V1 文档、增量 Parser、冻结 Golden Vectors 和 unittest；工具执行结果为 26/26 通过，包含 CRC-16/IBM-3740 独立算法核对、字节序边界、随机分块、bit flip、字节/整帧丢失、伪帧与短/截断流。最后增加独立小端向量：SEQ=7、0x1234 → B5 62 01 07 02 34 12 32 7F；归档 ZIP 经过读取与完整性核查。

#### Interpretation
说明当前参考软件有可复现的 SOFTWARE_ONLY 实现和测试覆盖，支持未来 FPGA 阶段复用。这不是 Human 编码成果，未核实 FPGA/USB-UART 实机，且 Assistance=A3 高于 Gate A1 ceiling，因此不得用于宣称 C2 独立实现通过，也不构成 Gate 的合格 PASS Evidence。

### HOST_DEVICE-EXP-004 — Human 对 Packet V1 最小规格与误同步边界的最终审签

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261017-110156`

References:
- HOST_DEVICE-EXP-001

Artifacts:
- NONE

#### Observation
Human 以四段独立审查意见陈述帧字段、CRC 覆盖、双帧同步和不增 ACK/重传/会话的工程理由，作出批准结论；此后反复主动澄清单帧不特判、当前容许流数据丢失、输入侧 CRC 盲区不纳入 G1。面对 Tutor 的三内嵌合法伪帧反例，Human 在知道‘不能保证最多两帧误交付、不能保证立即失同步’后，仍独立确认接受风险和维持 V1 的决定。

#### Interpretation
直接支持 C1 的实际适用范围和风险责任由 Human 持有；A1 仅描述独立提交的审签与最后裁决，不把此前 Tutor 对 CRC init、异常状态和理论吞吐的高辅助讲解追认为 Human 的独立推导。风险概率未建模，不宣称数学上的低于某阈值。

### HOST_DEVICE-EXP-005 — Human 独立构造正确的 CRC-16 Golden Vector 和解析判据

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261017-110156`

References:
- HOST_DEVICE-EXP-002

Artifacts:
- NONE

#### Observation
在先前错误 init 被明确纠正之后，Human 收到一条新输入 `VERSION=01, SEQ=00, sample=[0x1234,-1]`，独立返回 `B5 62 01 00 04 34 12 FF FF BD 16`；Tutor 按 CRC-16/IBM-3740 参数核对正确。Human 独立提出 byte buffer、指针逐字节定位、空 read 维持状态及同步后 LEN 定界思路，并在后续综合题中独立指出 CRC 正确的 SEQ 跳号帧必须交付，不得因此失同步。

#### Interpretation
支持 C2 对独立 Golden Vector、样本/CRC 小端序、状态分支与交付失败判据的掌握。以前错用 `init=0000` 计算出的 CRC 不作为 PASS；Human 未独立编写 Parser 或做源代码逐行核验，但 Gate 已允许 AI 协作实现。

### HOST_DEVICE-EXP-006 — Human 独立故障测试设计与最终统计综合判读

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `PASS`
Assistance: `A1`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261017-110156`

References:
- HOST_DEVICE-EXP-002
- HOST_DEVICE-EXP-005

Artifacts:
- NONE

#### Observation
Human 主动设计五组故障机制：Header 篡改、字节插入、载荷内有效伪帧、A/B 破坏引发的双帧同步差异、同步后 C 的 LEN 异常。在综合验收 `10,11,15,16(坏CRC),17,18` 场景中，独立填出交付 `10,11,15,17,18`，`bad_crc=1`，`sync_lost=1`，`sync_acquired=2`，`sequence_discontinuities=2`；说明跳号只是序号不连续，与 CRC 不合格不同，合法跳号帧应立即交付。

#### Interpretation
直接支持 C3 的故障机制设计、行为预测、计数口径与判定。四种计数反映不同事件，不应相加充当丢帧数。Tutor 后续纠正 Human 使用的‘bit 级重同步’为 Byte 级搜索；伪帧风险最坏后果的早期推测也曾被反例纠正，不能把这些错误推测记为 PASS。Human 并未亲手实现或执行 13 项注入代码，且没有 FPGA 实机证据。

### HOST_DEVICE-EXP-007 — Tutor 新参考解析器与故障注入的软件自测记录

Schema: `evidence_entry`
Type: `LEARNING`
Result: `PARTIAL`
Assistance: `A3`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261017-110156`

References:
- HOST_DEVICE-EXP-003

Artifacts:
- reference_client_review.py
- test_reference_client_review.py
- packet_v1_parser_review_bundle_v2.zip
- packet_v1_human_fault_review.zip
- PACKET_V1_HUMAN_FAULT_REPORT.md

#### Observation
本 Lesson 对话中 Tutor 声称为审查编写新版 Python Parser 与测试：基础 19/19，将 Human 五个故障方向落实成新增 13 个测试，最终报告合计 32/32 PASS（SOFTWARE_ONLY）。此 Handoff 仅按对话所报告的测试事实记录，收课时未重新获取这些文件的完整源码或重新执行测试。

#### Interpretation
支持软件参考方案已有工具辅助的测试案例与结果报告，但不支持 Human 独立执行、FPGA 实机通过、全部故障空间覆盖或 Gate 独立性 A1；因此记 A3/PARTIAL，不能以 32/32 单独构成 G1 PASS。

### HOST_DEVICE-EXP-008 — CRC-8 与补码的指导性原理学习

Schema: `evidence_entry`
Type: `LEARNING`
Result: `PARTIAL`
Assistance: `A2`
Gate: `HOST_DEVICE-GATE-G1`
Lesson: `HOST_DEVICE-LSN-20261017-110156`

References:
- NONE

Artifacts:
- CRC8_模二除法_补码_课堂笔记_更新版.md

#### Observation
Human 主动要求比较 CRC-8/CRC-16、模二长除法、`poly`/`init`、CRC 检错和奇偶校验、不超过 8 bit 的突发错误与有符号/无符号补码。Tutor 给出 `CRC-8/SMBUS poly=07, init=00`、`0x1C -> 0x54` 演算、碰撞/漏检示例、`-1`/`-2` 的 signed int16 小端例子及课程 Notes。

#### Interpretation
支持本课教学内容和后续参考 Notes，但多为 Tutor 演示、并非 Human 在 A1 下独立完成的新 CRC-8 验收；不据此改变 G1 条件或将 CRC-8 练习列为 G1 必选项。
