import os
import re
import argparse
from datetime import datetime


DEFAULT_TAGS = ["ai", "learning"]


def read_file_helper(path):
    """Helper to read a file with UTF-8 encoding. Used by tests."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def protect_codeblock_dashes(content):
    """
    Replace `---` lines inside fenced code blocks with placeholders
    so they are not mistaken for frontmatter boundaries.
    Returns (processed_content, placeholder_map).
    """
    PLACEHOLDER = "%%DASHES_{}_PLACEHOLDER%%"
    placeholder_map = {}
    counter = [0]

    def replace_dashes(match):
        block = match.group(0)
        idx = counter[0]
        counter[0] += 1
        ph = PLACEHOLDER.format(idx)
        # Replace all `---` lines in the block content with placeholders,
        # but keep the ``` fences intact
        inner = block[3:-3]  # strip ``` fences
        inner_protected = re.sub(r'^---\s*$', lambda m: '%%DASHES_INLINE_{}%%'.format(counter[0]), inner, flags=re.MULTILINE)
        counter[0] += 1
        placeholder_map[ph] = '```' + inner_protected + '```'
        return ph

    # Match fenced code blocks: ``` ... ```
    protected = re.sub(r'```[\s\S]*?```', replace_dashes, content)
    return protected, placeholder_map


def restore_codeblock_dashes(content, placeholder_map):
    """Restore placeholders back, converting inline dash placeholders to actual ---."""
    for ph, block in placeholder_map.items():
        # Restore inline dash placeholders inside the block
        block_restored = re.sub(r'%%DASHES_INLINE_\d+%%', '---', block)
        content = content.replace(ph, block_restored)
    # Also handle any remaining inline placeholders outside blocks (shouldn't exist)
    content = re.sub(r'%%DASHES_INLINE_\d+%%', '---', content)
    return content


def has_frontmatter(content):
    """Check if content starts with YAML frontmatter (--- delimiter).
    Protects code-block dashes first to avoid false positives."""
    # Protect code blocks first so --- inside them isn't mistaken
    safe_content, _ = protect_codeblock_dashes(content)
    return safe_content.lstrip('\ufeff').startswith("---")


def extract_code_blocks(content):
    """
    Extract fenced code blocks from content, replacing them with placeholders.
    Returns (processed_content, blocks_dict) where blocks_dict maps placeholder -> original block.
    """
    placeholder_pattern = "%%CODEBLOCK_{}_PLACEHOLDER%%"
    blocks = {}
    counter = [0]

    def replace_block(match):
        idx = counter[0]
        placeholder = placeholder_pattern.format(idx)
        blocks[placeholder] = match.group(0)
        counter[0] += 1
        return placeholder

    # Match fenced code blocks: ``` ... ```
    processed = re.sub(r"```[\s\S]*?```", replace_block, content)
    return processed, blocks


def restore_code_blocks(content, blocks):
    """Restore code block placeholders back to original blocks."""
    for placeholder, block in blocks.items():
        content = content.replace(placeholder, block)
    return content


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from content.
    Returns (fields_dict, rest_of_content) or (None, content) if no frontmatter.

    Handles:
      - Simple key: value
      - Inline arrays: tags: [a, b, c]
      - List format: tags:\n  - a\n  - b
      - Multi-line literal: description: |\n  line1\n  line2
      - Quoted strings: title: "Hello World"
    """
    # Protect code-block dashes before parsing
    safe_content, dash_map = protect_codeblock_dashes(content)

    # Strip BOM
    stripped = safe_content.lstrip('\ufeff')

    if not stripped.startswith('---'):
        return None, content

    lines = stripped.split('\n')
    if len(lines) < 2:
        return None, content

    # Line 0 must be ---
    if lines[0].strip() != '---':
        return None, content

    # Find closing --- (must be a line containing only ---)
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            closing_idx = i
            break

    if closing_idx is None:
        return None, content

    # Extract YAML lines (between the two --- markers)
    yaml_lines = lines[1:closing_idx]

    # Build the rest of content after frontmatter
    rest_lines = lines[closing_idx + 1:]
    rest = '\n'.join(rest_lines)

    # Restore code-block dashes in the rest
    rest = restore_codeblock_dashes(rest, dash_map)

    # Parse YAML fields
    fields = {}
    current_key = None
    current_list = None
    current_multiline = None
    multiline_style = None  # '|' or '>'

    for line in yaml_lines:
        # If we're collecting a multiline literal block
        if current_multiline is not None:
            if line and (line.startswith('  ') or line.startswith('\t') or
                         (line.strip() and multiline_style == '>')):
                # For | style, preserve indented lines as-is
                # For > style, fold lines (but we store raw for now)
                if multiline_style == '|':
                    current_multiline.append(line[2:] if line.startswith('  ') else line)
                else:
                    current_multiline.append(line.strip())
                continue
            else:
                # End of multiline block
                fields[current_key] = {
                    '_type': 'multiline',
                    '_style': multiline_style,
                    '_value': '\n'.join(current_multiline),
                }
                current_multiline = None
                current_key = None
                multiline_style = None
                # Fall through to process this line

        # If we're collecting a list
        if current_list is not None:
            list_match = re.match(r'^\s+-\s+(.*)', line)
            if list_match:
                item = list_match.group(1).strip()
                # Strip quotes
                if (item.startswith('"') and item.endswith('"')) or \
                   (item.startswith("'") and item.endswith("'")):
                    item = item[1:-1]
                current_list.append(item)
                continue
            else:
                # End of list
                fields[current_key] = current_list
                current_list = None
                current_key = None
                # Fall through to process this line

        # Empty line or comment
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Try to match key: value
        m = re.match(r'^(\w[\w-]*)\s*:\s*(.*)', line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()

            if value in ('|', '|-', '>', '>-'):
                # Multi-line literal or folded block scalar
                current_key = key
                current_multiline = []
                multiline_style = value[0]  # '|' or '>'
                continue
            elif value == '':
                # Could be start of a list
                current_key = key
                current_list = []
                continue
            elif value.startswith('[') and value.endswith(']'):
                # Inline array: [a, b, c]
                items_str = value[1:-1]
                if items_str.strip():
                    items = [s.strip().strip("'\"").strip() for s in items_str.split(',')]
                    items = [i for i in items if i]  # Remove empty strings
                else:
                    items = []
                fields[key] = items
                continue
            else:
                # Simple string value - strip surrounding quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                fields[key] = value
                continue

    # Close any still-open collectors
    if current_list is not None and current_key is not None:
        fields[current_key] = current_list
    if current_multiline is not None and current_key is not None:
        fields[current_key] = {
            '_type': 'multiline',
            '_style': multiline_style or '|',
            '_value': '\n'.join(current_multiline),
        }

    return fields, rest


def rebuild_frontmatter(fields):
    """
    Rebuild YAML frontmatter string from a fields dictionary.
    Preserves order: title, created, tags, then remaining fields alphabetically.
    Multi-line fields are emitted as literal block scalars (|).
    List fields are emitted in YAML list format.
    """
    lines = ['---']

    # Define preferred order: core fields first, then unknown fields in original order
    priority_keys = ['title', 'created', 'updated', 'tags', 'aliases']
    ordered_keys = []
    for k in priority_keys:
        if k in fields:
            ordered_keys.append(k)
    # Remaining keys preserve original insertion order (Python 3.7+ dicts are ordered)
    remaining = [k for k in fields if k not in priority_keys]
    ordered_keys.extend(remaining)

    for key in ordered_keys:
        value = fields[key]

        if isinstance(value, dict) and value.get('_type') == 'multiline':
            # Multi-line literal block
            style = value.get('_style', '|')
            lines.append(f'{key}: {style}')
            for vline in value['_value'].split('\n'):
                lines.append(f'  {vline}')
        elif isinstance(value, list):
            # List tags
            if not value:
                lines.append(f'{key}: []')
            else:
                lines.append(f'{key}:')
                for item in value:
                    # If item contains special chars, quote it
                    if any(c in item for c in ['"', "'", ':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
                        lines.append(f'  - "{item}"')
                    else:
                        lines.append(f'  - {item}')
        elif isinstance(value, str):
            # Check if value needs quoting (contains colon, hash, etc.)
            if ':' in value or value.startswith('"') or value.startswith("'") or '#' in value:
                # Use double quotes, escape internal double quotes
                escaped = value.replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f'{key}: {value}')
        else:
            # Fallback
            lines.append(f'{key}: {value}')

    lines.append('---')
    return '\n'.join(lines) + '\n'


def merge_tags(existing_tags, default_tags):
    """
    Merge default tags into existing tags list, no duplicates.
    Returns the merged list (existing order preserved, new tags appended).
    """
    result = list(existing_tags) if existing_tags else []
    for tag in default_tags:
        if tag not in result:
            result.append(tag)
    return result


def get_existing_tags(fields):
    """Extract tags list from parsed frontmatter fields."""
    tags_val = fields.get('tags', None)
    if tags_val is None:
        return None
    if isinstance(tags_val, list):
        return [str(t) for t in tags_val]
    if isinstance(tags_val, str):
        # Could be a comma-separated string or single tag
        return [t.strip() for t in tags_val.split(',') if t.strip()]
    return None


def merge_frontmatter(content, title, default_tags):
    """
    Main frontmatter merging function.

    If no frontmatter: add standard frontmatter with title, created, tags.
    If frontmatter exists: parse it, merge tags, preserve title/created/multiline,
    and rebuild.

    Returns (new_content, changes_list).
    """
    changes = []
    fields, rest = parse_frontmatter(content)

    if fields is None:
        # No frontmatter — add standard one
        new_fm = {
            'title': title,
            'created': datetime.now().strftime('%Y-%m-%d'),
            'tags': list(default_tags),
        }
        fm_block = rebuild_frontmatter(new_fm)
        new_content = fm_block + '\n' + rest
        changes.append("added frontmatter")
        return new_content, changes

    # Frontmatter exists — merge
    had_changes = False

    # Preserve title — do NOT overwrite
    if 'title' not in fields:
        fields['title'] = title
        had_changes = True

    # Preserve created — do NOT overwrite
    if 'created' not in fields:
        fields['created'] = datetime.now().strftime('%Y-%m-%d')
        had_changes = True

    # Merge tags
    existing_tags = get_existing_tags(fields)
    if existing_tags is None:
        fields['tags'] = list(default_tags)
        had_changes = True
    else:
        merged = merge_tags(existing_tags, default_tags)
        if merged != existing_tags:
            fields['tags'] = merged
            had_changes = True

    if had_changes:
        fm_block = rebuild_frontmatter(fields)
        new_content = fm_block + '\n' + rest
        changes.append("merged frontmatter")
        return new_content, changes
    else:
        # No changes needed in frontmatter
        return content, changes


def add_frontmatter(content, title):
    """
    Add YAML frontmatter if not already present.
    Bug 4 fix: check has_frontmatter before adding.
    """
    if has_frontmatter(content):
        return content
    frontmatter = f"""---
title: {title}
created: {datetime.now().strftime('%Y-%m-%d')}
tags: [{', '.join(DEFAULT_TAGS)}]
---
"""
    return frontmatter + content


def tag_exists_in_content(content, tag):
    """Check if a tag already exists in content (as #tag or in frontmatter)."""
    if f"#{tag}" in content:
        return True
    # Check if tag appears in frontmatter tags list (e.g., tags: [ai, learning] or tags:\n  - ai)
    if re.search(rf"tags:\s*\[.*\b{re.escape(tag)}\b.*\]", content):
        return True
    if re.search(rf"^\s*- {re.escape(tag)}\s*$", content, re.MULTILINE):
        return True
    return False


def normalize_tags(content):
    """
    Add DEFAULT_TAGS as #tag at end of content if not already present.
    Bug 5 fix: check tag existence before adding.
    Bug 3 fix: code blocks are protected (tags only appends at end, but we check
    existence in full content including code blocks which is correct — we don't
    want to add a tag if it already appears anywhere).
    """
    result = content
    for tag in DEFAULT_TAGS:
        if not tag_exists_in_content(result, tag):
            result += f"\n#{tag}"
    return result


def normalize_wikilinks(content):
    """
    Normalize whitespace inside [[wikilinks]].
    Bug 3 fix: code blocks are extracted, protected, then restored after normalization.
    """
    # Extract code blocks to protect them
    safe_content, blocks = extract_code_blocks(content)

    # Normalize wikilinks in the safe content (outside code blocks)
    safe_content = re.sub(
        r"\[\[(.*?)\]\]",
        lambda m: f"[[{m.group(1).strip()}]]",
        safe_content,
    )

    # Restore code blocks
    return restore_code_blocks(safe_content, blocks)


def process_file(path, dry_run=False):
    """
    Process a single markdown file.
    Returns a structured result dict.
    Bug 1 fix: dry_run prevents writing.
    Bug 6 fix: UTF-8 encoding.
    Bug 7 fix: handle empty files.
    Bug 8 fix: return structured result.
    """
    # Bug 6 fix: explicit UTF-8 encoding
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    title = os.path.splitext(os.path.basename(path))[0]

    # Bug 7 fix: handle empty files gracefully
    if not content.strip():
        result = {
            "path": path,
            "status": "skipped",
            "reason": "empty file",
            "changes": [],
        }
        if dry_run:
            print(f"[DRY-RUN] Would skip empty file: {path}")
        else:
            print(f"Skipped (empty): {path}")
        return result

    changes = []
    new_content = content

    # Merge frontmatter (handles both add and update)
    new_content, fm_changes = merge_frontmatter(new_content, title, DEFAULT_TAGS)
    changes.extend(fm_changes)

    # Normalize tags (append #tag in body only if truly missing after merge)
    # The merge_frontmatter already handles frontmatter tags; this catches
    # cases where tags aren't in frontmatter but should be added as #tag
    tags_before = new_content
    new_content = normalize_tags(new_content)
    if new_content != tags_before:
        changes.append("added tags")

    # Normalize wikilinks (outside code blocks)
    wikilinks_before = new_content
    new_content = normalize_wikilinks(new_content)
    if new_content != wikilinks_before:
        changes.append("normalized wikilinks")

    # Bug 1 fix: dry-run prints plan and returns early, never writes
    if dry_run:
        print(f"[DRY-RUN] Would process: {path}  changes: {changes}")
        return {
            "path": path,
            "status": "dry_run",
            "changes": changes,
        }

    # Bug 6 fix: explicit UTF-8 encoding for write
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Processed: {path}  changes: {changes}")
    return {
        "path": path,
        "status": "processed",
        "changes": changes,
    }


def process_dir(root, dry_run=False):
    """
    Walk directory tree and process all .md files.
    Bug 2 fix: only process .md files, skip .obsidian and .git directories.
    Bug 8 fix: collect and return structured results.
    """
    results = []

    for current_root, dirs, files in os.walk(root):
        # Bug 2 fix: exclude .obsidian and .git directories from traversal
        dirs[:] = [d for d in dirs if d not in (".obsidian", ".git")]

        for file in files:
            # Bug 2 fix: only process .md files
            if not file.endswith(".md"):
                continue

            path = os.path.join(current_root, file)
            result = process_file(path, dry_run=dry_run)
            results.append(result)

    return results


def print_report(results):
    """Bug 8 fix: print a structured summary report."""
    print("\n" + "=" * 50)
    print("  OBSIDIAN NOTE NORMALIZER — PROCESSING REPORT")
    print("=" * 50)

    processed = [r for r in results if r["status"] == "processed"]
    dry_runs = [r for r in results if r["status"] == "dry_run"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"  Total files scanned:  {len(results)}")
    print(f"  Processed:            {len(processed)}")
    print(f"  Dry-run previews:     {len(dry_runs)}")
    print(f"  Skipped:              {len(skipped)}")
    if errors:
        print(f"  Errors:               {len(errors)}")
    print("-" * 50)

    if processed:
        print("\n  [PROCESSED]")
        for r in processed:
            ch = ", ".join(r["changes"]) if r["changes"] else "no changes"
            print(f"    {r['path']}  ({ch})")

    if dry_runs:
        print("\n  [DRY-RUN — would process]")
        for r in dry_runs:
            ch = ", ".join(r["changes"]) if r["changes"] else "no changes"
            print(f"    {r['path']}  ({ch})")

    if skipped:
        print("\n  [SKIPPED]")
        for r in skipped:
            print(f"    {r['path']}  reason: {r['reason']}")

    if errors:
        print("\n  [ERRORS]")
        for r in errors:
            print(f"    {r['path']}  error: {r['reason']}")

    print("=" * 50)

    total_changes = sum(len(r["changes"]) for r in processed)
    print(f"\n  Summary: {len(processed)} files processed, "
          f"{total_changes} total changes applied.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Obsidian Markdown notes — add frontmatter, tags, clean wikilinks."
    )
    parser.add_argument("root", help="Root directory containing .md notes")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    results = process_dir(args.root, dry_run=args.dry_run)

    # Bug 8 fix: print structured summary report
    print_report(results)

    return results


if __name__ == "__main__":
    main()
