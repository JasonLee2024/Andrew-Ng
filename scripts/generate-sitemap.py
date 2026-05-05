#!/usr/bin/env python3
"""
Generate Sitemap — KB Site Map + Directory Tree Sync
====================================================
Scans the actual knowledge base directory structure and:
1. Generates/updates `sitemap.md` — a standalone sitemap page
2. Updates `README.md` — keeps the "## 目录结构" ASCII tree in sync
3. Exits with code 1 if tree is stale (for pre-commit hook)

Usage:
    python3 scripts/generate-sitemap.py [--check] [--dry-run]

    --check    Don't write, just check if tree is up-to-date (exit code)
    --dry-run  Print what would change without modifying files
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime


# --- Configuration ---

# File descriptions shown in the ASCII tree
# "auto" means script auto-generates a description from the first heading
FILE_DESCRIPTIONS: dict[str, str] = {
    # Root
    "README.md": "首页导航 + 最近动态一览",
    "_config.yml": "GitHub Pages 配置",
    "sitemap.md": "🗺️ 站点地图（自动生成）",

    # profile/
    "profile/bio.md": "个人履历",
    "profile/platforms-index.md": "全平台索引",
    "profile/projects-index.md": "项目索引表",
}

# Non-markdown files to include in the tree
NON_MD_FILES: dict[str, str] = {
    "_config.yml": "GitHub Pages 配置",
    "scripts/update.sh": "自动拉取最新动态",
    "scripts/generate-sitemap.py": "站点地图生成器",
}

# Directories with descriptions for the tree
DIR_DESCRIPTIONS = {
    "profile": "个人简介、履历、平台索引",
    "projects": "核心开源项目详解",
    "talks": "演讲、访谈、播客",
    "social": "X/Twitter 观点精选",
    "community": "社区衍生项目 & 讨论",
    "blog": "博客文章摘要",
    "scripts": "自动化维护脚本",
    "courses": "课程体系",
    "companies": "企业版图",
    "papers": "学术论文",
}

# Navigation table (for sitemap.md)
NAV_TABLE = {
    "profile/": "个人简介、履历时间线、全平台索引",
    "projects/": "核心开源项目详解（nanoGPT, nanochat, LLM.c 等）",
    "talks/": "演讲、访谈、播客内容整理",
    "blog/": "博客文章摘要与解读",
    "social/": "X/Twitter 等社交平台观点精选",
    "community/": "社区衍生项目、讨论与二次创作",
    "scripts/": "自动化更新脚本",
    "courses/": "课程体系",
    "companies/": "企业版图",
    "papers/": "学术论文",
    "[[timeline]]": "综合时间线 — 所有事件的集中索引",
}


def get_file_desc(md_path: Path, kb_root: Path, custom: dict) -> str:
    """Get file description: custom map > auto from heading > filename."""
    rel = str(md_path.relative_to(kb_root)).replace("\\", "/")
    if rel in custom:
        return custom[rel]
    try:
        content = md_path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if m:
            title = m.group(1).strip()
            # Trim long descriptions
            if len(title) > 40:
                title = title[:37] + "..."
            return title
    except: pass
    return md_path.stem.replace("-", " ").title()


def build_tree(kb_root: Path) -> str:
    """Build ASCII directory tree from ALL tracked files."""
    lines = [f"{kb_root.name}/"]

    def collect_files(base: Path) -> dict[str, list[str]]:
        """Collect all files (both .md and known non-md) grouped by top-level dir."""
        result: dict[str, list[str]] = {"": []}
        # Collect all .md files
        for f in sorted(base.rglob("*.md")):
            if ".git" in f.parts:
                continue
            rel = str(f.relative_to(base))
            parts = rel.split("/")
            key = parts[0] if len(parts) > 1 else ""
            if key not in result:
                result[key] = []
            result[key].append(rel)
        # Add known non-md files
        for nf_rel, _ in NON_MD_FILES.items():
            nf_path = base / nf_rel
            if nf_path.exists():
                parts = nf_rel.split("/")
                key = parts[0] if len(parts) > 1 else ""
                if key not in result:
                    result[key] = []
                if nf_rel not in result[key]:
                    result[key].append(nf_rel)
        return result

    dirs = collect_files(kb_root)

    # Directory display order
    order = ["", "profile", "projects", "talks", "social", "community", "blog", "scripts"]
    for d in sorted(dirs.keys()):
        if d and d not in order:
            order.append(d)

    # Root files display order
    root_priority = ["README.md", "_config.yml", "sitemap.md", "timeline.md"]
    seen = set()

    for idx, d in enumerate(order):
        if d not in dirs or not dirs[d]:
            continue
        visible = [x for x in order if x in dirs and dirs[x]]
        is_last_dir = (d == visible[-1]) if visible else True
        prefix = "└── " if is_last_dir else "├── "

        if d == "":
            # Root: show priority files first, then others
            remaining = []
            for fname in sorted(dirs[""]):
                key = fname.split("/")[-1]
                if key in root_priority:
                    desc = FILE_DESCRIPTIONS.get(fname) or NON_MD_FILES.get(fname, "")
                    if not desc:
                        desc = get_file_desc(kb_root / fname, kb_root, FILE_DESCRIPTIONS)
                    lines.append(f"├── {key}  ← {desc}")
                    seen.add(key)
                else:
                    remaining.append(key)
            for fname in remaining:
                if fname not in seen:
                    desc = get_file_desc(kb_root / fname, kb_root, FILE_DESCRIPTIONS)
                    lines.append(f"├── {fname}  ← {desc}")
        else:
            dir_desc = DIR_DESCRIPTIONS.get(d, "")
            lines.append(f"{prefix}{d}/{'  ← ' + dir_desc if dir_desc else ''}")
            files = sorted(dirs[d])
            for fi, fname in enumerate(files):
                is_last = (fi == len(files) - 1)
                sub_prefix = "    " if is_last_dir else "│   "
                sub_join = "└── " if is_last else "├── "
                leaf = fname.split("/")[-1]
                desc = FILE_DESCRIPTIONS.get(fname) or NON_MD_FILES.get(fname, "")
                if not desc:
                    desc = get_file_desc(kb_root / fname, kb_root, FILE_DESCRIPTIONS)
                lines.append(f"{sub_prefix}{sub_join}{leaf}  ← {desc}")

    return "\n".join(lines)


def build_sitemap_md(kb_root: Path, tree: str, stats: dict) -> str:
    """Generate sitemap.md content."""
    nav_rows = []
    for dir_name, desc in NAV_TABLE.items():
        if any((kb_root / d.replace("[[", "").replace("]]", "")).exists() or
               (kb_root / "profile").parent.exists() for d in [dir_name]):
            nav_rows.append(f"| `{dir_name}` | {desc} |")

    sitemap = f"""---
