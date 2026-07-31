// affiliate.js: 楽譜(黒本/Omnibook/Real Book)のAmazon検索リンク生成
import { AMAZON_ASSOCIATE_TAG } from "./config.js";

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

export function buildBookSearchLink(bookKey) {
  const query = BOOK_SEARCH_QUERIES[bookKey];
  if (!query || !AMAZON_ASSOCIATE_TAG) return null;
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}&tag=${encodeURIComponent(AMAZON_ASSOCIATE_TAG)}`;
}
