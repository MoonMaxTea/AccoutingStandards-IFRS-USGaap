/** 探测 asc.fasb.org 页面结构（一次性调试） */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const DEBUG = join(dirname(fileURLToPath(import.meta.url)), "../.tmp/asc-debug");
mkdirSync(DEBUG, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage();

await page.goto("https://asc.fasb.org/Home", { waitUntil: "networkidle", timeout: 90000 });
writeFileSync(join(DEBUG, "home.html"), await page.content());
console.log("URL after home:", page.url());

// Access
for (const sel of ['text=Access', 'a:has-text("Access")', 'button:has-text("Access")']) {
  const el = page.locator(sel).first();
  if (await el.count()) {
    await el.click();
    await page.waitForTimeout(3000);
    console.log("Clicked Access via", sel);
    break;
  }
}
writeFileSync(join(DEBUG, "after-access.html"), await page.content());
console.log("URL after access:", page.url());

// Try 606-10
const urls = [
  "https://asc.fasb.org/606-10/tableOfContent",
  "https://asc.fasb.org/606/tableOfContent",
  "https://asc.fasb.org/606-10-05",
];
for (const url of urls) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForTimeout(2000);
  const body = await page.innerText("body");
  const hasJoin = /join/i.test(body);
  const has606 = /606-10/.test(body);
  console.log(url, "join?", hasJoin, "606-10?", has606, "len", body.length);
  writeFileSync(join(DEBUG, `page-${url.split("/").pop()}.html`), await page.content());
  if (hasJoin) {
    const links = await page.locator("a, button").allInnerTexts();
    const joinTexts = links.filter((t) => /join|show all|print/i.test(t));
    console.log("  buttons/links:", joinTexts.slice(0, 20));
  }
}

await browser.close();
console.log("Debug files in", DEBUG);
