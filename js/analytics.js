// analytics.js: Cloudflare Web Analyticsのビーコン読み込み
import { ANALYTICS_TOKEN } from "./config.js";

export function initAnalytics() {
  if (!ANALYTICS_TOKEN) return;

  // ADS_ENABLEDと違い独自ドメイン限定にしない。GitHub Pages側の利用状況も
  // 見えないと、どちらのURLに人が来ているのか判断できないため。
  const script = document.createElement("script");
  script.defer = true;
  script.src = "https://static.cloudflareinsights.com/beacon.min.js";
  script.setAttribute("data-cf-beacon", JSON.stringify({ token: ANALYTICS_TOKEN }));
  document.head.appendChild(script);
}
