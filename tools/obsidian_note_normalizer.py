import os
import re
import argparse
from datetime import datetime


DEFAULT_TAGS = ["ai", "learning"]


def has_frontmatter(content):
    """Check if content starts with YAML frontmatter (--- delimiter)."""
    return content.lstrip().startswith("---")


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


def add_frontmatter(content, title):
    """
    Add YAML frontmatter if not already present.
    Bug 4 fix: check has_frontmatter before adding.
    """
    if has_frontmatter(content):
        return content
    frontmatter = f"""---
title: {title}
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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

    # Add frontmatter if missing
    if not has_frontmatter(new_content):
        new_content = add_frontmatter(new_content, title)
        changes.append("added frontmatter")

    # Normalize tags (append if missing)
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
