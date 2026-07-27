// i18n.js: URLパス(/en/を含むか)からロケールを判定する
export const LOCALE = location.pathname.includes("/en/") ? "en" : "ja";

// 相対パスの基点。/en/配下のページから見て、data.js等アプリ直下のファイルは1階層上になる
export const ROOT = LOCALE === "en" ? "../" : "./";
