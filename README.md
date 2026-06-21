# Obsidian Note Normalizer

> Obsidian Markdown 笔记规范化工具。hermes-harness 工作线的 Python 验证场。

## 功能

- YAML frontmatter 解析、合并、规范化
- 字段排序（tags/created/modified → 字母序）
- 幂等性保证（多次 normalize 不产生二次 diff）
- dry-run 模式

## 测试

```bash
cd tests && pytest -v
```

36 条测试覆盖 8 种 frontmatter 场景。

## 相关仓库

- [hermes-harness](https://github.com/YIMO691/hermes-harness) — Agent 工作线（管线本体）
- [BackpackDemo](https://github.com/YIMO691/BackpackDemo) — Unity 验证项目
