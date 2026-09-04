# SDD：修复 Obsidian Markdown 笔记规范化脚本

## 1. 背景

`tools/obsidian_note_normalizer.py` 有 8 个 bug：
- dry-run 仍写文件
- 处理非 .md 文件
- 修改代码块内容
- 重复添加 frontmatter
- 重复添加 tags
- 非 UTF-8 编码
- 空文件不稳定
- 无结构化报告

## 2. 功能目标

修复所有 bug，保持单文件脚本结构：
- dry-run 只输出计划不写文件
- 只处理 .md，跳过 .git/.obsidian
- 保护 fenced code block 内容
- 已有 frontmatter 不重复加
- tags 不重复
- UTF-8 + 中文路径兼容
- 输出处理报告

## 3. 非目标 / 本次不做

- 不引入第三方依赖（python-frontmatter, PyYAML, markdown-it 等）
- 不重写成 Obsidian 插件
- 不接入 Obsidian API
- 不修改真实知识库文件
- 不删除/移动/重命名文件
- 不修改 .obsidian / .git 目录
- 不伪造测试结果

## 4. 允许范围

- `tools/obsidian_note_normalizer.py`
- `tests/test_obsidian_note_normalizer.py`（新建）
- `tests/fixtures/`（已有 5 个样例）
- README 相关说明

## 5. 验收

### 功能
- dry-run 不写文件
- 非 .md 文件跳过
- 代码块内容不变
- frontmatter 不重复
- tags 不重复
- UTF-8 通过

### 工程
- 0 第三方依赖
- 4 份报告齐全
- 测试可运行
