---
schema: teaching_mode_route
HOST_DEVICE-GATE-G1: PROJECT
---

# Teaching Mode Route

本文件由 Human 批准后的 Master Plan 维护，按 **Gate ID → Teaching Mode** 指定课程策略。

- 合法模式：`PROJECT`、`CONCEPT`。
- 每次 Master 将新 Gate 交给 Tutor 前，必须确认该 Gate 的模式，并经 Human 审批后在 frontmatter 中增加唯一映射。
- Python 从当前 `state.current_gate` 查找映射，只装配 `TEACHING_CONTRACT.md` 与选中模式的规范。
- 缺失、重复、非法映射会阻止 Tutor 开课；模式选择不写入 `master_outline.md`。
- 本文件的模式映射变更属于 Master 批准的课程配置，提交前与学习状态一样需要 Human 审核。
