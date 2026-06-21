# SDD：修复 Obsidian normalizer 的 YAML frontmatter 合并逻辑

## 1. 背景

当前 `obsidian_note_normalizer.py` 已修复 8 个基础 bug（dry-run、.md过滤、代码块保护、frontmatter检测、tags去重、UTF-8、空文件、报告），但 frontmatter 处理仍有边界漏洞：

- YAML 列表格式 tags 未被识别，仍可能在正文追加 #tag
- 内联数组格式 tags 未被识别
- 中文 title 可能被破坏
- 已有 created 日期可能被覆盖
- 多行字段（如 description）可能丢失
- 代码块中的 `---` 可能被误判为 frontmatter

## 2. 功能目标

不引入第三方 YAML 库，保守修复 frontmatter 合并：
- 识别 YAML 列表 tags + 内联数组 tags
- tags 合并去重（默认 + 已有）
- 保留 title、created、多行字段、未知字段
- 代码块内 `---` 不被误判
- dry-run 不写文件

## 3. 非目标 / 本次不做

- 不引入 PyYAML、python-frontmatter、ruamel.yaml
- 不实现完整 YAML 解析器
- 不重写整个工具
- 不覆盖已有 created/title
- 不修改代码块内容
- 不伪造 pytest 结果

## 4. 验收

8 个新增 pytest 用例全部通过，21 个已有测试不退化。
