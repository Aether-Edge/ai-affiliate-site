# AIアフィリエイト自動更新サイト スターターキット

GitHub Pages + GitHub Actions + AI API で、**記事の研究・執筆・公開を自動化**する収益サイトの土台です。さらに **Cowork の定期実行**で「品質の高い柱記事」と「収益レビュー」を回す二段構えを想定しています。

---

## 1. 全体構成

```
            ┌─────────────────────────────────────────┐
            │  GitHub リポジトリ（このフォルダ一式）      │
            └─────────────────────────────────────────┘
                       │
   ┌───────────────────┼────────────────────────┐
   │ 毎日 自動（主力）   │  週1 高品質（Cowork）      │ 手動編集
   ▼                   ▼                          ▼
generate.yml      Cowork定期実行タスク          deploy.yml
 (cron)            ・トレンド調査               (push時)
 AI APIで記事生成   ・柱記事を執筆               ビルド→公開
 → commit          ・収益データのレビュー
   │                ・次に狙うキーワード提案
   ▼                   │
 build_site.py（Markdown → 静的HTML）
   ▼
 GitHub Pages で公開（AdSense + アフィリリンク入り）
```

- **主力エンジン＝GitHub Actions**：クラウドで確実に毎日動く。Coworkを開かなくても記事が増える。
- **品質担保＝Cowork定期実行**：AIが量産した記事に埋もれないよう、Claude本体が時間をかけた「柱記事」や戦略を担当。
- どちらも最終的に同じGitHubリポジトリに記事(Markdown)を足すだけ。

---

## 2. 収益「月50万円」の現実的な内訳

AdSense単体は1PVあたり約0.2〜0.5円。**50万円をAdSenseだけ**で出すには月100万〜250万PV必要で、新規サイトには非現実的です。現実的な設計は **アフィリエイト主軸＋AdSense補助**：

| 収益源 | 役割 | 月50万円時の目安 |
|---|---|---|
| アフィリエイト（ASP/Amazon/楽天） | 主軸（70〜85%） | 35〜42万円 |
| Google AdSense | 補助 | 8〜15万円 |

到達イメージ（高単価ニッチの場合）：**月10万PV前後＋成約率0.5〜1%＋平均報酬2,000〜5,000円**でアフィリ30〜40万円。ここに到達するまで通常 **半年〜1年・記事100〜300本**が目安です。自動生成はこの「本数」を圧倒的に速くするための仕組みです。

> ⚠️ 重要：AI生成そのままの薄い記事を量産するとGoogleの品質評価（Helpful Content）で評価されず、AdSense審査も通りにくいです。**「自動で量産 → Coworkと人で要所を磨く」**のハイブリッドが鍵です。

---

## 3. 推奨ニッチ（初期設定済み）と代替案

このキットは初期状態で **「ポータブル電源・防災ガジェット」** に設定済みです。理由：

- **高単価**：本体5万〜20万円。Amazonでも単価が高く、Jackery/EcoFlow/Ankerは直接ASP案件もあり1件数千円。
- **需要が安定＋季節要因**：防災・キャンプ・車中泊・停電対策で年中検索される。
- **YMYL（医療・金融）ではない**ので審査・品質評価のハードルが比較的低い。
- **新製品とセールが絶えず出る**＝自動生成の「ネタ切れ」が起きにくい。

別ジャンルにしたい場合は `config.yaml` の `niche` と `seed_keywords` を書き換えるだけ。代替候補：

- **ふるさと納税 返礼品比較**：検索量大・高単価・季節需要。大手が強い。
- **格安SIM/光回線 比較**：1件5,000〜20,000円と超高単価。ただし激戦・やや専門性必須。
- **VOD（動画配信）作品情報**：成約単価は中程度だが新作で毎日ネタが出る＝自動化超向き。

---

## 4. セットアップ手順（GitHubアカウントあり前提）

### ① リポジトリを作る
1. GitHubで新規リポジトリ `ai-affiliate-site`（Public）を作成。
2. このフォルダ一式をアップロード（ドラッグ&ドロップ or `git push`）。

