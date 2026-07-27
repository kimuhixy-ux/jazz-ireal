// ads.js: Google AdSense自動広告の読み込み(カスタムドメイン経由のアクセス時のみ)
import { ADS_ENABLED, ADSENSE_CLIENT_ID } from "./config.js";

export function initAds() {
  if (!ADS_ENABLED || !ADSENSE_CLIENT_ID) return;

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(ADSENSE_CLIENT_ID)}`;
  script.crossOrigin = "anonymous";
  document.head.appendChild(script);
}
