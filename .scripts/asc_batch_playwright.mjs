#!/usr/bin/env node
/**
 * DEPRECATED: 勿用。会唤起本机 Edge，请改用 cursor-ide-browser MCP。
 */
import { chromium } from "playwright";
import { spawnSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const LOG_DIR = join(ROOT, ".logs/cursor");
const CDP_DIR = join(ROOT, ".tmp/asc-cdp");
mkdirSync(LOG_DIR, { recursive: true });
mkdirSync(CDP_DIR, { recursive: true });

const TOPICS = [
  105, 205, 210, 220, 225, 230, 235, 250, 255, 260, 270, 272, 274, 275, 280,
  310, 320, 321, 323, 325, 326, 330, 340, 350, 360, 405, 410, 420, 430, 440,
  450, 460, 470, 480, 505, 605, 606, 608, 610, 710, 712, 715, 718, 720, 730,
  740, 805, 808, 810, 815, 820, 825, 830, 835, 842, 848, 850, 855, 860, 862,
  865, 905, 908, 910, 912, 915, 920, 922, 924, 926, 928, 930, 932, 940, 942,
  944, 946, 948, 950, 952, 954, 958, 960, 962, 965, 970, 972, 974, 978, 980,
  985,
];

function parseArgs() {
  const args = process.argv.slice(2);
  let fromNum = null;
  let only = null;
  let skip606 = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--from" && args[i + 1]) fromNum = parseInt(args[++i], 10);
    if (args[i] === "--only" && args[i + 1])
      only = args[++i].split(",").map((x) => parseInt(x.trim(), 10));
    if (args[i] === "--skip-done") skip606 = true;
  }
  let list = only ?? TOPICS;
  if (fromNum) list = list.filter((n) => n >= fromNum);
  if (skip606) list = list.filter((n) => n !== 606);
  return list;
}

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  writeFileSync(join(LOG_DIR, "asc-export.log"), line + "\n", { flag: "a" });
}

async function exportTopic(page, num) {
  const url = `https://asc.fasb.org/${num}/showallinonepage`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(3000);

  const probe = await page.evaluate((n) => {
    const t = document.body.innerText || "";
    const re = new RegExp(`${n}-\\d{2}-\\d{2}-\\d+`);
    return {
      len: t.length,
      hasPara: re.test(t),
      title: document.title,
      cf: /cloudflare|verify you are human/i.test(t.slice(0, 2000)),
    };
  }, num);

  if (probe.cf) throw new Error("Cloudflare 拦截");
  if (probe.len < 5000 || !probe.hasPara)
    throw new Error(`正文过短或缺少段落号 len=${probe.len} title=${probe.title}`);

  const text = await page.evaluate(() => document.body.innerText);
  const cdpPath = join(CDP_DIR, `asc-${num}.json`);
  writeFileSync(
    cdpPath,
    JSON.stringify({ result: { value: text } }, null, 0),
    "utf8"
  );

  const py = spawnSync(
    "python",
    [join(__dirname, "asc_batch_export_runner.py"), cdpPath, String(num)],
    { cwd: ROOT, encoding: "utf8" }
  );
  if (py.status !== 0) throw new Error(py.stderr || py.stdout || "python failed");
  return cdpPath;
}

async function main() {
  const list = parseArgs();
  log(`开始 Playwright 批量导出 ${list.length} 个 Topic`);

  const browser = await chromium.launch({
    channel: "msedge",
    headless: false,
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  const failed = [];
  for (const num of list) {
    try {
      await exportTopic(page, num);
    } catch (e) {
      log(`FAIL ASC ${num}: ${e.message}`);
      failed.push({ num, error: e.message });
    }
  }

  await browser.close();
  log(`完成。成功 ${list.length - failed.length}/${list.length}，失败 ${failed.length}`);
  if (failed.length) {
    writeFileSync(
      join(LOG_DIR, "asc-export-failed.json"),
      JSON.stringify(failed, null, 2),
      "utf8"
    );
  }
}

main().catch((e) => {
  log(`致命错误: ${e.message}`);
  process.exit(1);
});
