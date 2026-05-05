#!/usr/bin/env python3
"""
Knowledge Base Static Site Generator
=====================================
Converts an Obsidian-compatible Markdown knowledge base into a static HTML site.

Usage:
    python3 build-site.py /path/to/knowledge-base/ [--output ./site] [--title "站点名称"]

Features:
    - Renders every .md file as a standalone HTML page
    - Parses [[wikilink]] into relative HTML links
    - Supports dark/light theme toggle
    - Generates navigation sidebar
    - Compatible with Karpathy/Andrew-Ng style knowledge bases
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {site_title}</title>
<style>
:root {{
    --bg:#0d1117; --bg2:#161b22; --bg3:#21262d;
    --text:#e6edf3; --text2:#8b949e; --accent:#58a6ff;
    --border:#30363d; --code-bg:#1c2128;
    --link:#58a6ff; --link-hover:#79c0ff;
    --heading:#f0f6fc;
    --blockquote-bg:#161b22; --blockquote-border:#58a6ff;
    --table-border:#30363d; --table-alt:#161b22;
    --scrollbar:#30363d; --scrollbar-hover:#484f58;
}}
[data-theme="light"] {{
    --bg:#ffffff; --bg2:#f6f8fa; --bg3:#eaeef2;
    --text:#1f2328; --text2:#656d76; --accent:#0969da;
    --border:#d0d7de; --code-bg:#f6f8fa;
    --link:#0969da; --link-hover:#0550ae;
    --heading:#1f2328;
    --blockquote-bg:#f6f8fa; --blockquote-border:#0969da;
    --table-border:#d0d7de; --table-alt:#f6f8fa;
    --scrollbar:#d0d7de; --scrollbar-hover:#9ca3af;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
    background:var(--bg); color:var(--text); line-height:1.6;
    display:flex; min-height:100vh;
}}
.sidebar {{
    width:260px; flex-shrink:0; background:var(--bg2);
    border-right:1px solid var(--border); padding:20px; overflow-y:auto;
    position:sticky; top:0; height:100vh;
}}
.sidebar h2 {{ font-size:14px; color:var(--text2); margin:16px 0 8px; text-transform:uppercase; letter-spacing:0.5px; }}
.sidebar a {{
    display:block; padding:4px 8px; border-radius:4px; font-size:14px;
    color:var(--text); text-decoration:none; transition:background 0.15s;
}}
.sidebar a:hover {{ background:var(--bg3); color:var(--link); }}
.sidebar a.active {{ background:var(--bg3); color:var(--accent); font-weight:600; }}
.sidebar .repo-link {{
    display:block; text-align:center; padding:8px 12px; margin-bottom:16px;
    background:var(--accent); color:#fff; border-radius:6px;
    font-size:13px; font-weight:600; text-decoration:none;
}}
.sidebar .repo-link:hover {{ opacity:0.9; }}
.main {{ flex:1; padding:32px 48px; max-width:960px; }}
.theme-toggle {{
    position:fixed; top:16px; right:16px; z-index:100;
    background:var(--bg2); border:1px solid var(--border); border-radius:6px;
    padding:6px 12px; cursor:pointer; color:var(--text); font-size:13px;
    transition:background 0.15s;
}}
.theme-toggle:hover {{ background:var(--bg3); }}
h1 {{ font-size:28px; color:var(--heading); margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--border); }}
h2 {{ font-size:22px; color:var(--heading); margin-top:28px; margin-bottom:10px; }}
h3 {{ font-size:18px; color:var(--heading); margin-top:24px; margin-bottom:8px; }}
p {{ margin:10px 0; }}
a {{ color:var(--link); text-decoration:none; }}
a:hover {{ color:var(--link-hover); text-decoration:underline; }}
code {{
    background:var(--code-bg); padding:2px 6px; border-radius:4px;
    font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace; font-size:13px;
}}
pre {{ background:var(--code-bg); padding:16px; border-radius:6px; overflow-x:auto; margin:12px 0; }}
pre code {{ background:none; padding:0; }}
blockquote {{
    border-left:4px solid var(--blockquote-border); background:var(--blockquote-bg);
    padding:8px 16px; margin:12px 0; border-radius:0 4px 4px 0;
}}
table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
th, td {{ padding:8px 12px; border:1px solid var(--table-border); text-align:left; }}
th {{ background:var(--bg3); font-weight:600; }}
tr:nth-child(even) {{ background:var(--table-alt); }}
ul, ol {{ padding-left:24px; margin:8px 0; }}
li {{ margin:4px 0; }}
hr {{ border:none; border-top:1px solid var(--border); margin:20px 0; }}
img {{ max-width:100%; border-radius:4px; }}
.sidebar-section {{ margin-bottom:8px; }}
.sidebar-section summary {{ cursor:pointer; font-size:12px; color:var(--text2); text-transform:uppercase; letter-spacing:0.5px; padding:4px 8px; }}
.sidebar-section[open] summary {{ margin-bottom:4px; }}
::-webkit-scrollbar {{ width:8px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:var(--scrollbar); border-radius:4px; }}
::-webkit-scrollbar-thumb:hover {{ background:var(--scrollbar-hover); }}
</style>
</head>
<body>
<div class="sidebar">
    <a class="repo-link" href="{repo_url}" target="_blank">View on GitHub</a>
    <h2>📖 知识地图</h2>
    {sidebar_links}
    <h2>🔗 链接</h2>
    <a href="https://github.com/{repo_full}" target="_blank">GitHub 仓库</a>
    <a href="https://jasonlee2024.github.io/{repo_name}/" target="_blank">Pages 首页</a>
</div>
<button class="theme-toggle" onclick="toggleTheme()">🌙 深色</button>
<div class="main">
{content}
<hr>
<p style="color:var(--text2);font-size:12px;text-align:center;">
    由 <strong>build-site.py</strong> 自动生成 · {build_date} ·
    <a href="https://github.com/{repo_full}">GitHub 仓库</a>
</p>
</div>
<script>
(function(){{var t=localStorage.getItem('theme');if(t==='light'){{document.body.setAttribute('data-theme','light');document.querySelector('.theme-toggle').textContent='☀️ 浅色';}}}})();
function toggleTheme(){{var b=document.body;var t=b.getAttribute('data-theme');if(t==='light'){{b.removeAttribute('data-theme');localStorage.setItem('theme','dark');this.textContent='🌙 深色';}}else{{b.setAttribute('data-theme','light');localStorage.setItem('theme','light');this.textContent='☀️ 浅色';}}}}
</script>
</body>
</html>"""


