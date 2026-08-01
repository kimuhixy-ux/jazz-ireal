// config.js: 収益化関連の設定値
export const AMAZON_ASSOCIATE_TAG = "kimuhixy-22";

// Amazon.com(米国)のアソシエイトタグ。JPとは別アカウントなので別途取得が必要。
// 未設定(空文字)の間は英語ページでもタグ無しの amazon.com に飛ばす。
// リンク先を .co.jp のままにすると、英語圏の読者が日本語の店舗に着地して離脱する。
export const AMAZON_US_ASSOCIATE_TAG = "";

// Ko-fiのユーザー名(例: "kimuhixy")。未設定(空文字)の間は寄付リンクを表示しない
export const KOFI_USERNAME = "kimuhixy";

// AdSense広告はカスタムドメイン(kimuhixy.com)経由のアクセス時のみ表示する
// (GitHub Pages / Cloudflare Pagesの単体URLでは重複コンテンツ扱いを避けるため表示しない)
export const ADS_ENABLED = location.hostname === "kimuhixy.com";

// Google AdSenseのパブリッシャーID
export const ADSENSE_CLIENT_ID = "ca-pub-3562055879455682";

// 静的曲ページの楽譜セクション直後に出す手動広告ユニットのスロットID(数字10桁)。
// AdSense管理画面で「記事内広告」を作成して取得する。空文字の間は自動広告のみ。
export const ADSENSE_INARTICLE_SLOT = "5164314844";

