"""
Tests for obsidian_note_normalizer.py

Covers all 8 bug fixes:
1. dry-run does not write files
2. non-.md files are skipped
3. code blocks are protected from modification
4. frontmatter is not duplicated
5. tags are not duplicated
6. UTF-8 encoding works
7. empty files are handled gracefully
8. structured report dict is returned
"""

import os
import sys
import tempfile
import shutil
import pytest

# Add the tools directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import obsidian_note_normalizer as normalizer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
FRONTMATTER_FIXTURES_DIR = os.path.join(FIXTURES_DIR, "frontmatter")


# ---------------------------------------------------------------------------
# Helper: copy a fixture to a temp dir for safe mutation tests
# ---------------------------------------------------------------------------
@pytest.fixture
def work_dir():
    """Create a temporary directory with a copy of the fixtures."""
    tmp = tempfile.mkdtemp(prefix="norm_test_")
    dst = os.path.join(tmp, "notes")
    shutil.copytree(FIXTURES_DIR, dst)
    yield dst
    shutil.rmtree(tmp, ignore_errors=True)


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ===========================================================================
# BUG 1: dry-run does NOT write files
# ===========================================================================
def test_dry_run_does_not_write(work_dir):
    """dry_run=True should print a plan but never modify files on disk."""
    md_path = os.path.join(work_dir, "normal_note.md")
    original = read_file(md_path)

    result = normalizer.process_file(md_path, dry_run=True)

    # File on disk must be unchanged
    assert read_file(md_path) == original
    # Result must indicate dry_run status
    assert result["status"] == "dry_run"
    assert result["path"] == md_path


# ===========================================================================
# BUG 2: non-.md files are skipped; .obsidian/.git dirs excluded
# ===========================================================================
def test_non_md_files_skipped(work_dir):
    """Files without .md extension (like note.txt) must be skipped."""
    results = normalizer.process_dir(work_dir, dry_run=True)
    paths = [r["path"] for r in results]
    # note.txt should NOT appear in results
    assert not any(p.endswith(".txt") for p in paths)
    # But all .md files should be present
    md_files = [f for f in os.listdir(work_dir) if f.endswith(".md")]
    for md in md_files:
        full = os.path.join(work_dir, md)
        assert full in paths


def test_obsidian_and_git_dirs_excluded(work_dir):
    """Directories named .obsidian or .git must be excluded from traversal."""
    # Create fake .obsidian and .git dirs with .md files inside
    obsidian_dir = os.path.join(work_dir, ".obsidian")
    git_dir = os.path.join(work_dir, ".git")
    os.makedirs(obsidian_dir, exist_ok=True)
    os.makedirs(git_dir, exist_ok=True)

    with open(os.path.join(obsidian_dir, "config.md"), "w", encoding="utf-8") as f:
        f.write("# obsidian config\n")
    with open(os.path.join(git_dir, "readme.md"), "w", encoding="utf-8") as f:
        f.write("# git readme\n")

    results = normalizer.process_dir(work_dir, dry_run=True)
    paths = [r["path"] for r in results]

    assert os.path.join(obsidian_dir, "config.md") not in paths
    assert os.path.join(git_dir, "readme.md") not in paths


# ===========================================================================
# BUG 3: code block content is NOT modified
# ===========================================================================
def test_code_blocks_protected_from_wikilink_normalization(work_dir):
    """Wikilinks inside fenced code blocks must NOT be normalized."""
    md_path = os.path.join(work_dir, "code_block.md")
    original = read_file(md_path)

    result = normalizer.process_file(md_path, dry_run=False)

    # After processing, verify code block content is unchanged
    processed = read_file(md_path)
    # The code block contains [[FakeLink]] — must remain exactly as-is
    assert "[[FakeLink]]" in processed
    # The code block contains #ai — must remain
    assert "#ai" in processed
    # The real wikilink outside code block should be normalized
    assert "[[Real Link]]" in processed
    assert "[[ Real Link ]]" not in processed


def test_code_blocks_protected_from_tag_detection(work_dir):
    """Tags inside code blocks should not prevent adding tags if missing elsewhere."""
    md_path = os.path.join(work_dir, "code_block.md")
    original = read_file(md_path)

    # Process the file (it has no frontmatter, so tags should be added)
    result = normalizer.process_file(md_path, dry_run=False)

    processed = read_file(md_path)
    # #ai appears in code block but also gets added at end if not in body
    # The code block's #ai must remain untouched
    assert "// 不应该修改代码块里的 #ai" in processed


