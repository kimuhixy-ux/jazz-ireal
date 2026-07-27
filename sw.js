// sw.js: オフライン閲覧のためのService Worker
// バージョンを上げると古いキャッシュが破棄され、新しいファイルに置き換わります。
const CACHE_VERSION = "jazz-ireal-v3";

const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./about.html",
  "./privacy.html",
  "./manifest.json",
  "./en/index.html",
  "./en/about.html",
  "./en/privacy.html",
  "./en/manifest.json",
  "./css/style.css",
  "./js/app.js",
  "./js/i18n.js",
  "./js/strings.js",
  "./js/config.js",
  "./js/donate.js",
  "./js/ads.js",
  "./js/affiliate.js",
  "./data.js",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

// Cloudflare Pagesは*.htmlパスを拡張子なしの正規URLへ308リダイレクトするため、
// リダイレクト後のレスポンス(response.redirected === true)はキャッシュしない。
// これをキャッシュすると、後続のナビゲーションリクエストにrespondWith()で
// 返した際にChromeがnet::ERR_FAILEDで拒否する。
async function precache(cache, urls) {
  await Promise.all(
    urls.map(async (url) => {
      try {
        const response = await fetch(url);
        if (response.ok && !response.redirected) {
          await cache.put(url, response);
        }
      } catch (e) {
        // オフライン等でプリキャッシュに失敗しても致命的ではない
      }
    })
  );
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => precache(cache, PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  if (new URL(request.url).origin !== location.origin) return; // iReal Pro/Spotify等の外部リンクは対象外

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          // リダイレクト先のレスポンスはキャッシュしない(理由は上記precache参照)
          if (!response.redirected) {
            const clone = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => cached);
    })
  );
});
