# ChangedFiles.md — Files Changed in Bug Fix

## Commit: f7c8aa6
Branch: `feature/fix-normalizer`
Message: `fix: resolve 8 bugs in obsidian_note_normalizer`

---

## Modified: tools/obsidian_note_normalizer.py

### Summary of changes
| Area | Before | After |
|------|--------|-------|
| Lines | 70 | ~220 |
| Functions | 7 | 12 |
| Imports | 3 | 3 (no new) |
| Dependencies | 0 third-party | 0 third-party |

### Detailed diff (conceptual)

**New helper functions added:**
- `extract_code_blocks(content)` — replaces fenced code blocks with placeholders
- `restore_code_blocks(content, blocks)` — restores placeholders to original blocks
- `tag_exists_in_content(content, tag)` — checks tag presence in body + frontmatter
- `print_report(results)` — formatted summary output

**Modified functions:**

**`has_frontmatter(content)`**
- Changed: `content.startswith("---")` → `content.lstrip().startswith("---")`
- Reason: handle leading whitespace / BOM bytes

**`add_frontmatter(content, title)`**
- Added: defensive `if has_frontmatter(content): return content` guard
- Changed: `datetime.now()` → `datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
  for predictable, human-readable timestamps
- Changed: `tags: {DEFAULT_TAGS}` (Python repr) → `tags: [{', '.join(DEFAULT_TAGS)}]`
  (valid YAML-style list)

**`normalize_tags(content)`**
- Changed: uses `tag_exists_in_content()` instead of raw `f"#{tag}" not in content`
- Reason: skip tags already declared in frontmatter

**`normalize_wikilinks(content)`**
- Added: `extract_code_blocks()` / `restore_code_blocks()` wrapping
- Changed: regex `re.sub` now applied only to content outside code blocks
- Reason: protect code block content from modification

**`process_file(path, dry_run=False)`**
- Added: `encoding="utf-8"` on both `open()` calls
- Added: empty-file guard → returns skipped result early
- Added: dry-run check → returns early without writing
- Added: change tracking (`changes` list)
- Changed: returns `dict` instead of `None`
- Changed: `print()` message includes changes detail

**`process_dir(root, dry_run=False)`**
- Added: directory exclusion (`dirs[:] = ...` for .obsidian/.git)
- Added: file extension filter (`if not file.endswith(".md"): continue`)
- Changed: returns `list[dict]` instead of `None`

**`main()`**
- Changed: calls `print_report(results)` after processing
- Changed: returns `results` list for programmatic use
- Changed: argparse description updated

---

## New: tests/test_obsidian_note_normalizer.py

| Metric | Value |
|--------|-------|
| Lines | ~380 |
| Test functions | 21 |
| Test classes | 0 (flat module) |
| Fixtures | 1 (`work_dir`) |
| Dependencies | `pytest` (test only), stdlib only |

### Test inventory by bug:
| Bug | Test(s) |
|-----|---------|
| 1. dry-run | `test_dry_run_does_not_write` |
| 2. md filter | `test_non_md_files_skipped`, `test_obsidian_and_git_dirs_excluded` |
| 3. code blocks | `test_code_blocks_protected_from_wikilink_normalization`, `test_code_blocks_protected_from_tag_detection`, `test_extract_restore_code_blocks_roundtrip`, `test_extract_code_blocks_no_blocks`, `test_normalize_wikilinks_outside_code_blocks` |
| 4. frontmatter | `test_frontmatter_not_duplicated`, `test_frontmatter_added_when_missing` |
| 5. tags | `test_tags_not_duplicated`, `test_tags_in_frontmatter_not_duplicated` |
| 6. UTF-8 | `test_utf8_encoding_read_write`, `test_utf8_with_bom_handled` |
| 7. empty files | `test_empty_file_does_not_crash`, `test_whitespace_only_file_skipped` |
| 8. reporting | `test_process_file_returns_structured_dict`, `test_process_dir_returns_list_of_dicts`, `test_empty_dir_returns_empty_list`, `test_full_dry_run_on_fixtures` |
| Unit | `test_has_frontmatter` |

---

## Files NOT modified (per rules)
- `tests/fixtures/normal_note.md` — unchanged
- `tests/fixtures/has_frontmatter.md` — unchanged
- `tests/fixtures/code_block.md` — unchanged
- `tests/fixtures/empty.md` — unchanged
- `tests/fixtures/note.txt` — unchanged
- `SDD-fix-normalizer.md` — unchanged (reference only)
