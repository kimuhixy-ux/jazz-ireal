# Google CMP 導入・横展開手順書

このサイトでは、Google AdSense の「プライバシーとメッセージ」が提供する欧州規制メッセージを使用する。独自CMPや第三者CMPタグは追加しない。

## 対象と前提

- 対象地域: 欧州経済領域（EEA）、英国、スイス
- 対象ドメイン: `kimuhixy.com`
- AdSense publisher ID: `ca-pub-3562055879455682`
- 広告方式: AdSense自動広告
- CMP: Google提供CMP（IAB Europe TCF対応）

Google提供CMPの設定・文面が法的要件を満たすかの最終確認は運営者が行う。この文書は管理画面操作と実装整合性の記録であり、法的助言ではない。

## AdSense管理画面での設定

1. AdSenseへログインする。
2. 左メニューの「プライバシーとメッセージ」を開く。
3. 「欧州の規制」カードを開く。
4. 初回は「作成」、既存メッセージがあれば「管理」を選ぶ。
5. 対象サイトとして`kimuhixy.com`を選択する。サイトが未登録なら先に追加する。
6. サイト名、プライバシーポリシーURL、ロゴを確認する。
7. 利用者の選択肢は3択表示にする。
   - 同意しない（Do not consent）
   - 同意する（Consent）
   - オプションを管理（Manage options）
8. 同意ボタンは、同意を明確に示す文言のままにする。「サイトへ進む」など同意か不明な文言へ変更しない。
9. 対応言語を確認する。英語を必須とし、管理画面で提供される場合は日本語も追加する。
10. 広告技術プロバイダと利用目的を確認する。不要な事業者を推測で追加しない。
11. メッセージを公開する。

Google CMPは、メッセージ表示サイトに必要な同意撤回リンクを自動追加する。自動広告を利用しているため、独自の`googlefc.showRevocationMessage`リンクは重複して追加しない。

## Consent Modeの判断

AdSenseの「欧州の規制」設定には、広告目的および解析目的のConsent Mode設定がある。これはCMP公開とは別の任意設定である。

- Google AdsやGA4を利用しておらず、AdSenseのみの場合: 初期状態のままでよい。
- Google AdsやGA4を追加する場合: 各タグの実装と地域別デフォルト状態を確認してから有効化する。
- 判断前に有効化しない。全サイト・アプリの欧州規制メッセージへ影響するアカウント単位設定が含まれる。

## 公開前テスト

メッセージ公開後、本番URLへ次のクエリを付けて地域判定を無視したテスト表示を行う。

```text
https://kimuhixy.com/jazz-ireal/?fc=alwaysshow&fctype=gdpr
```

次を確認する。

- [ ] 欧州規制メッセージが表示される
- [ ] サイト名とプライバシーポリシーURLが正しい
- [ ] 「同意しない」「同意する」「オプションを管理」の3つが表示される
- [ ] 管理画面の目的と事業者が初期状態で未選択になっている
- [ ] 同意、拒否、個別選択の各操作後にサイトが利用できる
- [ ] ページ下部に「プライバシーと Cookie の設定」相当の撤回リンクが表示される
- [ ] 撤回リンクからメッセージを再表示し、選択を変更できる
- [ ] 日本語トップ、英語トップ、日英詳細ページで動作する
- [ ] iPhone Safariとデスクトップブラウザで本文や操作ボタンが見切れない
- [ ] AdSense管理画面でメッセージが「公開」状態になっている

## コード側の整合条件

- AdSenseコードとpublisher IDを変更しない。
- AdSenseコードは`kimuhixy.com`でだけ読み込む既存条件を維持する。
- Google CMPと競合する独自Cookieバナーや別CMPを追加しない。
- 日英プライバシーポリシーに対象地域、選択肢、後から変更できることを記載する。
- Service Workerでプライバシーポリシーを更新した場合はキャッシュバージョンを上げる。
- 静的生成ページにも既存と同じAdSenseコードとプライバシーポリシーへのリンクを含める。

## 他アプリへの横展開

同じ`kimuhixy.com`配下かつ同じAdSenseアカウントのアプリでは、管理画面の欧州規制メッセージを共用できる。各リポジトリでは次だけを個別確認する。

1. publisher IDが同一か。
2. 全広告ページにAdSenseコードがあるか。
3. 日本語と英語のプライバシーポリシーがあるか。
4. Cookie、広告、対象地域のCMP、同意変更について記載されているか。
5. 自動生成ページからポリシーへ到達できるか。
6. Service Workerが古いポリシーを返さないか。
7. `?fc=alwaysshow&fctype=gdpr`で各アプリの代表ページを確認できるか。

## 公式資料

- Google AdSense「About European regulations messages」
  - https://support.google.com/adsense/answer/10961068?hl=en
- Google AdSense「Add a consent revocation link to your site」
  - https://support.google.com/adsense/answer/10959060?hl=en
- Google AdSense「Manage consent mode settings」
  - https://support.google.com/adsense/answer/16053245?hl=en
- Google AdSense「About Privacy & messaging」
  - https://support.google.com/adsense/answer/10924669?hl=en
