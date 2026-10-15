---
schema: topic_notes
topic: HOST_DEVICE
mutation: CURATED
---

# HOST_DEVICE Notes

## Durable Mental Models

- OSI 七层原始表格（按本 Lesson 首次出现的 Markdown 表格逐字保留，不改写行名与例子）： | 层级 | 名称 | 解决的核心问题 | 典型例子 | |---|---|---|---| | L7 | 应用层「Application」 | 数据代表什么业务？ | HTTP、设备采样消息 | | L6 | 表示层「Presentation」 | 数据如何编码和表示？ | 数据格式转换、编码、加密 | | L5 | 会话层「Session」 | 通信会话怎样建立、维持、结束？ | 会话管理、检查点 | | L4 | 传输层「Transport」 | 端到端的数据怎样交付？ | TCP、UDP | | L3 | 网络层「Network」 | 数据如何穿过多个网络到达目标？ | IP、路由 | | L2 | 数据链路层「Data Link」 | 相邻节点如何组织和传输数据帧？ | 以太网 MAC、链路帧校验 | | L1 | 物理层「Physical」 | 比特怎样变成真实物理信号？ | 电气信号、线缆、收发器 |
- 协议分层是职责分开，不是点对点 UART 必须机械实现 OSI 七层。UART/USB-UART 管底层比特收发，Packet V1 负责设备→Host 分帧和采样表示；TCP/UDP 属于网络传输层示例，AXI4-Stream 的 TVALID/TREADY 是逐拍握手、TLAST 标出传输边界，它们不是 ACK 重传机制。
- Python 通过操作系统/串口驱动设置 USB-UART 波特率并写入字节；真正逐 bit 的 UART 发送时序由 USB-UART 芯片等硬件时钟实现，而非 Python GUI 定时器逐 bit 生成。USB 桥接器缓存/延迟可导致 Python 一次 read() 收到任意长度的字节块；它是持续字节流的分批交付，不是按独立 TXT 或 Packet V1 帧自动分组。
- 区分四种速率：UART 硬件 bit/baud 时序、PC 软件平均生成样本速率、瞬时 USB/OS read() 批次节奏、Packet V1 有效采样吞吐率。以 115200 baud/8N1 为例，一组 16×int16 原始输入为 32 Byte（约 2.78 ms），输出加 7 Byte 字段成为 39 Byte（约 3.39 ms）；连续满速输入最多约 5760 samples/s，输出最多约 4726 samples/s，若 PC 每 20 ms 发一组则约 800 samples/s，留有余量。软件发送间隔不是精密 ADC 采样时钟。
- FIFO 好比水桶：一阵子进水快可以先存着，但若长期流入快于流出，再大的桶也会装满。本例同波特率下原始输入每 16 样本 32 Byte、Packet V1 输出 39 Byte，持续满速送入会积压；当前 PC 自己控制 Data Generator，优先通过调低平均输入速率解决，不通过无限增大 FPGA FIFO 伪装吞吐问题。接收缓存只平滑突发，不解决长期速率失配。
- CRC 只对被它覆盖的字节检错，不是加密、不是绝对不出错，也不自动验证 FPGA 封包前的原始输入是否正确。PC→FPGA 原始 UART 若漏掉/错收字节，FPGA 对错误 int16 重新算出合法 Packet V1 CRC 时，Host 的 bad_crc、SEQ 和同步统计甚至可能全正常。
- 未同步时需两条相邻、CRC 正确、SEQ 模 256 递增的完整候选帧才可信，确认后两帧一起交付；已同步时 CRC 正确的一帧立即交付，因此正常最后一帧不等待第二条。孤立合法候选在初始/恢复时可能弃用，是连续采样方案有意识接受的代价，不应为此添加超时放行。
- 8-bit SEQ 从 0 到 255 然后回绕；只凭上次收到 11、下次收到 13 且假定设备未重启、SEQ 每帧加一，实际丢帧可为 1+256k（k≥0），不一定只丢 1 帧。SEQ 能提供有限的连续性线索，无法用来保证准确统计所有丢失、更无法唯一判定设备重启。
- 错误计数记录的是不同现象，不是可以相加的丢帧总数。例：10、11 交付，12 CRC 错，13、14 恢复双帧确认且全部交付；bad_crc=1、sync_lost=1、sync_acquired=2（初次+恢复）、sequence_discontinuities=1，真正已知测试注入只有 12 一帧损坏；统计项不应相加显示『丢两帧』。
- 会话管理的价值来自中断恢复需求和重新开始的成本，而非只因为数据多。大文件下载、固件升级可保存对象标识、进度和完整性证据以便断点续传；当前 UART 连续监测无需独立会话层、心跳、超时宣告会话结束。会话相关能力可以由应用层和现成协议实现，并不必须独立实现 OSI L5。
- Golden Reference/Golden Model 是依据明确规格制成的可信标准答案，Golden Vectors 是固定输入与预期输出；不是本课自造名词。独立的意义是：期望值不能由同一个被测编码器自产自验。两个实现都误用大端时业务值往返可能相同，却共同违反小端协议；例 sample=0x1234 预期线上低字节先 `34 12`，完整 SEQ=7 测试帧为 `B5 62 01 07 02 34 12 32 7F`。

