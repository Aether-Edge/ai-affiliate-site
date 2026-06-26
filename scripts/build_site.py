#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content/posts/*.md  →  _site/  に静的サイトを生成。
- Markdown→HTML（表・見出し対応）
- [[AFFILIATE: 商品名]] を Amazon検索アフィリリンクへ自動変換
- AdSense / アフィリ免責 をテンプレートで挿入
- index・各記事・sitemap.xml・robots.txt・ads.txt を出力
"""
import re, html, shutil, pathlib, urllib.parse, datetime
import yaml, markdown, frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG  = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
SITE, MON = CFG["site"], CFG["monetization"]
OUT  = ROOT / "_site"
POSTS_DIR = ROOT / "content" / "posts"

env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                  autoescape=select_autoescape(["html"]))

def affiliate_link(name):
    name = name.strip()
    q = urllib.parse.quote(name)
    tag = MON.get("amazon_tag", "")
    url = f"https://www.amazon.co.jp/s?k={q}"
    if tag:
        url += f"&tag={tag}"
    return (f'<a class="aff-btn" href="{url}" target="_blank" '
            f'rel="nofollow sponsored noopener">▶ {html.escape(name)} を探す（Amazon）</a>')

def render_body(md_text):
    # アフィリプレースホルダを先に変換
    md_text = re.sub(r"\[\[AFFILIATE:\s*(.+?)\]\]",
                     lambda m: "\n\n" + affiliate_link(m.group(1)) + "\n\n", md_text)
    return markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc", "sane_lists"])

def load_posts():
    posts = []
    for f in POSTS_DIR.glob("*.md"):
        post = frontmatter.load(f)
        meta = post.metadata
        slug = f.stem
        posts.append({
            "title": meta.get("title", slug),
            "description": meta.get("description", ""),
            "date": str(meta.get("date", "")),
            "tags": meta.get("tags", []),
            "slug": slug,
            "url": f"{SITE['base_url'].rstrip('/')}/posts/{slug}.html",
            "path": f"posts/{slug}.html",
            "body": render_body(post.content),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True, exist_ok=True)

    # 静的ファイルをコピー
    static = ROOT / "static"
    if static.exists():
        for f in static.glob("*"):
            shutil.copy(f, OUT / f.name)

    posts = load_posts()
    ctx = {"site": SITE, "mon": MON, "now": datetime.date.today().isoformat()}

    # 各記事
    post_tpl = env.get_template("post.html")
    for p in posts:
        (OUT / "posts" / f"{p['slug']}.html").write_text(
            post_tpl.render(post=p, posts=posts, **ctx), encoding="utf-8")

    # トップページ
    (OUT / "index.html").write_text(
        env.get_template("index.html").render(posts=posts, **ctx), encoding="utf-8")

    # 固定ページ（プライバシーポリシー）: content/privacy.md があれば
    priv = ROOT / "content" / "privacy.md"
    if priv.exists():
        body = render_body(frontmatter.load(priv).content)
        page = {"title": "プライバシーポリシー", "description": "当サイトの方針",
                "date": "", "tags": [], "slug": "privacy", "body": body,
                "url": f"{SITE['base_url'].rstrip('/')}/privacy.html"}
        (OUT / "privacy.html").write_text(
            post_tpl.render(post=page, posts=posts, **ctx), encoding="utf-8")

    # sitemap.xml
    urls = [SITE["base_url"].rstrip("/") + "/"] + [p["url"] for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{html.escape(u)}</loc></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # robots.txt
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['base_url'].rstrip('/')}/sitemap.xml\n",
        encoding="utf-8")

    print(f"[build] {len(posts)} posts -> {OUT}")

if __name__ == "__main__":
    main()
