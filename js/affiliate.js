// affiliate.js: 楽譜(黒本/Omnibook/Real Book)のAmazonリンク生成
import { AMAZON_ASSOCIATE_TAG } from "./config.js";

// 書名から商品ページのASINを引く対照表。
// 検索結果ページより商品ページ直リンクの方が購入までの手数が少なく、かつ
// 版違い(C/B♭/E♭・ハンディ版など)を誤って買われる事故も防げる。
// ページ番号が一致する版のASINだけを入れること。未確認の本は空欄のままにすると
// 従来どおり検索リンクにフォールバックする。
const BOOK_ASINS = {
  "Vol.2": "4845623080", // ジャズ・スタンダード・バイブル2 in B♭
  "初版": "484561944X", // ジャズ・スタンダード・バイブル in E♭
  "John Coltrane Omnibook (B♭)": "1458422119",
  "Miles Davis Omnibook (E♭)": "", // 手元の実物はB♭版。データの調号表記と食い違うため保留
  "Stan Getz Omnibook (B♭)": "1480397423",
  "Charlie Parker Omnibook (E♭)": "", // 未確認
  "Charlie Parker Omnibook Vol.2 (E♭)": "1540021963",
  "Cannonball Adderley Omnibook (E♭)": "", // 未確認
  "Wynton Marsalis Omnibook (B♭)": "1495052451",
  "Real Book Vol.1": "0634060759", // The Real Book Vol.1 Sixth Edition for E♭
  "Real Book Vol.2": "0634060783", // The Eb Real Book vol.2 Second Edition
  "Real Book Vol.3": "1423415884", // The Eb Real Book Volume 3
};

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

export function buildBookLink(bookKey) {
  if (!AMAZON_ASSOCIATE_TAG) return null;
  const tag = encodeURIComponent(AMAZON_ASSOCIATE_TAG);
  const asin = BOOK_ASINS[bookKey];
  if (asin) return `https://www.amazon.co.jp/dp/${encodeURIComponent(asin)}?tag=${tag}`;
  const query = BOOK_SEARCH_QUERIES[bookKey];
  if (!query) return null;
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}&tag=${tag}`;
}
