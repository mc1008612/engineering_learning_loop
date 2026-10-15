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
