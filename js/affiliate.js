// affiliate.js: 楽譜(黒本/Omnibook/Real Book)のAmazonリンク生成
import { AMAZON_ASSOCIATE_TAG, AMAZON_US_ASSOCIATE_TAG } from "./config.js";

// 書名から商品ページのASINを引く対照表。
// 検索結果ページより商品ページ直リンクの方が購入までの手数が少なく、かつ
// 版違い(C/B♭/E♭・ハンディ版など)を誤って買われる事故も防げる。
// ページ番号が一致する版のASINだけを入れること。未確認の本は空欄のままにすると
// 従来どおり検索リンクにフォールバックする。
// 洋書のASINはISBN-10と同じ値なので、amazon.com でもそのまま商品ページになる。
const BOOK_ASINS = {
  "Vol.2": "4845623080", // ジャズ・スタンダード・バイブル2 in B♭
  "初版": "484561944X", // ジャズ・スタンダード・バイブル in E♭
  "John Coltrane Omnibook (B♭)": "1458422119",
  "Miles Davis Omnibook (E♭)": "1480354848", // Miles Davis Omnibook: For Eb Instruments
  "Stan Getz Omnibook (B♭)": "1480397423",
  "Charlie Parker Omnibook (E♭)": "", // 未確認
  "Charlie Parker Omnibook Vol.2 (E♭)": "1540021963",
  "Cannonball Adderley Omnibook (E♭)": "1495011836", // Cannonball Adderley Omnibook: For E-flat Instruments
  "Wynton Marsalis Omnibook (B♭)": "1495052451",
  "Real Book Vol.1": "0634060759", // The Real Book Vol.1 Sixth Edition for E♭
  "Real Book Vol.2": "0634060783", // The Eb Real Book vol.2 Second Edition
  "Real Book Vol.3": "1423415884", // The Eb Real Book Volume 3
};

// 黒本(ジャズ・スタンダード・バイブル)は日本国内向けの出版物で amazon.com に無い。
// 英語ページでも .co.jp に出し、リンク切れを避ける。
const JP_ONLY_BOOKS = new Set(["Vol.2", "初版"]);

// 黒本の巻・Omnibookの書名・Real Bookの巻から、Amazon.co.jpでの検索クエリを引く対照表
const BOOK_SEARCH_QUERIES = {
  "Vol.2": "ジャズ・スタンダード・バイブル 2",
  "初版": "ジャズ・スタンダード・バイブル",
  "John Coltrane Omnibook (B♭)": "John Coltrane Omnibook",
  "Miles Davis Omnibook (E♭)": "Miles Davis Omnibook",
  "Stan Getz Omnibook (B♭)": "Stan Getz Omnibook",
  "Charlie Parker Omnibook (E♭)": "Charlie Parker Omnibook",
  "Charlie Parker Omnibook Vol.2 (E♭)": "Charlie Parker Omnibook Volume 2",
  "Cannonball Adderley Omnibook (E♭)": "Cannonball Adderley Omnibook",
  "Wynton Marsalis Omnibook (B♭)": "Wynton Marsalis Omnibook",
  // Real Book は C/B♭/E♭ 版が別商品。当サイトのページ番号は E♭ 版準拠なので
  // クエリに Eb を含め、版違いを買わせないようにする。
  "Real Book Vol.1": "The Real Book Volume 1 Eb",
  "Real Book Vol.2": "The Real Book Volume 2 Eb",
  "Real Book Vol.3": "The Real Book Volume 3 Eb",
};

// 英語ページの読者は米国が中心なので amazon.com に送る。
// 訪問者のIPで振り分けず表示言語で決めているのは、静的HTMLに焼き込めて
// キャッシュが効くうえ、判定が外れても読者の読める言語の店舗に着地するため。
function marketplace(bookKey, english) {
  if (english && !JP_ONLY_BOOKS.has(bookKey)) {
    return { host: "https://www.amazon.com", tag: AMAZON_US_ASSOCIATE_TAG };
  }
  return { host: "https://www.amazon.co.jp", tag: AMAZON_ASSOCIATE_TAG };
}

export function buildBookLink(bookKey, english) {
  const { host, tag } = marketplace(bookKey, english);
  const suffix = tag ? `?tag=${encodeURIComponent(tag)}` : "";
  const asin = BOOK_ASINS[bookKey];
  if (asin) return `${host}/dp/${encodeURIComponent(asin)}${suffix}`;
  const query = BOOK_SEARCH_QUERIES[bookKey];
  if (!query) return null;
  const tagParam = tag ? `&tag=${encodeURIComponent(tag)}` : "";
  return `${host}/s?k=${encodeURIComponent(query)}${tagParam}`;
}
