// donate.js: フッターへのKo-fi寄付リンク表示
import { KOFI_USERNAME } from "./config.js";
import { S } from "./strings.js";

export function renderDonateLink() {
  if (!KOFI_USERNAME) return;
  const footer = document.querySelector(".app-footer");
  if (!footer) return;

  const p = document.createElement("p");
  p.className = "footer-donate";
  p.innerHTML = `<a href="https://ko-fi.com/${encodeURIComponent(KOFI_USERNAME)}" target="_blank" rel="noopener">${S.kofiSupport}</a>`;
  footer.appendChild(p);
}
