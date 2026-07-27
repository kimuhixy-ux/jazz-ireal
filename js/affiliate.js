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
  "Cannonball Adderley Omnibook (E♭)": "Cannonball Adderley Omnibook",
  "Real Book Vol.1": "The Real Book Volume 1",
};

export function buildBookSearchLink(bookKey) {
  const query = BOOK_SEARCH_QUERIES[bookKey];
  if (!query || !AMAZON_ASSOCIATE_TAG) return null;
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}&tag=${encodeURIComponent(AMAZON_ASSOCIATE_TAG)}`;
}
