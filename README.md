# xiaohongshu-publisher

把主题或素材写成可复制发布的小红书（Xiaohongshu / RED / XHS）笔记草稿：标题、正文、话题标签、封面文案、配图建议；支持图文与视频脚本；默认 3 个备选版本。

**只生成文案与人工发布指引，不登录小红书，不自动上传或发帖。**

当前版本：**0.1.1**（见 `SKILL.md` → `metadata.version`）。

## 安装

把本仓库目录放到宿主的 skills 路径，目录名建议保持 `xiaohongshu-publisher`：

| 宿主 | 常见路径 |
|---|---|
| Claude Code | `~/.claude/skills/xiaohongshu-publisher/` |
| Cursor / Agent 自定义 skill | 以产品文档中的 skills / workflows 目录为准，放入同名文件夹 |

目录应包含：

```
xiaohongshu-publisher/
├── SKILL.md
├── references/
│   ├── platform-rules.md   # 字数与合规唯一来源
│   ├── title-formulas.md
│   ├── keyword-guide.md
│   └── examples.md
├── scripts/
│   └── check_note.py       # 字数/标签/禁用词自检
├── evals/
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## 何时会用到

- 「帮我写一篇小红书笔记」
- 「把这段素材改写成小红书图文 / 测评 / 探店」
- 「写个小红书视频脚本」
- 「小红书种草文案」「优化标题和标签」

不会用于：公众号 / 知乎 / 微博 / 抖音正文，登录 / 上传，账号数据分析，纯封面出图。

## 输出长什么样

- **图文：** 标题、正文（纯文本代码块）、标签 5–10、封面、配图建议、版本说明
- **视频：** 分镜表（时间码｜画面｜口播｜字幕）、口播稿、封面、CTA、时长建议
- 缺真实经历时用 `【待补充：…】`，不编造第一人称数据
- 文末附发布时间、互动、**AI 内容标识**、合作/样品标注等人工发布提醒

硬限制口径只维护在 `references/platform-rules.md`。

### 示例（缩略）

**输入：** 新手养猫避坑

**版本 A · 避坑清单**

- 标题：`新手养猫必踩的5个坑，第3个超坑`
- 正文：痛点开头 → 5 条要点（经历处占位）→ 互动引导
- 标签：`#新手养猫` `#养猫避坑` …
- 封面：主「5 个坑」/ 副「第 3 条超坑」

完整好/坏对照见 `references/examples.md`。

## 自检脚本

```bash
python3 scripts/check_note.py note.json
# 或
echo '{"title":"新手养猫必踩的5个坑","body":"……","tags":["#新手养猫","#养猫避坑","#养猫注意事项","#养猫日记","#宠物护理"]}' \
  | python3 scripts/check_note.py
```

检查标题 ≤20、正文 ≤1000（不含标签，待实测）、标签 5–10，并扫描绝对化 / 医疗 / 金融风险词。`PASS` 退出码 0，`FAIL` 为 1。

## 合规摘要

医疗不写疗效承诺，金融不承诺收益，不编造数据与背书；宣称场景禁用「最 / 第一 / 百分百 / 永久」等绝对化用语；AI 辅助内容建议按平台规则标识。详见 `references/platform-rules.md`。  
**不维护无出处的长敏感词表。**

## 评测

- `evals/evals.json` — 场景与断言（含反编造、硬规则、视频分镜等）
- `evals/triggers.json` — `{"query","should_trigger"}` 数组，可对接 skill-creator description 优化循环

## 许可

MIT © 2026 baitianlime
