import os
import re
import argparse
from datetime import datetime


DEFAULT_TAGS = ["ai", "learning"]


def has_frontmatter(content):
    return content.startswith("---")


def add_frontmatter(content, title):
    frontmatter = f"""---
title: {title}
created: {datetime.now()}
tags: {DEFAULT_TAGS}
---
"""
    return frontmatter + content


def normalize_tags(content):
    for tag in DEFAULT_TAGS:
        if f"#{tag}" not in content:
            content += f"\n#{tag}"
    return content


def normalize_wikilinks(content):
    return re.sub(r"\[\[(.*?)\]\]", lambda m: f"[[{m.group(1).strip()}]]", content)


def process_file(path, dry_run=False):
    with open(path, "r") as f:
        content = f.read()

    title = os.path.splitext(os.path.basename(path))[0]

    if not has_frontmatter(content):
        content = add_frontmatter(content, title)

    content = normalize_tags(content)
    content = normalize_wikilinks(content)

    with open(path, "w") as f:
        f.write(content)

    print("Processed:", path)


def process_dir(root, dry_run=False):
    for current_root, dirs, files in os.walk(root):
        for file in files:
            path = os.path.join(current_root, file)
            process_file(path, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    process_dir(args.root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
