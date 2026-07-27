# プログラマティックSEO横展開手順書

この文書は `jazz-ireal` で実装した、データ1件につき日英1ページを静的生成する方式を他の vanilla JS + HTML + CSS リポジトリへ展開するための手順書です。

## 1. 今回追加・変更したもの

- `scripts/generate_pages.py`: データ読込、slug採番、日英詳細ページ・索引・sitemap・robots生成
- `scripts/validate_generated_pages.py`: 件数、SEO要素、JSON-LD、免責文、内部リンク、sitemapの検査
- `templates/detail_ja.html` / `templates/detail_en.html`: 日英詳細ページ
- `templates/index_ja.html` / `templates/index_en.html`: 日英索引ページ
- `items/<slug>/index.html`: 日本語詳細ページ
- `en/items/<slug>/index.html`: 英語詳細ページ
- `items/index.html` / `en/items/index.html`: A–Z索引
- `sitemap.xml` / `robots.txt`
- `css/style.css`: 詳細・索引用の既存テーマ準拠スタイル
- `index.html` / `en/index.html`: 索引への入口
- `js/app.js`: `?q=<title>` で該当曲を絞り込む入口
- `sw.js`: 生成ページをプリキャッシュせず、ナビゲーションをネットワーク優先にする処理

## 2. 横展開前の調査

次を現在のファイルから調べ、記録する。

1. レコード件数、全フィールド、型、欠損数、英語フィールドの充足率
2. コード進行、メロディ、歌詞、本文など、詳細ページへ複製してはいけない著作物フィールドの有無
3. `/en/` 静的ページ、クライアント側トグル、canonical、hreflangの現状
4. AdSenseのpublisher ID、読み込み条件、広告ユニットID、ドメイン直下の`ads.txt`
5. 現在のリポジトリ容量と、`レコード数 × 言語数 × 想定HTMLサイズ`による生成後容量

翻訳が欠ける場合は、英語ページを日本語フォールバックで公開するか、翻訳完了まで生成を止めるかをオーナーに確認する。

## 3. URLとslug

既存に`/en/`がある場合の標準URL:

- 日本語: `/items/<slug>/`
- 英語: `/en/items/<slug>/`

ファイルは各ディレクトリの`index.html`として出力する。slugはUnicodeをNFKD正規化し、ASCII化した英数字ケバブケースを基本とする。ASCII化で空になる名前は安定したレコード番号を使う。以下を必ず処理する。

- `index`などの予約語を避ける
- 同一の基本slugには`-2`、`-3`を付ける
- 元タイトル自体が`-2`などで終わる場合も含め、最終slug集合全体で一意性を検査する
- 並び替えでURLが変わりうるため、公開後はslugマップを保存するか旧URLからのリダイレクトを用意する

## 4. テンプレート適合

各リポジトリの既存CSS、ヘッダー、フッター、日英URL構造を優先する。テンプレートには最低限、次を入れる。

- 一意の`title`と155文字程度以内の`meta description`
- 自己参照canonical
- `ja`、`en`、`x-default`の相互hreflang
- ページ別OGP、Twitter Card
- パンくず、アプリ本体へのリンク、静的索引へのリンク
- データから断定できる関連項目への内部リンク
- 既存と同じ条件・publisher IDのAdSense読み込み
- 広告・アフィリエイト表記、プライバシーポリシーへのリンク

AdSenseは既存実装を削除・変更しない。自動広告なら既存publisher IDを使い、既存と同様に本番ホストだけで読み込む。`ads.txt`はドメイン直下にだけ置く必要があるため、サブパス配信リポジトリ内の有無だけで対応済みと判断しない。

## 5. schema.orgタイプの選び方

レコードの実体に最も近い型を1つ選び、推測値を入れない。

| データ | 推奨タイプ | 主な項目 |
|---|---|---|
| 楽曲 | `MusicComposition` | `name`, `composer`, `datePublished`, `genre` |
| 書籍・文学作品 | `Book` | `name`, `author`, `datePublished`, `isbn` |
| 人物 | `Person` | `name`, `birthDate`, `nationality` |
| 賞・受賞記録 | `Award`相当の利用可能な型を再調査 | 受賞名、対象、年 |
| 場所・施設 | `Place`または具体的な下位型 | `name`, `geo`, `address` |

全詳細ページに`BreadcrumbList`を追加する。`WebSite`はサイト共通情報として追加可能。データに独立フィールドがない作曲者や年を説明文から機械抽出してschemaへ入れない。

## 6. 著作権と書籍参照

楽譜・コード進行・メロディ・歌詞・書籍本文は、本文、meta description、JSON-LD、OGPのすべてから除外する。書名は掲載位置を示す指示的使用に限定し、`official`、`authorized`、`licensed`など提携・公認を示唆する表現を生成物に入れない。

楽譜本を参照するサイトでは、日英の指定免責文と、参照版に関する注記を詳細・索引ページへ入れる。版データがない場合は固定文言を推測せず、オーナー確認後に確定する。

## 7. 索引、sitemap、robots

- 日英それぞれにA–Zまたはカテゴリ別索引を生成する
- トップページから索引へ通常の`<a>`リンクを張る
- 5万URL以下なら単一`sitemap.xml`、超える場合は複数sitemapとsitemap indexに分割する
- `robots.txt`にsitemapの絶対URLを記載する
- サイトがサブパス配信の場合、ドメイン直下の`/robots.txt`にもsitemap登録が必要か、ポータル側の配信設定を確認する

## 8. Service Worker

数千ページを`PRECACHE_URLS`へ追加しない。生成ページのナビゲーションはネットワーク優先とし、成功時のみ閲覧済みページをキャッシュ、オフライン時にキャッシュへフォールバックする。変更時はキャッシュバージョンを上げる。

## 9. 更新手順

```sh
python3 scripts/generate_pages.py
python3 scripts/validate_generated_pages.py
git diff --check
```

同じデータとテンプレートから再実行した際に差分が出ないことを確認する。生成物は手編集せず、修正はデータ・テンプレート・生成スクリプトへ行う。

## 10. 確認チェックリスト

- [ ] 日英の詳細ページ数が元レコード数と一致
- [ ] slugが全件一意で、予約語と衝突しない
- [ ] 全ページにcanonical、相互hreflang、title、descriptionがある
- [ ] JSON-LDが構文エラーなく、実データだけを表現している
- [ ] OGPとTwitter Cardがページ別タイトル・説明を持つ
- [ ] 全内部リンクの参照先が存在する
- [ ] 日英索引が全レコードを1回ずつ掲載
- [ ] sitemapのURL数が想定と一致し、重複がない
- [ ] robots.txtがsitemapを指す
- [ ] 著作物フィールドと提携を示唆する語が生成物にない
- [ ] 指定免責文と版注記がある
- [ ] AdSenseのIDと読み込み条件が既存実装と一致
- [ ] 生成ページがService Workerの事前キャッシュ対象外
- [ ] iPhone幅とデスクトップ幅で代表ページ・長い曲名・索引を目視確認
- [ ] `generate_pages.py`再実行後に意図しない差分がない
- [ ] `git push`前にオーナー承認を得る