def parse_wikilinks(text: str, all_pages: dict) -> str:
    """Convert [[wikilink]] to <a href='path.html'>text</a>."""
    def repl(m):
        target = m.group(1)
        # Support [[page|display text]]
        if '|' in target:
            page_name, display = target.split('|', 1)
        else:
            page_name = target
            display = page_name.split('/')[-1] or page_name

        # Look up the actual file path
        # Normalize: strip extension if any, strip ./ prefix
        normalized = page_name.lower().replace('.md', '').lstrip('./')

        if normalized in all_pages:
            href = all_pages[normalized]
        else:
            # Try partial match
            matched = [k for k in all_pages if normalized in k or k.endswith('/' + normalized)]
            if matched:
                href = all_pages[matched[0]]
            else:
                # Keep as text but style differently
                return f'<span style="color:var(--text2);font-style:italic;">[[{display}]]</span>'

        return f'<a href="{href}">{display}</a>'

    return re.sub(r'\[\[([^\]]+)\]\]', repl, text)


def md_to_html(md_text: str) -> str:
    """Convert basic Markdown to HTML. Handles enough for knowledge base files."""
    lines = md_text.split('\n')
    html = []
    in_code_block = False
    in_table = False
    table_rows = []
    in_list = False
    list_type = None
    in_blockquote = False
    blockquote_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if in_code_block:
                html.append('</code></pre>')
                in_code_block = False
            else:
                _flush_blockquote(html, blockquote_lines)
                _flush_list(html, in_list, list_type)
                in_list = False
                html.append('<pre><code>')
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            html.append(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') + '\n')
            i += 1
            continue

        # Blank line - flush pending blocks
        if not line.strip():
            _flush_blockquote(html, blockquote_lines)
            _flush_list(html, in_list, list_type)
            in_list = False
            in_blockquote = False
            if in_table:
                html.append('</tbody></table>')
                in_table = False
            html.append('')
            i += 1
            continue

        # Table
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if not in_table:
                # Check if next line is table separator
                if i + 1 < len(lines) and re.match(r'^\|[\s\-:]+\|', lines[i + 1]):
                    _flush_blockquote(html, blockquote_lines)
                    _flush_list(html, in_list, list_type)
                    in_list = False
                    html.append('<table><thead><tr>')
                    for c in cells:
                        html.append(f'<th>{_inline_md(c)}</th>')
                    html.append('</tr></thead><tbody>')
                    in_table = True
                    i += 2  # skip separator line
                    continue
                else:
                    # Not a real table, treat as normal text
                    pass
            else:
                html.append('<tr>')
                for c in cells:
                    html.append(f'<td>{_inline_md(c)}</td>')
                html.append('</tr>')
            i += 1
            continue
        else:
            if in_table:
                html.append('</tbody></table>')
                in_table = False

        # Horizontal rule
        if re.match(r'^---+\s*$', line.strip()):
            _flush_blockquote(html, blockquote_lines)
            _flush_list(html, in_list, list_type)
            in_list = False
            html.append('<hr>')
            i += 1
            continue

        # Headings
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            _flush_blockquote(html, blockquote_lines)
            _flush_list(html, in_list, list_type)
            in_list = False
            level = len(hm.group(1))
            text = _inline_md(hm.group(2))
            html.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('> '):
            in_blockquote = True
            blockquote_lines.append(line.strip()[2:])
            i += 1
            continue

        # List items
        li_match = re.match(r'^(\s*)[\-\*]\s+(.+)$', line)
        if li_match:
            _flush_blockquote(html, blockquote_lines)
            indent = len(li_match.group(1))
            content = _inline_md(li_match.group(2))
            if not in_list or list_type != 'ul':
                _flush_list(html, in_list, list_type)
                html.append('<ul>')
                in_list = True
                list_type = 'ul'
            html.append(f'<li>{content}</li>')
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if ol_match:
            _flush_blockquote(html, blockquote_lines)
            content = _inline_md(ol_match.group(2))
            if not in_list or list_type != 'ol':
                _flush_list(html, in_list, list_type)
                html.append('<ol>')
                in_list = True
                list_type = 'ol'
            html.append(f'<li>{content}</li>')
            i += 1
            continue

        # Regular paragraph
        _flush_blockquote(html, blockquote_lines)
        _flush_list(html, in_list, list_type)
        in_list = False
        html.append(f'<p>{_inline_md(line)}</p>')
        i += 1

    # Flush remaining
    _flush_blockquote(html, blockquote_lines)
    _flush_list(html, in_list, list_type)
    if in_code_block:
        html.append('</code></pre>')
    if in_table:
        html.append('</tbody></table>')

    return '\n'.join(html)


def _flush_blockquote(html, lines):
    if lines:
        content = '<br>'.join(_inline_md(l) for l in lines)
        html.append(f'<blockquote><p>{content}</p></blockquote>')
        lines.clear()


def _flush_list(html, in_list, list_type):
    if in_list:
        html.append(f'</{list_type}>')


def _inline_md(text: str) -> str:
    """Process inline Markdown: bold, italic, code, links, wikilinks."""
    # Code first (so it doesn't get processed by other rules)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Escape HTML entities (but not our generated tags)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Restore our generated tags
    text = text.replace('&lt;code&gt;', '<code>').replace('&lt;/code&gt;', '</code>')
    text = text.replace('&lt;strong&gt;', '<strong>').replace('&lt;/strong&gt;', '</strong>')
    text = text.replace('&lt;em&gt;', '<em>').replace('&lt;/em&gt;', '</em>')
    text = text.replace('&lt;a ', '<a ').replace('&lt;/a&gt;', '</a>')
    text = text.replace('&gt;', '>').replace('&lt;br&gt;', '<br>')

    return text


def get_page_title(md_path: Path, kb_root: Path) -> str:
    """Extract page title from first heading or filename."""
    try:
        content = md_path.read_text(encoding='utf-8')
        # Try first # heading
        m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except:
        pass
    rel_path = md_path.relative_to(kb_root)
    return rel_path.stem.replace('-', ' ').title()


def collect_pages(kb_root: Path) -> dict:
    """Collect all .md files and build lookup dictionary."""
    pages = {}
    file_order = []

    # Named pages for sidebar ordering
    named_order = [
        'readme', 'timeline',
        'profile/bio', 'profile/platforms-index',
        'profile/projects-index',
        'courses/_index', 'companies/_index',
        'papers/_index', 'talks/_index', 'blog/_index',
    ]

    for md_file in sorted(kb_root.rglob('*.md')):
        if '.git' in md_file.parts:
            continue
        rel = md_file.relative_to(kb_root)
        # Normalize key: lowercase, no extension
        key = str(rel).lower().replace('.md', '').replace('\\', '/')
        # URL: same path but .html
        url = str(rel).replace('.md', '.html').replace('\\', '/')
        pages[key] = url
        file_order.append((key, md_file, rel))

    # Sort by named order, then alphabetical
    def sort_key(item):
        key = item[0]
        if key in named_order:
            return (0, named_order.index(key))
        # Check if key starts with any named prefix
        for i, n in enumerate(named_order):
            if key.startswith(n):
                return (0, i)
        return (1, key)

    file_order.sort(key=sort_key)
    return pages, file_order


def build_sidebar(pages: dict, file_order: list, kb_root: Path, current_url: str) -> str:
    """Generate sidebar HTML."""
    items = []

    # Group by directory
    def get_dir(key):
        if '/' in key:
            return key.rsplit('/', 1)[0]
        return ''

    current_dir = get_dir(current_url.replace('.html', ''))

    for key, md_path, rel in file_order:
        url = pages[key]
        title = get_page_title(md_path, kb_root)

        # Skip root key (README) - it's the home button
        if key == 'readme':
            active = 'active' if current_url == 'index.html' else ''
            items.append(f'<a class="{active}" href="index.html">🏠 {title}</a>')
            items.append('<h2>目录</h2>')
            continue

        directory = get_dir(key)
        if key.startswith('profile/'):
            label = '👤 个人'
        elif key.startswith('courses/'):
            label = '📚 课程'
        elif key.startswith('companies/'):
            label = '🏢 企业'
        elif key.startswith('papers/'):
            label = '📄 论文'
        elif key.startswith('talks/'):
            label = '🎤 演讲'
        elif key.startswith('blog/'):
            label = '✍️ 博客'
        else:
            label = '📄 其他'

        active = 'active' if url == current_url else ''

        if key.endswith('/_index'):
            # Section header
            items.append(f'<h2>{label}</h2>')
            items.append(f'<a class="{active}" href="{url}">{title}</a>')
        else:
            items.append(f'<a class="{active}" href="{url}">{title}</a>')

    return '\n'.join(items)


def build_site(kb_root: Path, output_dir: Path, site_title: str, repo_full: str):
    """Build the complete static site."""
    repo_name = repo_full.split('/')[-1]
    repo_url = f'https://github.com/{repo_full}'
    build_date = datetime.now().strftime('%Y-%m-%d %H:%M')

    pages, file_order = collect_pages(kb_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read README as index
    readme_path = kb_root / 'README.md'
    index_content = ''
    if readme_path.exists():
        md_text = readme_path.read_text(encoding='utf-8')
        # Strip front matter
        md_text = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
        md_text = parse_wikilinks(md_text, pages)
        index_content = md_to_html(md_text)

    generated = []

    for key, md_path, rel in file_order:
        rel_path = str(rel).replace('.md', '.html')
        output_path = output_dir / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        md_text = md_path.read_text(encoding='utf-8')
        # Strip front matter
        md_text = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
        md_text = parse_wikilinks(md_text, pages)
        content_html = md_to_html(md_text)

        title = get_page_title(md_path, kb_root)
        sidebar_links = build_sidebar(pages, file_order, kb_root, rel_path)

        # Generate breadcrumb
        parts = rel_path.replace('.html', '').split('/')
        if len(parts) > 1:
            breadcrumb_parts = ['<a href="index.html">首页</a>']
            breadcrumb_parts.append(f'<span>{title}</span>')
            breadcrumb = '<span style="font-size:13px;color:var(--text2);margin-bottom:8px;display:block;">' + ' › '.join(breadcrumb_parts) + '</span>'
        else:
            breadcrumb = ''

        page_html = TEMPLATE.format(
            title=title,
            site_title=site_title,
            content=breadcrumb + content_html,
            sidebar_links=sidebar_links,
            repo_url=repo_url,
            repo_full=repo_full,
            repo_name=repo_name,
            build_date=build_date,
        )

        output_path.write_text(page_html, encoding='utf-8')
        generated.append(str(rel_path))

    # Ensure index.html exists (from README)
    if readme_path.exists():
        sidebar_links = build_sidebar(pages, file_order, kb_root, 'index.html')
        index_html = TEMPLATE.format(
            title='首页',
            site_title=site_title,
            content=index_content,
            sidebar_links=sidebar_links,
            repo_url=repo_url,
            repo_full=repo_full,
            repo_name=repo_name,
            build_date=build_date,
        )
        (output_dir / 'index.html').write_text(index_html, encoding='utf-8')
        print(f'  ✓ index.html (首页)')

    print(f'\n✨ 构建完成：{len(generated) + 1} 个页面 → {output_dir}')
    return True


def main():
    parser = argparse.ArgumentParser(description='Knowledge Base Static Site Generator')
    parser.add_argument('kb_path', help='Path to the knowledge base directory')
    parser.add_argument('--output', '-o', default='./site', help='Output directory (default: ./site)')
    parser.add_argument('--title', '-t', default='知识库', help='Site title')
    parser.add_argument('--repo', '-r', default='JasonLee2024/Andrew-Ng', help='GitHub repo (user/repo)')
    args = parser.parse_args()

    kb_root = Path(args.kb_path).resolve()
    output_dir = Path(args.output).resolve()

    if not kb_root.is_dir():
        print(f'❌ 目录不存在：{kb_root}')
        sys.exit(1)

    print(f'📖 知识库：{kb_root}')
    print(f'📦 输出到：{output_dir}')
    print(f'🏷️  标题：{args.title}')
    print()

    build_site(kb_root, output_dir, args.title, args.repo)


if __name__ == '__main__':
    main()
