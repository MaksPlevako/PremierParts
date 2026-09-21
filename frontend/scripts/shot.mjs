// Dev helper: node scripts/shot.mjs <path> <out.png> [width] [fullPage] [actions]
// actions: "type:<selector>:<text>" | "click:<selector>" | "wait:<ms>" | "hover:<selector>" separated by "|"
import { chromium } from "@playwright/test";

const [, , path = "/", out = "shot.png", width = "1440", full = "1", actions = ""] = process.argv;
const base = process.env.BASE_URL ?? "http://localhost:3000";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(width), height: Number(width) < 600 ? 844 : 900 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
await page.goto(base + path, { waitUntil: "networkidle" });
for (const step of actions.split("|").filter(Boolean)) {
  const [kind, sel, ...rest] = step.split(":");
  if (kind === "type") await page.locator(sel).first().fill(rest.join(":"));
  if (kind === "press") await page.locator(sel).first().press(rest.join(":"));
  if (kind === "click") await page.locator(sel).first().click();
  if (kind === "hover") await page.locator(sel).first().hover();
  if (kind === "wait") await page.waitForTimeout(Number(sel));
  if (kind === "scroll") await page.mouse.wheel(0, Number(sel));
}
await page.waitForTimeout(1200);
await page.screenshot({ path: out, fullPage: full === "1" });
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
console.log("saved", out);
await browser.close();
