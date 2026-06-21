# Test Report: Frontmatter Field Ordering

## Test Execution

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\20544\Desktop\obsidian-normalizer
collecting ... collected 42 items

tests/test_obsidian_note_normalizer.py::test_dry_run_does_not_write PASSED [  2%]
tests/test_obsidian_note_normalizer.py::test_non_md_files_skipped PASSED [  4%]
tests/test_obsidian_note_normalizer.py::test_obsidian_and_git_dirs_excluded PASSED [  7%]
tests/test_obsidian_note_normalizer.py::test_code_blocks_protected_from_wikilink_normalization PASSED [  9%]
tests/test_obsidian_note_normalizer.py::test_code_blocks_protected_from_tag_detection PASSED [ 11%]
tests/test_obsidian_note_normalizer.py::test_frontmatter_not_duplicated PASSED [ 14%]
tests/test_obsidian_note_normalizer.py::test_frontmatter_added_when_missing PASSED [ 16%]
tests/test_obsidian_note_normalizer.py::test_tags_not_duplicated PASSED  [ 19%]
tests/test_obsidian_note_normalizer.py::test_tags_in_frontmatter_not_duplicated PASSED [ 21%]
tests/test_obsidian_note_normalizer.py::test_utf8_encoding_read_write PASSED [ 23%]
tests/test_obsidian_note_normalizer.py::test_utf8_with_bom_handled PASSED [ 26%]
tests/test_obsidian_note_normalizer.py::test_empty_file_does_not_crash PASSED [ 28%]
tests/test_obsidian_note_normalizer.py::test_whitespace_only_file_skipped PASSED [ 30%]
tests/test_obsidian_note_normalizer.py::test_process_file_returns_structured_dict PASSED [ 33%]
tests/test_obsidian_note_normalizer.py::test_process_dir_returns_list_of_dicts PASSED [ 35%]
tests/test_obsidian_note_normalizer.py::test_empty_dir_returns_empty_list PASSED [ 38%]
tests/test_obsidian_note_normalizer.py::test_full_dry_run_on_fixtures PASSED [ 40%]
tests/test_obsidian_note_normalizer.py::test_extract_restore_code_blocks_roundtrip PASSED [ 42%]
tests/test_obsidian_note_normalizer.py::test_extract_code_blocks_no_blocks PASSED [ 45%]
tests/test_obsidian_note_normalizer.py::test_has_frontmatter PASSED      [ 47%]
tests/test_obsidian_note_normalizer.py::test_normalize_wikilinks_outside_code_blocks PASSED [ 50%]
tests/test_obsidian_note_normalizer.py::test_yaml_list_tags_merge PASSED [ 52%]
tests/test_obsidian_note_normalizer.py::test_yaml_list_tags_merge_process PASSED [ 54%]
tests/test_obsidian_note_normalizer.py::test_inline_array_tags_parse PASSED [ 57%]
tests/test_obsidian_note_normalizer.py::test_inline_array_tags_merge PASSED [ 59%]
tests/test_obsidian_note_normalizer.py::test_chinese_title_preservation PASSED [ 61%]
tests/test_obsidian_note_normalizer.py::test_chinese_title_not_overwritten PASSED [ 64%]
tests/test_obsidian_note_normalizer.py::test_multiline_field_parse PASSED [ 66%]
tests/test_obsidian_note_normalizer.py::test_multiline_field_preserved PASSED [ 69%]
tests/test_obsidian_note_normalizer.py::test_no_frontmatter_added PASSED [ 71%]
tests/test_obsidian_note_normalizer.py::test_codeblock_dashes_not_frontmatter_boundary PASSED [ 73%]
tests/test_obsidian_note_normalizer.py::test_protect_codeblock_dashes PASSED [ 76%]
tests/test_obsidian_note_normalizer.py::test_dry_run_preserves_frontmatter_file PASSED [ 78%]
tests/test_obsidian_note_normalizer.py::test_created_date_not_overwritten PASSED [ 80%]
tests/test_obsidian_note_normalizer.py::test_created_date_in_parse PASSED [ 83%]
tests/test_obsidian_note_normalizer.py::test_parse_rebuild_roundtrip PASSED [ 85%]
tests/test_obsidian_note_normalizer.py::test_field_order_core_fields_reordered PASSED [ 88%]
tests/test_obsidian_note_normalizer.py::test_field_order_unknown_fields_preserve_original_order PASSED [ 90%]
tests/test_obsidian_note_normalizer.py::test_field_order_multiline_field_preserved_with_ordering PASSED [ 92%]
tests/test_obsidian_note_normalizer.py::test_field_order_updated_and_aliases_not_added PASSED [ 95%]
tests/test_obsidian_note_normalizer.py::test_field_order_aliases_after_tags PASSED [ 97%]
tests/test_obsidian_note_normalizer.py::test_field_order_full_process_preserves_order PASSED [100%]

============================= 42 passed in 0.70s ==============================
```

## Results

- **Total tests: 42**
- **Passed: 42**
- **Failed: 0**
- **Old tests preserved: 36/36**
- **New tests: 6**
- **Verdict: APPROVED**