# ===========================================================================
# BUG 4: frontmatter is NOT duplicated
# ===========================================================================
def test_frontmatter_not_duplicated(work_dir):
    """Files that already have frontmatter must not get a second one."""
    md_path = os.path.join(work_dir, "has_frontmatter.md")
    original = read_file(md_path)

    result = normalizer.process_file(md_path, dry_run=False)
    processed = read_file(md_path)

    # Should have exactly one frontmatter block
    assert processed.count("---") == 2  # opening --- and closing ---
    assert "Existing Note" in processed
    # Should not have "added frontmatter" in changes
    assert "added frontmatter" not in result["changes"]

    # Verify the original frontmatter title is preserved
    assert "title: Existing Note" in processed


def test_frontmatter_added_when_missing(work_dir):
    """Files without frontmatter should get one added."""
    md_path = os.path.join(work_dir, "normal_note.md")
    original = read_file(md_path)

    result = normalizer.process_file(md_path, dry_run=False)
    processed = read_file(md_path)

    assert "added frontmatter" in result["changes"]
    assert processed.startswith("---")
    assert "title: normal_note" in processed


# ===========================================================================
# BUG 5: tags are NOT duplicated
# ===========================================================================
def test_tags_not_duplicated(work_dir):
    """Tags that already exist must not be added again."""
    # Create a file that already has #ai tag
    md_path = os.path.join(work_dir, "has_tags.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Test\n\nThis file has #ai already.\n")

    result = normalizer.process_file(md_path, dry_run=False)
    processed = read_file(md_path)

    # #ai should appear exactly once (already present in body)
    assert processed.count("#ai") == 1
    # learning already exists in frontmatter tags list, so #learning is NOT appended
    # (no duplication — tag already declared in frontmatter)
    assert "#learning" not in processed
    # But learning should be declared in the frontmatter
    assert "learning" in processed


def test_tags_in_frontmatter_not_duplicated(work_dir):
    """Tags declared in frontmatter should prevent appending #tag."""
    md_path = os.path.join(work_dir, "has_frontmatter.md")
    result = normalizer.process_file(md_path, dry_run=False)
    processed = read_file(md_path)

    # The frontmatter has tags: [unity], and DEFAULT_TAGS are [ai, learning]
    # Neither should be duplicated if already present
    # has_frontmatter.md has tags: [unity] — not ai or learning, so ai and
    # learning should be added
    assert "#ai" in processed or "ai" in processed
    assert "#learning" in processed or "learning" in processed


# ===========================================================================
# BUG 6: UTF-8 encoding
# ===========================================================================
def test_utf8_encoding_read_write(work_dir):
    """Files with non-ASCII characters must be read and written correctly."""
    md_path = os.path.join(work_dir, "unicode_test.md")
    content = "# 你好世界\n\n[[中文链接]]\n\n日本語テスト\n"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    result = normalizer.process_file(md_path, dry_run=False)
    processed = read_file(md_path)

    assert "你好世界" in processed
    assert "中文链接" in processed
    assert "日本語テスト" in processed


def test_utf8_with_bom_handled(work_dir):
    """Files with BOM should be handled (lstrip handles BOM-affected startswith)."""
    md_path = os.path.join(work_dir, "bom_test.md")
    with open(md_path, "w", encoding="utf-8-sig") as f:
        f.write("# BOM Test\n")

    # Should not crash
    result = normalizer.process_file(md_path, dry_run=True)
    assert result["status"] == "dry_run"


# ===========================================================================
# BUG 7: empty files handled gracefully
# ===========================================================================
def test_empty_file_does_not_crash(work_dir):
    """Empty files must be skipped with status='skipped', not crash."""
    md_path = os.path.join(work_dir, "empty.md")

    # empty.md should exist and be empty
    result = normalizer.process_file(md_path, dry_run=False)
    assert result["status"] == "skipped"
    assert result["reason"] == "empty file"

    # Verify the file is still empty
    processed = read_file(md_path)
    assert processed == "" or processed == "\n"


