// strings.js: 日本語/英語のUI文言辞書。LOCALEに応じてSオブジェクトの値が決まる。
import { LOCALE } from "./i18n.js";

const en = LOCALE === "en";

export const S = {
  searchPlaceholder: en ? "Search by tune title (alternate spellings OK)" : "曲名で探す（別表記でも可）",
  searchAriaLabel: en ? "Search tunes" : "曲名検索",

  filterFormAriaLabel: en ? "Filter by form" : "形式で絞り込む",
  filterStyleAriaLabel: en ? "Filter by style" : "スタイルで絞り込む",
  filterBookAriaLabel: en ? "Filter by book" : "掲載書籍で絞り込む",
  tagrowAriaLabel: en ? "Filter by harmonic feature" : "和声的特徴で絞り込む",

  filterFormAllLabel: en ? "Form: All" : "形式：すべて",
  filterStyleAllLabel: en ? "Style: All" : "スタイル：すべて",
  filterBookAllLabel: en ? "Book: All" : "掲載書籍：すべて",

  bookFilterOptions: [
    { value: "kurobon", label: en ? "In the Jazz Standard Bible (Kuro-bon)" : "黒本に掲載" },
    { value: "omnibook", label: en ? "In an Omnibook" : "Omnibookに掲載" },
    { value: "realbook", label: en ? "In the Real Book" : "Real Bookに掲載" },
    { value: "any", label: en ? "In any book" : "いずれかに掲載" },
    { value: "all", label: en ? "In all three" : "全カテゴリに掲載" },
  ],

  unknownFormRow: en ? "Form unknown" : "形式不明",
  unknownStyleRow: en ? "Style unknown" : "スタイル不明",
  unknownShort: en ? "Unknown" : "不明",
  noteUnrecorded: en ? "Not noted" : "記載なし",

  pillFormLabel: en ? "Form" : "形式",
  pillStyleLabel: en ? "Style" : "スタイル",
  pillEditionLabel: en ? "Included in" : "収録",
  editionValue: (ver) => (en ? `Edition ${ver}` : `${ver} 版`),

  headingHarmonic: en ? "Harmonic Features" : "和声的特徴",
  headingClassificationNote: en ? "Classification Notes" : "分類の根拠",
  altTitlesHeading: (n) => (en ? `Alternate titles (${n})` : `元の表記（${n}件）`),
  headingSheetMusic: en ? "Sheet Music" : "楽譜",
  subKurobon: en ? "Jazz Standard Bible" : "黒本",
  subOmnibook: "Omnibook",
  subRealBook: "Real Book",

  ctaIreal: en ? "Open in iReal Pro" : "iReal Pro で開く",
  ctaSpotify: en ? "Open in Spotify" : "Spotify で開く",
  ctaFootHtml: en
    ? 'If the app doesn\'t open, visit <a href="https://www.irealpro.com" target="_blank" rel="noopener">irealpro.com</a>'
    : 'アプリが開かない場合は <a href="https://www.irealpro.com" target="_blank" rel="noopener">irealpro.com</a>',

  amazonSearchAriaLabel: (name) => (en ? `Search for ${name} on Amazon` : `${name}をAmazonで探す`),

  kofiSupport: en ? "☕ Support on Ko-fi" : "☕ Ko-fiで応援する",
  aboutLink: en ? "About" : "運営者情報",
  privacyLink: en ? "Privacy Policy" : "プライバシーポリシー",
  langSwitchLabel: en ? "日本語" : "English",
  footerDisclosure: en
    ? "This site may contain ads and affiliate links."
    : "本サイトには広告・アフィリエイトリンクが含まれる場合があります",
};
