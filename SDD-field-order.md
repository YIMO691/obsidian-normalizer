# SDD：新增 frontmatter 字段顺序稳定化

## 1. 背景

当前 normalizer 36/36 pytest 通过。新增需求：frontmatter 字段稳定排序。

## 2. 新增目标

核心字段顺序固定为 title → created → updated → tags → aliases。未知字段保留在后且保持原顺序。不存在不强行加。

## 3. 非目标 / 本次不做

- 不引入第三方 YAML 库
- 不覆盖 created/title
- 不强加 updated/aliases
- 不删除/放宽旧测试
- 不丢失多行字段/未知字段
- 不破坏 dry-run

## 4. 回归要求 ★ 关键

- 旧 36 个测试必须全部通过
- 新增 ≥5 个测试（字段排序、未知保留、多行保留、不强行新增、aliases排序）
- 完整 pytest 输出

## 5. 验收

pytest 全部通过。旧 36 + 新增 ≥ 41。
