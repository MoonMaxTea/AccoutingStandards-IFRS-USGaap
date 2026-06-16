/**
 * 从 asc.fasb.org 抓取 ASC Codification 合并页文本（试点脚本）
 *
 * ⚠️ 注意：asc.fasb.org 使用 Cloudflare 防护，headless/自动化 IP 可能被拦截。
 * 若本脚本失败，请改用 Print-to-PDF 流程：asc_print_pdf_import.py
 *
 * 用法:
 *   node .scripts/asc_codification_scrape.mjs 606 --headed   # 请在本地有界面运行
 *   node .scripts/asc_codification_scrape.mjs 606 --debug
 */

import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const ASC_DIR = join(ROOT, "03 - 知识库/US GAAP/ASC准则");
const DEBUG_DIR = join(ROOT, ".tmp/asc-debug");
const HOME = "https://asc.fasb.org/Home";

const TOPICS = {
  606: {
    name_en: "Revenue From Contracts With Customers",
    name_cn: "客户合同收入",
    subtopics: ["606-10"],
    key: true,
  },
};

function normalize(text) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim() + "\n";
}

function slug(num, nameEn) {
  return join(ASC_DIR, `ASC ${num} - ${nameEn}.md`);
}

function buildMarkdown(meta, num, parts) {
  const today = new Date().toISOString().slice(0, 10);
  const subtopicsYaml = meta.subtopics.map((s) => `"${s}"`).join(", ");
  const keyLine = meta.key ? "key: true\n" : "";
  let title = `# ASC ${num} — ${meta.name_en}（${meta.name_cn}）`;
  if (meta.key) title += " ⭐ 重点准则";

  const fm = `---
tags: [us-gaap, asc-${num}]
standard: ASC ${num}
source: FASB ASC
source_url: https://asc.fasb.org/
source_type: Codification
scraped_date: "${today}"
subtopics: [${subtopicsYaml}]
${keyLine}---
`;

  let body = `${fm}\n${title}\n`;
  for (const [sub, text] of parts) {
    body += `\n---\n\n## Subtopic ${sub}\n\n${text}\n`;
  }
  return body;
}

async function launchBrowser(headed) {
  for (const channel of ["msedge", "chrome", null]) {
    try {
      const opts = { headless: !headed };
      if (channel) opts.channel = channel;
      return await chromium.launch(opts);
    } catch {
      /* try next */
    }
  }
  throw new Error("无法启动浏览器，请确认已安装 Edge 或 Chrome");
}

async function acceptHome(page, debug) {
  await page.goto(HOME, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2000);

  const names = [/access/i, /access the basic view/i];
  for (const pat of names) {
    const btn = page.getByRole("button", { name: pat });
    if ((await btn.count()) > 0) {
      await btn.first().click();
      await page.waitForTimeout(2500);
      break;
    }
    const link = page.getByRole("link", { name: pat });
    if ((await link.count()) > 0) {
      await link.first().click();
      await page.waitForTimeout(2500);
      break;
    }
  }
  if (debug) {
    mkdirSync(DEBUG_DIR, { recursive: true });
    await page.screenshot({ path: join(DEBUG_DIR, "01-after-access.png"), fullPage: true });
  }
}

async function gotoSubtopic(page, subtopic) {
  const urls = [
    `https://asc.fasb.org/${subtopic}/tableOfContent`,
    `https://asc.fasb.org/${subtopic}`,
    `https://asc.fasb.org/${subtopic.split("-")[0]}/tableOfContent`,
  ];
  for (const url of urls) {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(2000);
    const html = await page.content();
    if (html.includes(subtopic)) return;
  }
}

async function clickJoinAll(page) {
  const pats = [/join\s*all\s*sections/i, /show\s*all\s*in\s*one\s*page/i];
  for (const pat of pats) {
    for (const role of ["button", "link"]) {
      const loc = page.getByRole(role, { name: pat });
      if ((await loc.count()) > 0) {
        await loc.first().click();
        return true;
      }
    }
  }
  const fallback = page.locator("a, button").filter({ hasText: /join all/i });
  if ((await fallback.count()) > 0) {
    await fallback.first().click();
    return true;
  }
  return false;
}

async function waitForParagraphs(page, subtopic, timeoutMs = 120000) {
  const re = new RegExp(`${subtopic.replace(/-/g, "\\-")}-\\d+-\\d+`);
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const body = await page.innerText("body");
    if (re.test(body)) return;
    await page.waitForTimeout(2000);
  }
  throw new Error(`等待 ${subtopic} 段落超时`);
}

async function extractText(page) {
  for (const sel of ["#content", ".content", "#mainContent", "main", "article"]) {
    const loc = page.locator(sel);
    if ((await loc.count()) > 0) {
      const text = await loc.first().innerText();
      if (text.length > 500) return normalize(text);
    }
  }
  return normalize(await page.innerText("body"));
}

async function scrapeSubtopic(page, subtopic, debug) {
  await gotoSubtopic(page, subtopic);
  if (debug) {
    mkdirSync(DEBUG_DIR, { recursive: true });
    await page.screenshot({
      path: join(DEBUG_DIR, `02-${subtopic}-landing.png`),
      fullPage: true,
    });
  }

  const joined = await clickJoinAll(page);
  if (!joined) console.log("  警告: 未找到 Join All Sections，尝试直接提取");

  await page.waitForTimeout(4000);
  await waitForParagraphs(page, subtopic);

  if (debug) {
    await page.screenshot({
      path: join(DEBUG_DIR, `03-${subtopic}-merged.png`),
      fullPage: true,
    });
    writeFileSync(join(DEBUG_DIR, `03-${subtopic}-merged.html`), await page.content(), "utf8");
  }

  return extractText(page);
}

async function scrapeTopic(num, { headed, debug }) {
  const meta = TOPICS[num];
  if (!meta) throw new Error(`Topic ${num} 未配置`);

  console.log(`ASC ${num}: ${meta.name_en}`);
  mkdirSync(ASC_DIR, { recursive: true });

  const browser = await launchBrowser(headed);
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });
  const page = await context.newPage();
  const parts = [];

  try {
    await acceptHome(page, debug);
    for (const sub of meta.subtopics) {
      console.log(`  Subtopic ${sub} …`);
      const text = await scrapeSubtopic(page, sub, debug);
      console.log(`  提取 ${text.length.toLocaleString()} 字符`);
      parts.push([sub, text]);
    }
  } finally {
    await browser.close();
  }

  const out = slug(num, meta.name_en);
  writeFileSync(out, buildMarkdown(meta, num, parts), "utf8");
  console.log(`  已写入: ${out}`);
  return parts.every(([, t]) => t.length > 1000);
}

const args = process.argv.slice(2);
const headed = args.includes("--headed");
const debug = args.includes("--debug");
const topics = args.filter((a) => /^\d+$/.test(a)).map(Number);
const nums = topics.length ? topics : [606];

let ok = 0;
for (const num of nums) {
  try {
    if (await scrapeTopic(num, { headed, debug })) ok++;
  } catch (err) {
    console.error(`ASC ${num} 失败:`, err.message);
  }
}
console.log(`\n完成: ${ok}/${nums.length}`);
process.exit(ok === nums.length ? 0 : 1);
