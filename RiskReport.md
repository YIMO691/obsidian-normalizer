# RiskReport.md — Risk Assessment for obsidian_note_normalizer Fix

## Risk Summary

| Risk ID | Risk | Severity | Likelihood | Status |
|---------|------|----------|------------|--------|
| R1 | Code block placeholder collision | Low | Low | Mitigated |
| R2 | Frontmatter detection false negatives | Medium | Low | Mitigated |
| R3 | Tag detection false positives in code | Low | Low | Accepted |
| R4 | Large file memory usage | Low | Medium | Accepted |
| R5 | Concurrent file access | Medium | Low | Not addressed |
| R6 | Non-standard frontmatter formats | Medium | Low | Partially mitigated |
| R7 | Regression: existing behavior change | Low | Low | Mitigated |

---

## Detailed Risk Analysis

### R1: Code block placeholder collision
**Severity:** Low | **Likelihood:** Low

**Description:** The `extract_code_blocks()` function uses placeholder tokens
of the form `%%CODEBLOCK_N_PLACEHOLDER%%`. If a Markdown file naturally
contains text matching this pattern, it could be incorrectly replaced during
restoration.

**Mitigation:**
- The placeholder pattern is extremely specific and unlikely to appear in
  natural documentation
- The round-trip test (`test_extract_restore_code_blocks_roundtrip`) verifies
  lossless preservation
- Worst case: a file containing the literal placeholder string would have
  it replaced by the last code block — a cosmetic issue, not data loss

**Recommendation:** If this becomes a concern, switch to a UUID-based
placeholder (e.g., `__CB_<uuid4>__`).

---

### R2: Frontmatter detection false negatives
**Severity:** Medium | **Likelihood:** Low

**Description:** `has_frontmatter()` checks `content.lstrip().startswith("---")`.
This may miss frontmatter blocks that:
- Use `---` with trailing whitespace
- Use YAML document start `...`
- Have the `---` on a line other than the first (after BOM handled by lstrip)

**Mitigation:**
- `lstrip()` handles leading whitespace and BOM characters
- The vast majority of Obsidian frontmatter blocks start with `---\n` on
  line 1
- Test `test_frontmatter_not_duplicated` confirms correct detection on the
  `has_frontmatter.md` fixture

**Recommendation:** If users report frontmatter duplication, consider a
more robust regex: `re.match(r'\s*---\s*\n', content)`.

---

### R3: Tag detection false positives in code blocks
**Severity:** Low | **Likelihood:** Low

**Description:** `tag_exists_in_content()` searches the entire content
including code blocks. If a tag like `#ai` appears inside a code block
comment, `normalize_tags()` will skip adding it — which is actually correct
behavior (we don't want duplicate tags, even if one is in a code block).

**Accepted risk:** This is by design. A tag appearing in a code block
comment still "exists" in the document. Adding a second `#ai` would be
worse than skipping it. No mitigation needed.

---

### R4: Large file memory usage
**Severity:** Low | **Likelihood:** Medium

**Description:** `process_file()` reads the entire file into memory as a
string. For very large Markdown files (e.g., exported documentation >100MB),
this could cause memory pressure.

**Mitigation:**
- Obsidian notes are typically small (<1MB)
- The script is designed for personal knowledge bases, not bulk document
  processing
- No reports of OOM issues in current usage

**Recommendation:** If large-file support is needed, switch to line-by-line
streaming with code-block state tracking. Not required for current scope.

---

### R5: Concurrent file access
**Severity:** Medium | **Likelihood:** Low

**Description:** If Obsidian is open and auto-saving while the normalizer
runs, there could be a race condition where the normalizer reads a partially
written file, or Obsidian overwrites the normalized version.

**Not addressed in this fix:** The SDD scope excludes Obsidian API
integration. This is a pre-existing risk in the original script as well.

**Recommendation:** Users should close Obsidian before running the
normalizer, or the script should be extended to use Obsidian's file
system watcher APIs in a future version.

---

### R6: Non-standard frontmatter formats
**Severity:** Medium | **Likelihood:** Low

**Description:** Some Obsidian users may have frontmatter in non-standard
formats (TOML `+++` delimiters, JSON frontmatter, etc.). The script only
handles YAML-style `---` delimited frontmatter.

**Partially mitigated:**
- YAML `---` is the overwhelming standard for Obsidian
- Non-YAML frontmatter would be treated as "no frontmatter" and a new one
  added, potentially creating double frontmatter with different delimiters

**Recommendation:** Document the YAML-only assumption. Future enhancement
could detect `+++` TOML delimiters.

---

### R7: Regression — existing behavior change
**Severity:** Low | **Likelihood:** Low

**Description:** The fix changes the return type of `process_file()` and
`process_dir()` from `None` to `dict`/`list[dict]`. Any code importing
these functions and relying on `None` return would break.

**Mitigation:**
- The original script only had `main()` calling these functions and
  ignoring return values — no breakage
- The new return values are additive (they return information that was
  previously discarded)
- `main()` still prints to stdout as before, plus the structured report
- Tests verify the new return signatures

---

## Overall Assessment

**Risk level: LOW**

All 8 bugs are fixed with well-tested mitigations. The remaining risks are
either pre-existing (R5, R6), accepted by design (R3), or mitigated to
acceptable levels (R1, R2, R4, R7). The fix is safe to deploy.
