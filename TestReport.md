# TestReport.md — Pytest Results for obsidian_note_normalizer

## Test Execution

**Command:**
```
python -m pytest tests/test_obsidian_note_normalizer.py -v
```

**Date:** 2026-06-21
**Python:** 3.11.15
**pytest:** 9.0.2
**Platform:** Windows 10 (win32)

---

## Result: 21 passed, 0 failed, 0 errors

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\20544\Desktop\obsidian-normalizer
plugins: anyio-4.13.0, asyncio-1.3.0, timeout-2.4.0
collected 21 items

tests/test_obsidian_note_normalizer.py::test_dry_run_does_not_write PASSED [  4%]
tests/test_obsidian_note_normalizer.py::test_non_md_files_skipped PASSED [  9%]
tests/test_obsidian_note_normalizer.py::test_obsidian_and_git_dirs_excluded PASSED [ 14%]
tests/test_obsidian_note_normalizer.py::test_code_blocks_protected_from_wikilink_normalization PASSED [ 19%]
tests/test_obsidian_note_normalizer.py::test_code_blocks_protected_from_tag_detection PASSED [ 23%]
tests/test_obsidian_note_normalizer.py::test_frontmatter_not_duplicated PASSED [ 28%]
tests/test_obsidian_note_normalizer.py::test_frontmatter_added_when_missing PASSED [ 33%]
tests/test_obsidian_note_normalizer.py::test_tags_not_duplicated PASSED  [ 38%]
tests/test_obsidian_note_normalizer.py::test_tags_in_frontmatter_not_duplicated PASSED [ 42%]
tests/test_obsidian_note_normalizer.py::test_utf8_encoding_read_write PASSED [ 47%]
tests/test_obsidian_note_normalizer.py::test_utf8_with_bom_handled PASSED [ 52%]
tests/test_obsidian_note_normalizer.py::test_empty_file_does_not_crash PASSED [ 57%]
tests/test_obsidian_note_normalizer.py::test_whitespace_only_file_skipped PASSED [ 61%]
tests/test_obsidian_note_normalizer.py::test_process_file_returns_structured_dict PASSED [ 66%]
tests/test_obsidian_note_normalizer.py::test_process_dir_returns_list_of_dicts PASSED [ 71%]
tests/test_obsidian_note_normalizer.py::test_empty_dir_returns_empty_list PASSED [ 76%]
tests/test_obsidian_note_normalizer.py::test_full_dry_run_on_fixtures PASSED [ 80%]
tests/test_obsidian_note_normalizer.py::test_extract_restore_code_blocks_roundtrip PASSED [ 85%]
tests/test_obsidian_note_normalizer.py::test_extract_code_blocks_no_blocks PASSED [ 90%]
tests/test_obsidian_note_normalizer.py::test_has_frontmatter PASSED      [ 95%]
tests/test_obsidian_note_normalizer.py::test_normalize_wikilinks_outside_code_blocks PASSED [100%]

============================= 21 passed in 0.37s ==============================
```

---

## Test Details

### Bug 1: dry-run (1 test)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_dry_run_does_not_write` | PASSED | dry_run=True does not modify file on disk; returns status='dry_run' |

### Bug 2: .md filter (2 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_non_md_files_skipped` | PASSED | note.txt not in results; all .md files present |
| `test_obsidian_and_git_dirs_excluded` | PASSED | .md files inside .obsidian/ and .git/ are excluded |

### Bug 3: code blocks (5 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_code_blocks_protected_from_wikilink_normalization` | PASSED | [[FakeLink]] inside ``` block preserved; [[ Real Link ]] outside normalized |
| `test_code_blocks_protected_from_tag_detection` | PASSED | #ai inside ``` block preserved unchanged |
| `test_extract_restore_code_blocks_roundtrip` | PASSED | extract → restore is exact identity (lossless round-trip) |
| `test_extract_code_blocks_no_blocks` | PASSED | content with no code blocks passes through unchanged |
| `test_normalize_wikilinks_outside_code_blocks` | PASSED | [[ spaced link ]] → [[spaced link]]; code block content untouched |

### Bug 4: frontmatter (2 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_frontmatter_not_duplicated` | PASSED | has_frontmatter.md keeps exactly one --- block; "added frontmatter" not in changes |
| `test_frontmatter_added_when_missing` | PASSED | normal_note.md gets frontmatter added; starts with --- |

### Bug 5: tags (2 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_tags_not_duplicated` | PASSED | #ai appears once; learning in frontmatter prevents #learning append |
| `test_tags_in_frontmatter_not_duplicated` | PASSED | Frontmatter tags respected; no duplicate #tag appends |

### Bug 6: UTF-8 (2 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_utf8_encoding_read_write` | PASSED | Chinese + Japanese characters survive round-trip |
| `test_utf8_with_bom_handled` | PASSED | UTF-8-BOM files do not crash |

### Bug 7: empty files (2 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_empty_file_does_not_crash` | PASSED | empty.md returns status='skipped', reason='empty file' |
| `test_whitespace_only_file_skipped` | PASSED | whitespace-only files also skipped |

### Bug 8: reporting (4 tests)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_process_file_returns_structured_dict` | PASSED | Return dict has path, status, changes keys |
| `test_process_dir_returns_list_of_dicts` | PASSED | Return is list of valid dicts; referenced paths exist |
| `test_empty_dir_returns_empty_list` | PASSED | Empty directory → empty list |
| `test_full_dry_run_on_fixtures` | PASSED | All 4 .md fixtures found; empty.md skipped; others dry_run |

### Unit tests (1 test)
| Test | Status | What it verifies |
|------|--------|------------------|
| `test_has_frontmatter` | PASSED | Correctly identifies presence/absence of YAML frontmatter |

---

## Test Environment

- All tests use `tempfile.mkdtemp()` with fixture copying — no real files are
  modified
- `work_dir` fixture copies `tests/fixtures/` → temp dir before each test,
  cleans up after
- Tests are isolated: each test gets a fresh copy of fixtures
- No network access required
- No external services needed
