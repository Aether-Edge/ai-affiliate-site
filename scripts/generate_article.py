#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIで「研究 → SEO記事」を自動生成し content/posts/ に Markdown を書き出す。
GitHub Actions / Cowork定期実行 のどちらからでも呼べる。

必要な環境変数:
  GEMINI_API_KEY   (provider=gemini のとき)
  OPENAI_API_KEY   (provider=openai のとき)
  ANTHROPIC_API_KEY(provider=anthropic のとき)
任意:
  AI_PROVIDER, AI_MODEL  … config.yaml を上書き
"""
import os, re, sys, json, datetime, pathlib, unicodedata
import yaml, requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG  = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
POSTS_DIR = ROOT / "content" / "posts"
TOPICS    = ROOT / "data" / "topics.txt"
POSTS_DIR.mkdir(parents=True, exist_ok=True)

GEN   = CFG["generation"]
NICHE = CFG["niche"]
PROVIDER = os.environ.get("AI_PROVIDER", GEN.get("provider", "gemini"))
MODEL    = os.environ.get("AI_MODEL", GEN.get("model", "gemini-2.0-flash"))

# ---------- トピック選定 ----------
def next_topic():
    """data/topics.txt の先頭行を取り出して消費。無ければ seed から補充。"""
    queue = []
    if TOPICS.exists():
        queue = [l.strip() for l in TOPICS.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    if not queue:
        queue = list(NICHE.get("seed_keywords", []))
    if not queue:
        print("ERROR: トピックがありません。data/topics.txt か seed_keywords を設定してください。", file=sys.stderr)
        sys.exit(1)
    topic = queue.pop(0)
    TOPICS.parent.mkdir(parents=True, exist_ok=True)
    TOPICS.write_text("\n".join(queue) + ("\n" if queue else ""), encoding="utf-8")
    return topic

def slugify(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w぀-ヿ一-鿿]+", "-", text).strip("-").lower()
    return text[:60] or "post"

# ---------- プロンプト ----------
def build_prompt(topic):
    return f"""あなたは日本語のSEOに精通したプロのWebライター兼編集者です。
以下のテーマで、検索ユーザーの悩みを解決する高品質な記事を書いてください。

# サイトのジャンル
{NICHE['theme']}

# 想定読者
{NICHE['audience']}

# 今回の記事テーマ（狙うキーワード）
{topic}

# 厳守する条件
- 文字数の目安は {GEN.get('min_words',1800)} 文字以上。
- 冒頭に必ず次の形式のYAMLフロントマターを付ける（値は内容に合わせて生成）:
---
title: "（32文字以内の魅力的なタイトル。キーワードを自然に含む）"
description: "（120文字以内のメタディスクリプション）"
date: "{datetime.date.today().isoformat()}"
tags: ["タグ1", "タグ2", "タグ3"]
---
- 本文はMarkdown。見出しは ## と ### を使い、論理的な構成にする。
- 導入→結論（おすすめ）→比較表→選び方→よくある質問(FAQ)→まとめ の流れを基本とする。
- 必ず比較表をMarkdownの表で1つ以上入れる（製品名・容量・価格帯・特徴など）。
- 事実に基づき、誇張・断定しすぎない。価格は「2025年時点の目安」等と明記。
- 医療・法律・断定的な投資助言はしない。
- 「ここに商品リンク」と書きたい箇所には [[AFFILIATE: 商品名]] というプレースホルダだけ置く（実リンクは後で差し込む）。
- 出力はフロントマター＋本文のMarkdownのみでOK。前置きや説明文は不要。
"""

# ---------- 各プロバイダ呼び出し ----------
def call_gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("ERROR: GEMINI_API_KEY が未設定です。")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": GEN.get("temperature", 0.7), "maxOutputTokens": 8192},
    }
    if GEN.get("use_web_grounding"):
        body["tools"] = [{"google_search": {}}]
    r = requests.post(url, json=body, timeout=120)
    if r.status_code != 200 and "tools" in body:  # grounding非対応モデルへのフォールバック
        body.pop("tools", None)
        r = requests.post(url, json=body, timeout=120)
    r.raise_for_status()
    data = r.json()
    return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])

def call_openai(prompt):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("ERROR: OPENAI_API_KEY が未設定です。")
    r = requests.post("https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": MODEL, "temperature": GEN.get("temperature", 0.7),
              "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def call_anthropic(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ERROR: ANTHROPIC_API_KEY が未設定です。")
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        json={"model": MODEL, "max_tokens": 8192,
              "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])

def generate(prompt):
    return {"gemini": call_gemini, "openai": call_openai, "anthropic": call_anthropic}[PROVIDER](prompt)

# ---------- 後処理 ----------
def ensure_frontmatter(md, topic):
    if md.lstrip().startswith("---"):
        return md.lstrip()
    title = topic
    fm = (f'---\ntitle: "{title}"\n'
          f'description: "{title}について比較・解説します。"\n'
          f'date: "{datetime.date.today().isoformat()}"\n'
          f'tags: ["{NICHE["theme"][:10]}"]\n---\n\n')
    return fm + md

def main():
    n = int(GEN.get("posts_per_run", 1))
    for _ in range(n):
        topic = next_topic()
        print(f"[generate] topic = {topic}")
        md = generate(build_prompt(topic)).strip()
        md = re.sub(r"^```(markdown)?\s*|\s*```$", "", md).strip()  # コードフェンス除去
        md = ensure_frontmatter(md, topic)
        date = datetime.date.today().isoformat()
        fname = f"{date}-{slugify(topic)}.md"
        out = POSTS_DIR / fname
        # 同名衝突回避
        i = 2
        while out.exists():
            out = POSTS_DIR / f"{date}-{slugify(topic)}-{i}.md"; i += 1
        out.write_text(md, encoding="utf-8")
        print(f"[generate] wrote {out.relative_to(ROOT)} ({len(md)} chars)")

if __name__ == "__main__":
    main()
