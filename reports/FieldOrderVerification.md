# Field Order Verification Report

## Core Field Ordering: title → created → updated → tags → aliases

### Test 1: Core Fields Reordered
**Input order**: aliases, tags, updated, created, title
**Output order**: title, created, updated, tags, aliases
**Result**: PASSED — core fields reordered to prescribed sequence

### Test 2: Unknown Fields Preserve Original Order
**Input order**: status, title, priority, created, author, tags, reviewer
**Output order**: title, created, tags, status, priority, author, reviewer
**Result**: PASSED — unknowns kept original order (status < priority < author < reviewer) after core fields

### Test 3: Multi-line Fields with Ordering
**Input**: tags, created, title, description (multiline), status
**Output**: title, created, tags, description, status
**Multi-line content**: "First line of description", "Second line with special chars: ---", "Third line with [[wikilink]]" all preserved
**Result**: PASSED

### Test 4: No Forced Addition of updated/aliases
**Input fields**: title, created, tags, description
**Output**: no 'updated:' or 'aliases:' lines
**Result**: PASSED — fields not present in source are not added

### Test 5: Aliases After Tags
**Input order**: title, created, aliases, tags
**Output order**: title, created, tags, aliases
**Result**: PASSED — aliases (line after tags) verified by position comparison

### Test 6: Full Process Pipeline Integration
**Input**: mixed-order file with all 5 core fields + 2 custom fields
**Process**: parse → merge (adds ai, learning tags) → rebuild → write
**Output**: title → created → updated → tags → aliases → custom_field → another_custom
**Result**: PASSED — ordering survives full pipeline, default tags merged

## Regression Check: All 36 Original Tests

| Category | Tests | Status |
|----------|-------|--------|
| Bug 1: dry-run | 1 | PASSED |
| Bug 2: non-.md/.obsidian/.git | 2 | PASSED |
| Bug 3: code block protection | 2 | PASSED |
| Bug 4: frontmatter duplication | 2 | PASSED |
| Bug 5: tag duplication | 2 | PASSED |
| Bug 6: UTF-8 encoding | 2 | PASSED |
| Bug 7: empty files | 2 | PASSED |
| Bug 8: structured reports | 3 | PASSED |
| Integration: dry-run fixtures | 1 | PASSED |
| Unit: code blocks | 2 | PASSED |
| Unit: frontmatter/has | 1 | PASSED |
| Unit: wikilinks | 1 | PASSED |
| Frontmatter: YAML list tags | 2 | PASSED |
| Frontmatter: inline array tags | 2 | PASSED |
| Frontmatter: Chinese title | 2 | PASSED |
| Frontmatter: multi-line | 2 | PASSED |
| Frontmatter: no frontmatter | 1 | PASSED |
| Frontmatter: codeblock dashes | 2 | PASSED |
| Frontmatter: dry-run verify | 1 | PASSED |
| Frontmatter: created date | 2 | PASSED |
| Frontmatter: roundtrip | 1 | PASSED |
| **TOTAL (old)** | **36** | **ALL PASSED** |

## Final Tally
- Old tests: 36/36 PASSED
- New tests: 6/6 PASSED
- Total: 42/42 PASSED
- Verdict: **APPROVED**