date: {datetime.now().strftime('%Y-%m-%d')}
tags: [sitemap, navigation, index]
---

# 🗺️ 站点地图

> 本页由 `scripts/generate-sitemap.py` 自动生成 · 最后更新 {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 导航一览

| 目录 | 内容 |
|------|------|
{chr(10).join(nav_rows)}

## 目录结构

```
{tree}
```

## 统计

| 指标 | 数值 |
|------|------|
| Markdown 文件数 | **{stats['files']}** |
| 总行数 | **{stats['lines']}** |
| 目录数 | **{stats['dirs']}** |
| 知识库大小 | **{stats['size_kb']} KB** |
| 最后更新 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

## 维护说明

- 新增或删除文件后，运行 `python3 scripts/generate-sitemap.py` 更新本页
- 本文件由 pre-commit hook 自动校验一致性
- `scripts/update.sh` 每周运行时自动更新
"""
    return sitemap


def extract_current_tree(readme_path: Path) -> str | None:
    """Extract the current ASCII tree block from README.md."""
    try:
        content = readme_path.read_text(encoding="utf-8")
        m = re.search(r"## 目录结构\n\n```\n(.+?)\n```", content, re.DOTALL)
        if m:
            return m.group(1).strip()
    except: pass
    return None


def replace_tree_in_readme(readme_path: Path, new_tree: str, stats: dict) -> bool:
    """Replace the tree section in README.md. Returns True if changed."""
    content = readme_path.read_text(encoding="utf-8")

    old_section = re.search(r"## 目录结构\n\n```\n.*?\n```\n\n共 \*\*\d+ 个文件，\d+ 行\*\*。", content, re.DOTALL)
    new_section = f"## 目录结构\n\n```\n{new_tree}\n```\n\n共 **{stats['files']} 个文件，{stats['lines']} 行**。全部是 Obsidian 兼容的 Markdown（`[[wikilink]]` 双向链接）。"

    if old_section:
        new_content = content.replace(old_section.group(0), new_section)
    else:
        # Auto-append before the last horizontal rule or at end of file
        appendix = f"\n\n---\n\n## 目录结构\n\n```\n{new_tree}\n```\n\n共 **{stats['files']} 个文件，{stats['lines']} 行**。全部是 Obsidian 兼容的 Markdown（`[[wikilink]]` 双向链接）。"
        hr_match = list(re.finditer(r"\n---\n", content))
        if hr_match:
            insert_pos = hr_match[-1].start() + 1
            new_content = content[:insert_pos] + appendix + content[insert_pos:]
        else:
            new_content = content + appendix

    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def collect_stats(kb_root: Path) -> dict:
    """Collect KB statistics."""
    files = 0
    lines = 0
    size = 0
    dirs = set()

    for md_file in kb_root.rglob("*.md"):
        if ".git" in md_file.parts:
            continue
        files += 1
        try:
            text = md_file.read_text(encoding="utf-8")
            lines += text.count("\n") + 1
            size += len(text.encode("utf-8"))
        except: pass
        dirs.add(md_file.parent)

    return {
        "files": files,
        "lines": lines,
        "dirs": len(dirs),
        "size_kb": size // 1024,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Knowledge Base Sitemap Generator")
    parser.add_argument("--check", action="store_true", help="Check mode: exit 1 if stale")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    kb_root = Path.cwd().resolve()
    readme_path = kb_root / "README.md"

    if not readme_path.exists():
        print(f"❌ 未找到 README.md：{readme_path}")
        sys.exit(1)

    print(f"📖 扫描：{kb_root.name}")
    stats = collect_stats(kb_root)
    tree = build_tree(kb_root)

    if args.check:
        current = extract_current_tree(readme_path)
        if current == tree:
            print("✅ 目录结构已同步")
            sys.exit(0)
        else:
            print("❌ 目录结构不同步！请运行 `python3 scripts/generate-sitemap.py`")
            sys.exit(1)  # <-- THIS IS THE FIX

    # Update README
    changed_readme = replace_tree_in_readme(readme_path, tree, stats)
    if changed_readme:
        print(f"  ✓ README.md 目录树已更新")
    else:
        print(f"  - README.md 已是最新")

    # Write sitemap.md (as a separate page)
    sitemap = build_sitemap_md(kb_root, tree, stats)
    sitemap_path = kb_root / "sitemap.md"
    sitemap_path.write_text(sitemap, encoding="utf-8")
    print(f"  ✓ {sitemap_path.name} 已生成")

    print(f"\n📊 统计：{stats['files']} 文件，{stats['lines']} 行，{stats['dirs']} 目录，{stats['size_kb']} KB")
    print("✅ 完成")


if __name__ == "__main__":
    main()
