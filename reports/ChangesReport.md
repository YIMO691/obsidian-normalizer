# Code Changes Report

## File: tools/obsidian_note_normalizer.py

### Change Location: `rebuild_frontmatter()` function, lines 250-258

### Before (old code):
```python
    # Define preferred order
    priority_keys = ['title', 'created', 'tags']
    ordered_keys = []
    for k in priority_keys:
        if k in fields:
            ordered_keys.append(k)
    # Remaining keys sorted alphabetically
    remaining = sorted([k for k in fields if k not in priority_keys])
    ordered_keys.extend(remaining)
```

### After (new code):
```python
    # Define preferred order: core fields first, then unknown fields in original order
    priority_keys = ['title', 'created', 'updated', 'tags', 'aliases']
    ordered_keys = []
    for k in priority_keys:
        if k in fields:
            ordered_keys.append(k)
    # Remaining keys preserve original insertion order (Python 3.7+ dicts are ordered)
    remaining = [k for k in fields if k not in priority_keys]
    ordered_keys.extend(remaining)
```

### Changes Explained:
1. Added `'updated'` and `'aliases'` to `priority_keys` list
2. Removed `sorted()` call — unknown fields now use Python 3.7+ dict insertion order (original document order)
3. Updated comments for clarity

## File: tests/test_obsidian_note_normalizer.py

### Addition: 6 new test functions appended after line 772

No existing tests were modified or deleted. All 36 original tests pass unchanged.

### New Tests:
1. **test_field_order_core_fields_reordered** (unit test)
   - Creates frontmatter with core fields in random order
   - Verifies rebuilt output has title → created → updated → tags → aliases

2. **test_field_order_unknown_fields_preserve_original_order** (unit test)
   - Creates frontmatter with mixed core and unknown fields
   - Verifies unknown fields (status, priority, author, reviewer) keep original order after core fields

3. **test_field_order_multiline_field_preserved_with_ordering** (unit test)
   - Creates frontmatter with multi-line description field
   - Verifies multiline content preserved + correct ordering

4. **test_field_order_updated_and_aliases_not_added** (unit test)
   - Creates frontmatter without updated/aliases
   - Verifies they are NOT added by rebuild_frontmatter

5. **test_field_order_aliases_after_tags** (unit test)
   - Creates frontmatter with aliases before tags in source
   - Verifies aliases appears after tags in output

6. **test_field_order_full_process_preserves_order** (integration test)
   - Creates temp file, runs full process_file pipeline
   - Verifies ordering survives merge_frontmatter + rebuild_frontmatter + write
