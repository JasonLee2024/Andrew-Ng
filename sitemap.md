---
date: 2026-05-05
tags: [sitemap, navigation, index]
---

# 🗺️ 站点地图

> 本页由 `scripts/generate-sitemap.py` 自动生成 · 最后更新 2026-05-05 18:48

## 导航一览

| 目录 | 内容 |
|------|------|
| `profile/` | 个人简介、履历时间线、全平台索引 |
| `projects/` | 核心开源项目详解（nanoGPT, nanochat, LLM.c 等） |
| `talks/` | 演讲、访谈、播客内容整理 |
| `blog/` | 博客文章摘要与解读 |
| `social/` | X/Twitter 等社交平台观点精选 |
| `community/` | 社区衍生项目、讨论与二次创作 |
| `scripts/` | 自动化更新脚本 |
| `courses/` | 课程体系 |
| `companies/` | 企业版图 |
| `papers/` | 学术论文 |
| `[[timeline]]` | 综合时间线 — 所有事件的集中索引 |

## 目录结构

```
Andrew_Ng/
├── README.md  ← 首页导航 + 最近动态一览
├── _config.yml  ← GitHub Pages 配置
├── sitemap.md  ← 🗺️ 站点地图（自动生成）
├── timeline.md  ← Andrew Ng 时间线总索引
├── profile/  ← 个人简介、履历、平台索引
│   ├── bio.md  ← 个人履历
│   └── platforms-index.md  ← 全平台索引
├── talks/  ← 演讲、访谈、播客
│   └── _index.md  ← 演讲 & 对谈
├── blog/  ← 博客文章摘要
│   └── _index.md  ← 博客 & 专栏
├── scripts/  ← 自动化维护脚本
│   └── generate-sitemap.py  ← 站点地图生成器
├── companies/  ← 企业版图
│   └── _index.md  ← 企业版图
├── courses/  ← 课程体系
│   └── _index.md  ← 课程体系
└── papers/  ← 学术论文
    └── _index.md  ← 学术论文
```

## 统计

| 指标 | 数值 |
|------|------|
| Markdown 文件数 | **10** |
| 总行数 | **434** |
| 目录数 | **7** |
| 知识库大小 | **15 KB** |
| 最后更新 | 2026-05-05 18:48 |

## 维护说明

- 新增或删除文件后，运行 `python3 scripts/generate-sitemap.py` 更新本页
- 本文件由 pre-commit hook 自动校验一致性
- `scripts/update.sh` 每周运行时自动更新
