import { expect, test } from "@playwright/test";

const heroSearch = (page: import("@playwright/test").Page) => page.getByRole("combobox").first();

test("smart search understands a human query and leads to a product", async ({ page }) => {
  await page.goto("/");
  await heroSearch(page).fill("фара пасат B7");
  const panel = page.getByRole("listbox");
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Ми зрозуміли:")).toBeVisible();
  await expect(panel.getByText("Фари передні", { exact: true })).toBeVisible();

  await heroSearch(page).press("Enter");
  await expect(page).toHaveURL(/\/search\?q=/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("фара пасат B7");
  await page.locator("article a[href*='/product/']").first().click();
  await expect(page).toHaveURL(/\/product\//);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
});

test("add to cart and place an order", async ({ page }) => {
  await page.goto("/category/fary-perednie");
  const card = page.locator("article").filter({ has: page.getByRole("button", { name: "У кошик" }) }).first();
  await card.getByRole("button", { name: "У кошик" }).click();
  await expect(page.getByText("Додано в кошик")).toBeVisible();

  await page.goto("/cart");
  await expect(page.getByRole("heading", { name: "Кошик" })).toBeVisible();
  await page.getByRole("link", { name: "Оформити замовлення" }).click();

  await expect(page).toHaveURL(/\/checkout$/);
  await page.getByLabel("Ім'я та прізвище").fill("Тест Демо");
  await page.locator("input[type=tel]").fill("0634203993");
  await page.getByRole("button", { name: /Самовивіз у Києві/ }).click();
  await page.getByRole("button", { name: /Карткою при самовивозі/ }).click();
  await page.getByRole("button", { name: "Підтвердити замовлення" }).click();

  await expect(page).toHaveURL(/\/checkout\/success\/PP-\d+/, { timeout: 20_000 });
  await expect(page.getByRole("heading", { level: 1 })).toContainText("прийнято");
});

test("VIN in search offers «Моє авто» and the header chip remembers the car", async ({ page }) => {
  await page.goto("/");
  await heroSearch(page).fill("1VWBP7A3XCC012345");
  const panel = page.getByRole("listbox");
  await expect(panel.getByText("Ваше авто")).toBeVisible({ timeout: 15_000 });
  await panel.getByRole("button", { name: /деталей|Зробити моїм авто/ }).click();

  await expect(page).toHaveURL(/\/cars\/volkswagen\//);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Passat");
  await expect(page.locator("header").getByTitle(/Passat/).first()).toBeVisible();
});

test("catalog filters narrow the listing via the URL", async ({ page, isMobile }) => {
  test.skip(isMobile, "filters sidebar is desktop; mobile uses the sheet");
  await page.goto("/category/fary-perednie");
  await page.getByRole("button", { name: /^Ліва/ }).click();
  await expect(page).toHaveURL(/side=left/);
  await page.getByRole("button", { name: "Дешевші" }).click();
  await expect(page).toHaveURL(/sort=price_asc/);
});

test("legacy URLs redirect permanently", async ({ request }) => {
  const res = await request.get("/mark/544", { maxRedirects: 0 });
  expect(res.status()).toBe(301);
  expect(res.headers()["location"]).toContain("/cars/hyundai");
});