## Engineering Rules

- Packet V1 候选字段固定为 SYNC `B5 62` + VERSION `01` + SEQ 1 Byte + LEN 1 Byte + PAYLOAD int16 小端 2..32 Byte + CRC16 小端 2 Byte；LEN 是载荷字节数，须为 2,4,...,32，不含其他字段。CRC-16/IBM-3740 poly=0x1021、init=0xFFFF、非反射、xorout=0；覆盖 VERSION/SEQ/LEN/PAYLOAD，不含 SYNC。
- G1 只涵盖 Packet V1 协议、任意分块 Parser、独立 Golden Vectors 和必要故障恢复；不把 G2/G3 阶段的 FPGA 实机 GUI、性能、背压、DDR/高速采样工程或 S1 命令/响应纳入当前 Gate 的必备条件。
- Host 解析器必须接受任意大小 read() 字节块；`feed(b'')` 是暂时没有新增字节，不表示帧尾、截断或 EOF。保持缓存和同步状态，直到下一次字节到来；仅 Host 主动停用/关闭 Parser 才执行 `finish()` 统计残留；当前取消自动连续 N 次读取超时关闭策略。
- PC→FPGA→PC 是后续必须实践的最小硬件闭环。一个 USB-UART 的 TX/RX 物理全双工可由同一个 Python 进程打开同一 COM 口并读写；PC→FPGA 发送无 Packet V1 包头的原始 signed-int16 LE 字节流，FPGA UART RX 拼接并按 16 个样本一组封包后返回 Packet V1。初版 GUI 配置采样内容和平均发送速率，暂不做源样本逐个校对。
- 输入没有帧头时，丢一个字节就可能令后续 int16 高低字节长期错位；测试前复位 FPGA 的接收/拼接/封包状态，清除 PC 串口旧数据，检测 UART RX framing/overrun；若需要将此错误报告给 GUI，必须有可观察的状态路径，不能从 Packet V1 输出 CRC 自动推定。
- 重同步：坏版本、非法 LEN、CRC 失败或边界不符合时，拒绝候选并从候选起点向后滑动 1 Byte 继续找 SYNC；未同步阶段连续两帧都有效且 SEQ 连续才恢复。SEQ 跳变但当前已同步帧 CRC 有效时，记录异常并交付该帧。
- UART 初版示例可采用 115200 baud、8N1、每 20 ms 发送一个 16 样本完整分组；不使用 GUI QTimer 生成逐比特 UART 波形，不在 G1 把串口定时抖动/FPGA 时钟测量加入前置要求（后续可选）。
- 当前业务场景为持续监测、容许同步建立/恢复时丢少量有效候选；既不保证只有一帧的有限采集能交付，也不保证无错漏的文件或升级业务。若转成零丢失/可靠传输，必须另行明确结束条件、流控、重传或协议能力。
- Human 要求 AI 负责实现代码、Human 负责业务逻辑审核；原 G1 C2 则要求 Human 独立实现、最终 Assistance≤A1。应先通过 Master Review 正式处理验收口径，不得偷偷把 AI 输出改记成人类独立 PASS。

## Debug Checklist

