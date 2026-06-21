# ChangedFiles.md — Obsidian Note Normalizer Frontmatter Merge

**Generated:** 2026-06-21
**Branch:** v1.7-conditional-stress
**Base commit:** 4ed3213 (merge: fix obsidian normalizer — 8 bugs, 0 deps, 21 tests)

---

## Commits

### Commit 1: `3d16c4c` — feat: add SDD and 8 test fixtures for frontmatter merging scenarios

**New files:**
- `SDD-frontmatter-merge.md` — Specification document for frontmatter merging
- `tests/fixtures/frontmatter/yaml_list_tags.md` — Fixture: YAML list-format tags
- `tests/fixtures/frontmatter/inline_array_tags.md` — Fixture: inline array tags
- `tests/fixtures/frontmatter/chinese_title.md` — Fixture: Chinese title + tags
- `tests/fixtures/frontmatter/multiline_field.md` — Fixture: multi-line `|` field
- `tests/fixtures/frontmatter/no_frontmatter.md` — Fixture: no frontmatter
- `tests/fixtures/frontmatter/codeblock_dashes.md` — Fixture: `---` in code block
- `tests/fixtures/frontmatter/has_created_date.md` — Fixture: created 2020-01-01
- `tests/fixtures/frontmatter/dry_run_verify.md` — Fixture: dry-run verification

### Commit 2: `9d215ad` — fix: implement YAML frontmatter parsing, merging, and rebuilding

**Modified:**
- `tools/obsidian_note_normalizer.py` (+347 / -8 lines)

**New functions:**
| Function | Lines | Purpose |
|----------|-------|---------|
| `read_file_helper()` | +6 | UTF-8 file reader helper for tests |
| `protect_codeblock_dashes()` | +18 | Replace `---` inside code blocks with placeholders |
| `restore_codeblock_dashes()` | +11 | Restore placeholder `---` back |
| `parse_frontmatter()` | +112 | Conservative YAML parser (key:value, arrays, lists, multiline `\|`, Chinese) |
| `rebuild_frontmatter()` | +35 | Reconstruct YAML frontmatter from fields dict |
| `merge_tags()` | +9 | Merge default + existing tags, no duplicates |
| `get_existing_tags()` | +11 | Extract tags from parsed fields (list or string) |
| `merge_frontmatter()` | +45 | Main orchestrator — parse, merge, preserve, rebuild |

**Modified functions:**
| Function | Change |
|----------|--------|
| `has_frontmatter()` | Now protects code-block dashes before checking |
| `process_file()` | Uses `merge_frontmatter()` instead of naive `add_frontmatter()` |

### Commit 3: `efc9d6b` — test: add 15 pytest tests for frontmatter merging (8 scenarios)

**Modified:**
- `tests/test_obsidian_note_normalizer.py` (+390 / -2 lines)

**New tests:** 15 tests covering all 8 SDD scenarios + roundtrip test
**Existing tests updated:** `test_full_dry_run_on_fixtures` (flexible count for new subdirectory)

---

## Net change summary

| File | Status | Lines Changed |
|------|--------|---------------|
| `SDD-frontmatter-merge.md` | NEW | +34 |
| `tests/fixtures/frontmatter/*.md` (8 files) | NEW | +97 |
| `tools/obsidian_note_normalizer.py` | MODIFIED | +347 / -8 |
| `tests/test_obsidian_note_normalizer.py` | MODIFIED | +390 / -2 |
| **Total** | | **+868 / -10** |

## No files deleted