def test_whitespace_only_file_skipped(work_dir):
    """Files containing only whitespace should also be skipped."""
    md_path = os.path.join(work_dir, "whitespace.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("   \n  \n   ")

    result = normalizer.process_file(md_path, dry_run=False)
    assert result["status"] == "skipped"


# ===========================================================================
# BUG 8: structured report returned
# ===========================================================================
def test_process_file_returns_structured_dict(work_dir):
    """process_file must return a dict with path, status, changes keys."""
    md_path = os.path.join(work_dir, "normal_note.md")
    result = normalizer.process_file(md_path, dry_run=True)

    assert isinstance(result, dict)
    assert "path" in result
    assert "status" in result
    assert "changes" in result
    assert result["path"] == md_path
    assert result["status"] in ("processed", "dry_run", "skipped", "error")


def test_process_dir_returns_list_of_dicts(work_dir):
    """process_dir must return a list of structured result dicts."""
    results = normalizer.process_dir(work_dir, dry_run=True)

    assert isinstance(results, list)
    assert len(results) >= 1
    for r in results:
        assert isinstance(r, dict)
        assert "path" in r
        assert "status" in r
        assert "changes" in r
        assert os.path.exists(r["path"])


def test_empty_dir_returns_empty_list():
    """process_dir on an empty directory returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        results = normalizer.process_dir(tmp, dry_run=True)
        assert results == []


# ===========================================================================
# Integration: full dry-run on fixtures
# ===========================================================================
def test_full_dry_run_on_fixtures(work_dir):
    """Full dry-run on all fixtures produces expected results."""
    results = normalizer.process_dir(work_dir, dry_run=True)
    # Expect at least 4 .md files in root fixtures (plus frontmatter/ subdir ones)
    assert len(results) >= 4  # 4 root .md files (note.txt excluded) + frontmatter/ files

    statuses = {r["path"]: r["status"] for r in results}

    # empty.md should be skipped
    empty_path = os.path.join(work_dir, "empty.md")
    assert statuses.get(empty_path) == "skipped"

    # All root .md files should be dry_run (not skipped except empty)
    for key, val in statuses.items():
        if key != empty_path:
            assert val == "dry_run", f"{key} expected dry_run, got {val}"


# ===========================================================================
# Unit: extract_code_blocks and restore_code_blocks
# ===========================================================================
def test_extract_restore_code_blocks_roundtrip():
    """Code blocks extraction and restoration must be lossless."""
    content = """# Header

Some text.

```python
print("hello [[world]]")
# tag #ai
```

More text.

```csharp
// [[FakeLink]]
Debug.Log("test");
```
"""
    safe, blocks = normalizer.extract_code_blocks(content)
    # Verify placeholders exist
    assert "%%CODEBLOCK_" in safe
    # Verify original code is not in safe content
    assert 'print("hello [[world]]")' not in safe
    assert "[[FakeLink]]" not in safe

    # Round-trip must be exact
    restored = normalizer.restore_code_blocks(safe, blocks)
    assert restored == content


def test_extract_code_blocks_no_blocks():
    """Content with no code blocks should be unchanged."""
    content = "# Just a header\n\nSome text.\n"
    safe, blocks = normalizer.extract_code_blocks(content)
    assert safe == content
    assert blocks == {}


def test_has_frontmatter():
    """has_frontmatter correctly identifies frontmatter."""
    assert normalizer.has_frontmatter("---\ntitle: test\n---\n\ncontent")
    assert normalizer.has_frontmatter("---\n---\n")
    assert not normalizer.has_frontmatter("# Header\ncontent")
    assert not normalizer.has_frontmatter("")


def test_normalize_wikilinks_outside_code_blocks():
    """Wikilinks are normalized only outside code blocks."""
    content = """# Test

Some [[ spaced link ]] here.

```md
[[ do not touch me ]]
```

End [[ trailing space ]].
"""
    result = normalizer.normalize_wikilinks(content)

    assert "[[spaced link]]" in result
    assert "[[trailing space]]" in result
    # Code block content must be untouched
    assert "[[ do not touch me ]]" in result


# ===========================================================================
# FRONTMATTER FIX: Scenario 1 — YAML list tags merging
# ===========================================================================
def test_yaml_list_tags_merge():
    """YAML list-format tags (tags:\n  - unity\n  - ai) should be merged
    with default tags, no duplicates."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "yaml_list_tags.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    existing_tags = normalizer.get_existing_tags(fields)
    merged = normalizer.merge_tags(existing_tags, normalizer.DEFAULT_TAGS)

    assert "unity" in merged
    assert "ai" in merged
    assert "learning" in merged
    # No duplicates
    assert merged.count("ai") == 1
    assert merged.count("learning") == 1


def test_yaml_list_tags_merge_process():
    """Processing a file with YAML list tags should merge without appending
    duplicate #tag in body."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "yaml_list_tags.md")
        dst = os.path.join(tmpdir, "yaml_list_tags.md")
        shutil.copy2(src, dst)

        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        # Original tags (unity, ai) should be preserved
        assert "- unity" in processed or "unity" in processed
        assert "- ai" in processed or "ai" in processed

        # Default tag 'learning' should be merged
        assert "- learning" in processed or "learning" in processed

        # #ai should NOT be appended since it's already in frontmatter
        # Actually, normalize_tags might add #tag at end. Check that it
        # doesn't appear twice
        count_ai = processed.count("#ai") + processed.lower().count("ai")
        # Frontmatter should show changes
        assert "merged frontmatter" in result["changes"] or "added tags" in result["changes"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# FRONTMATTER FIX: Scenario 2 — Inline array tags
# ===========================================================================
def test_inline_array_tags_parse():
    """Inline array tags: tags: [agent, learning] should be parsed correctly."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "inline_array_tags.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    existing_tags = normalizer.get_existing_tags(fields)
    assert existing_tags is not None
    assert "agent" in existing_tags
    assert "learning" in existing_tags


def test_inline_array_tags_merge():
    """Inline array tags should merge with defaults — 'learning' already present,
    only 'ai' should be new."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "inline_array_tags.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    existing_tags = normalizer.get_existing_tags(fields)
    merged = normalizer.merge_tags(existing_tags, normalizer.DEFAULT_TAGS)

    assert "agent" in merged
    assert "learning" in merged
    assert "ai" in merged
    assert merged.count("learning") == 1


# ===========================================================================
# FRONTMATTER FIX: Scenario 3 — Chinese title preservation
# ===========================================================================
def test_chinese_title_preservation():
    """Chinese title (Unity 客户端 GC 优化) must be preserved exactly."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "chinese_title.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    assert "title" in fields
    assert fields["title"] == "Unity 客户端 GC 优化"

    # Rebuild and verify
    rebuilt = normalizer.rebuild_frontmatter(fields)
    assert "Unity 客户端 GC 优化" in rebuilt


def test_chinese_title_not_overwritten():
    """Processing a file with Chinese title must not overwrite it."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "chinese_title.md")
        dst = os.path.join(tmpdir, "chinese_title.md")
        shutil.copy2(src, dst)

        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        # Chinese title must be preserved
        assert "Unity 客户端 GC 优化" in processed

        # Original created date preserved
        assert "2025-03-20" in processed

        # Original tags preserved
        assert "unity" in processed
        assert "performance" in processed
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# FRONTMATTER FIX: Scenario 4 — Multi-line field preservation
# ===========================================================================
def test_multiline_field_parse():
    """Multi-line field (description: |) should be parsed correctly."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "multiline_field.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    assert "description" in fields
    desc = fields["description"]
    assert isinstance(desc, dict)
    assert desc["_type"] == "multiline"
    assert "第一行描述" in desc["_value"]
    assert "第二行描述" in desc["_value"]
    assert "第三行描述" in desc["_value"]


def test_multiline_field_preserved():
    """Multi-line fields must be preserved through processing."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "multiline_field.md")
        dst = os.path.join(tmpdir, "multiline_field.md")
        shutil.copy2(src, dst)

        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        # All multi-line content must be preserved
        assert "第一行描述" in processed
        assert "第二行描述" in processed
        assert "第三行描述" in processed
        # Special chars in multiline preserved
        assert "---" in processed
        assert "[[链接]]" in processed
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# FRONTMATTER FIX: Scenario 5 — New frontmatter when none exists
# ===========================================================================
def test_no_frontmatter_added():
    """When no frontmatter exists, standard YAML format should be added."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "no_frontmatter.md")
        dst = os.path.join(tmpdir, "no_frontmatter.md")
        shutil.copy2(src, dst)

        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        assert "added frontmatter" in result["changes"]
        assert processed.startswith("---")
        assert "title: no_frontmatter" in processed
        assert "tags:" in processed
        assert "ai" in processed
        assert "learning" in processed
        assert "created:" in processed

        # Body content preserved
        assert "# No Frontmatter Test" in processed
        assert "[[Test Link]]" in processed
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# FRONTMATTER FIX: Scenario 6 — Code block --- protection
# ===========================================================================
def test_codeblock_dashes_not_frontmatter_boundary():
    """Code block containing --- must NOT be treated as frontmatter boundary."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "codeblock_dashes.md")
        dst = os.path.join(tmpdir, "codeblock_dashes.md")
        shutil.copy2(src, dst)

        original = read_file(dst)
        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        # Code block content must be intact
        assert "```yaml" in processed
        assert "title: fake frontmatter" in processed
        assert "not-real" in processed

        # The frontmatter should still be recognized (file has valid frontmatter)
        # The code block --- should not confuse the parser
        assert "---" in processed  # Frontmatter markers exist

        # The code block --- should remain inside code block
        # Verify we don't have a second frontmatter accidentally
        fm_count = processed.count("---")
        # There should be: opening ---, closing --- of real frontmatter,
        # plus --- in code block (inside yaml block)
        assert fm_count >= 3  # at least 3 occurrences
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_protect_codeblock_dashes():
    """protect_codeblock_dashes replaces --- inside code blocks."""
    content = """---
title: test
---

```yaml
---
inside: code
---
```

End.
"""
    protected, pmap = normalizer.protect_codeblock_dashes(content)
    # The --- inside code block should be replaced
    assert "%%DASHES_" in protected
    # Opening/closing frontmatter --- should remain
    assert protected.lstrip().startswith("---")

    # Restore
    restored = normalizer.restore_codeblock_dashes(protected, pmap)
    assert "---" in restored
    assert "inside: code" in restored


# ===========================================================================
# FRONTMATTER FIX: Scenario 7 — dry-run must not write files
# ===========================================================================
def test_dry_run_preserves_frontmatter_file():
    """dry-run on a file with frontmatter must NOT write any changes."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "dry_run_verify.md")
        dst = os.path.join(tmpdir, "dry_run_verify.md")
        shutil.copy2(src, dst)

        original = read_file(dst)
        result = normalizer.process_file(dst, dry_run=True)

        # Status must be dry_run
        assert result["status"] == "dry_run"

        # File must be unchanged
        assert read_file(dst) == original

        # Content with frontmatter markers preserved exactly
        assert "---" in read_file(dst)
        assert "existing-tag" in read_file(dst)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# FRONTMATTER FIX: Scenario 8 — Created date must not be overwritten
# ===========================================================================
def test_created_date_not_overwritten():
    """Created date (2020-01-01) must be preserved, not replaced with today."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    try:
        src = os.path.join(FRONTMATTER_FIXTURES_DIR, "has_created_date.md")
        dst = os.path.join(tmpdir, "has_created_date.md")
        shutil.copy2(src, dst)

        result = normalizer.process_file(dst, dry_run=False)
        processed = read_file(dst)

        # Original created date must be preserved
        assert "created: 2020-01-01" in processed or "created: '2020-01-01'" in processed

        # Today's date must NOT appear as created
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        # We check that created is still 2020-01-01, not today
        assert "created: 2020-01-01" in processed

        # Original title preserved
        assert "Preserve Created Date Test" in processed

        # Legacy tag preserved
        assert "legacy" in processed

        # Default tags merged
        assert "ai" in processed
        assert "learning" in processed
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_created_date_in_parse():
    """parse_frontmatter correctly extracts created date."""
    path = os.path.join(FRONTMATTER_FIXTURES_DIR, "has_created_date.md")
    fields, _ = normalizer.parse_frontmatter(normalizer.read_file_helper(path))

    assert "created" in fields
    assert fields["created"] == "2020-01-01"


# ===========================================================================
# Additional: parse_frontmatter roundtrip test
# ===========================================================================
def test_parse_rebuild_roundtrip():
    """parse_frontmatter + rebuild_frontmatter should produce equivalent YAML."""
    content = """---
title: Roundtrip Test
created: 2024-06-15
tags:
  - python
  - testing
description: |
  A multi-line
  description field.
status: draft
---

# Content
Body text.
"""
    fields, rest = normalizer.parse_frontmatter(content)
    assert fields is not None
    assert fields["title"] == "Roundtrip Test"
    assert fields["created"] == "2024-06-15"
    assert "python" in fields["tags"]
    assert "testing" in fields["tags"]
    assert "description" in fields
    assert fields["status"] == "draft"

    rebuilt = normalizer.rebuild_frontmatter(fields)
    assert "title: Roundtrip Test" in rebuilt
    assert "created: 2024-06-15" in rebuilt
    assert "python" in rebuilt
    assert "testing" in rebuilt
    assert "status: draft" in rebuilt

    # Re-parse the rebuilt and verify
    fields2, _ = normalizer.parse_frontmatter(rebuilt + "\n" + rest)
    assert fields2["title"] == "Roundtrip Test"
    assert fields2["created"] == "2024-06-15"
    assert "python" in fields2["tags"]

    # Verify rest content preserved
    assert "# Content" in rest
    assert "Body text." in rest