- 验证输出帧：先检查 SYNC、VERSION、LEN 是否在合法范围，再按 LEN 找出 PAYLOAD/CRC 范围；CRC 由 VERSION 到 PAYLOAD 计算；有符号 16-bit 先低字节、后高字节。
- 任意读块测试：把同一串合法帧分别按逐字节、任意随机切分、空 read 和一次读取多帧送入解析器，应得到相同交付结果；不能假设一次 read() 等于一帧。
- CRC 不符时检查捕获点：错误出现在 FPGA 输入 UART RX 之前/之中、FPGA 拼接/封包时，还是 FPGA Packet V1 输出之后；如果错误发生在封包之前，正常 CRC 可能完全掩盖它。
- 读 GUI 错误统计先问『计数对象是什么』：bad_crc=候选帧 CRC 失败次数，sequence_discontinuities=已交付帧序号异常事件，sync_lost=已同步→未同步次数，sync_acquired=建立同步总次数；不直接相加。
- 如果解析器长时间不交付帧：检查是否仍未同步、是否仅见一条孤立合法候选、是否存在声明最大 LEN 却未凑齐数据的假头，以及是否需要更多字节才可排除假候选。
- 实机前必须核实板卡 UART 出口、FPGA I/O 电平、共地、交叉接线、波特率、Windows 同一 COM 口的独占打开与 Python 同进程双向使用；不能凭芯片型号假设板上有 USB-UART。

## Common Failure Modes

- 未同步收到一条 CRC 正确帧就急于交付：载荷内部可能包含伪造 SYNC、头部与 CRC；当前策略要求两条相邻且序号连续的帧，仍不构成数学上的绝对同步证明。
- 合法但不完整的假头声明 LEN=32：即使后面已经有真实的两条短帧，缓冲长度还不够检查假候选 CRC 时会先等待；连续流继续到来后可能恢复，但有限流不保证及时恢复。
- 两个 CRC 正确、SEQ 连续的假帧恰好相邻地出现在另一个合法帧 PAYLOAD 内：从内部偏移开始接收时仍可能被错误确认，当前不引入转义或防伪强保证。
- 把失去同步 1 次、CRC 失败 1 次、序号不连续 1 次加总为丢 3 帧：这些可能是同一次损坏引发的三个可观察现象，未必代表三帧。
- 误以为输出 CRC=0 就能证明 PC 原始输入完整：FPGA 封包前的 UART RX 丢字节或错字节可能被重新封成 CRC 正确但语义错误的 Packet V1；目前不做端到端样本逐项比对。
- 只用同一个编码器生成预期帧，再让同一套实现解码验证：共同的字段/字节序错误可能让往返结果表面正确；应用独立冻结 Golden Vectors 且至少对照一组人为检查的线上字节。
- 把正常无数据的短暂 read() 空返回认定为『末帧截断』或『会话结束』：会错误关闭连续采集；当前由显式 GUI 停止触发收尾。
- 盲目增加 FIFO 却让 PC 长期满速输入：39 Byte 输出的 Packet V1 吞吐低于 32 Byte 原始输入对应的样本吞吐，最终仍溢出，必须限制长期平均输入或使用有意义的背压/丢弃策略。

## References Worth Reusing

- 软件参考材料：`packet_v1_g1_final_review_20261015.zip`，内含 `protocol/PROTOCOL_V1.md`、`host/reference_client.py`、`golden/golden_vectors.json`、`tests/test_packet_v1.py`、`TEST_REPORT.md`、`TEST_LOG.txt`、`C3_ADDENDUM.md`；这是 AI 生成的 SOFTWARE_ONLY 审查包，26/26 测试通过，非硬件或 Human 独立 PASS。
- pySerial 官方 `read()` / timeout / ReaderThread 文档：https://pyserial.readthedocs.io/en/latest/pyserial_api.html ；阅读它们时区分一次 read 超时与应用自己决定结束。
- CRC RevEng CRC-16 catalogue（IBM-3740 参数与校验值 `123456789→0x29B1`）：https://reveng.sourceforge.io/crc-catalogue/16.htm
- Qt QTimer 官方资料：https://doc.qt.io/qt-6/qtimer.html ；开源串口助手示例：https://github.com/kangear/sscom 。用于区分 GUI 周期触发写入与 USB-UART 芯片真正生成位时序。
- 未来工程阅读优先级依据：UART 与 AXI4-Stream 的时序/握手，随后视 FPGA–Host 实机需求学习 Ethernet、PCIe/DMA、DDR、SPI/I2C；不将这些作为本 G1 的新验收内容。