### ② AI APIキーを登録（Geminiが最安・推奨）
1. Google AI Studio（aistudio.google.com）で **Gemini APIキー**を無料取得。
2. リポジトリの **Settings → Secrets and variables → Actions → New repository secret**。
3. 名前 `GEMINI_API_KEY`、値にキーを貼り付け。
   （OpenAI/Anthropicを使うなら `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` を登録し、`config.yaml` の `provider` を変更）

### ③ GitHub Pages を有効化
- **Settings → Pages → Build and deployment → Source = 「GitHub Actions」** を選択。

### ④ config.yaml を自分用に編集
- `site.base_url` を `https://<あなたのユーザー名>.github.io/ai-affiliate-site` に。
- `monetization.amazon_tag` を自分のAmazonアソシエイトIDに。
- AdSense承認後、`monetization.adsense_client` を `ca-pub-...` に。
- `static/ads.txt` の `pub-XXXX...` も同じIDに置換。

### ⑤ 動かす
- **Actions タブ → 「AI記事を自動生成して公開」→ Run workflow** で即実行。
- 数分後、Pagesに記事が公開されます。以後は毎日朝6時(JST)に自動で1本ずつ増えます（cronは `generate.yml` で変更可）。

### ⑥ 収益化の申請
- 記事が**15〜30本**たまり、プライバシーポリシー（同梱済み `/privacy.html`）が公開されたら **AdSense審査**に申請。
- **Amazonアソシエイト**・**もしも/A8.netなどASP**にも登録し、`config.yaml` のタグを設定。

---

## 5. Cowork 定期実行の役割（質問への回答）

**「Coworkの定期実行で、情報収集から記事生成まで行えるか？」→ はい、可能です。** Cowork（このアシスタント）は定期実行タスクとして、Web調査→執筆→ファイル書き出しまで一気通貫でできます。本キットでの推奨分担は次の通り：

- **GitHub Actions（毎日）**：量を担当。安価なAI APIで標準記事を1本/日。
- **Cowork定期実行（週1）**：質を担当。Claudeが時間をかけてトレンドを調べ、**2,000字超の比較・まとめの“柱記事”**を執筆。あわせて公開済み記事の改善点や次に狙うキーワードを提案。

Cowork定期実行タスクに渡すプロンプトの雛形は同梱の **`COWORK_TASK.md`** にあります。これをそのまま定期タスク化すれば、毎週月曜に柱記事の草稿が上がってきます（GitHub連携が未設定の間は、生成した記事をこちらで受け取り、リポジトリにアップする運用でOK）。

---

## 6. 50万円までのロードマップ

1. **月0〜1**：セットアップ完了、自動生成で30本到達、AdSense申請。
2. **月1〜3**：100本到達。アクセス解析でアタリ記事を特定し、Coworkで強化（追記・比較表・内部リンク）。
3. **月3〜6**：成約する記事のテーマに集中投下。ASPの高単価案件を記事に組み込む。
4. **月6〜12**：上位表示が増え、PVと成約が積み上がる。50万円はこの積み上げの先。

**伸びる/伸びないの最大の分岐は「検索意図に本当に応える記事か」**。自動化はスピードを与えますが、勝負所はCoworkと人による磨き込みです。

---

## 7. ファイル構成

```
config.yaml              ← ここだけ書き換えれば運用できる中心設定
requirements.txt
scripts/
  generate_article.py    ← AIで研究→記事を生成（Actions/Coworkから呼ぶ）
  build_site.py          ← Markdown → 静的HTML（AdSense/アフィリ自動挿入）
templates/               ← サイトのデザイン（base/index/post）
static/                  ← CSS・ads.txt
content/posts/           ← 生成された記事(Markdown)が貯まる場所
content/privacy.md       ← プライバシーポリシー（AdSense必須）
data/topics.txt          ← 記事化キーワードの順番待ち行列
.github/workflows/
  generate.yml           ← 毎日: 生成→コミット→ビルド→公開
  deploy.yml             ← 手動編集をpushした時: ビルド→公開
COWORK_TASK.md           ← Cowork定期実行に渡すプロンプト雛形
```

ローカル確認：`pip install -r requirements.txt` 後、`python scripts/build_site.py` → `_site/` をブラウザで開く。
