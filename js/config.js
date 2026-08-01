// config.js: 収益化関連の設定値
export const AMAZON_ASSOCIATE_TAG = "kimuhixy-22";

// Ko-fiのユーザー名(例: "kimuhixy")。未設定(空文字)の間は寄付リンクを表示しない
export const KOFI_USERNAME = "kimuhixy";

// AdSense広告はカスタムドメイン(kimuhixy.com)経由のアクセス時のみ表示する
// (GitHub Pages / Cloudflare Pagesの単体URLでは重複コンテンツ扱いを避けるため表示しない)
export const ADS_ENABLED = location.hostname === "kimuhixy.com";

// Google AdSenseのパブリッシャーID
export const ADSENSE_CLIENT_ID = "ca-pub-3562055879455682";

// 静的曲ページの楽譜セクション直後に出す手動広告ユニットのスロットID(数字10桁)。
// AdSense管理画面で「記事内広告」を作成して取得する。空文字の間は自動広告のみ。
export const ADSENSE_INARTICLE_SLOT = "";

// Cloudflare Web Analyticsのトークン(32桁の16進文字列)。
// Cloudflareダッシュボード > Web Analytics > サイト追加 で取得する。
// Cookieを使わないためCMPの同意対象外。空文字の間は計測しない。
export const ANALYTICS_TOKEN = "";
