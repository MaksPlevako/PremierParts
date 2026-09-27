import { expect, test } from "@playwright/test";

test("checkout rejects incomplete contact details before creating an order", async ({ page }) => {
  let orderPosted = false;
  await page.route("**/api/orders", (route) => {
    orderPosted = true;
    return route.fulfill({ status: 500, contentType: "application/json", body: "{}" });
  });

  await page.goto("/category/fary-perednie");
  const card = page.locator("article").filter({ has: page.getByRole("button", { name: "У кошик" }) }).first();
  await card.getByRole("button", { name: "У кошик" }).click();
  await page.goto("/checkout");
  await page.getByRole("button", { name: "Підтвердити замовлення" }).click();

  await expect(page.locator('[data-field="customer_name"] p')).toBeVisible();
  await expect(page.locator('[data-field="phone"] p')).toBeVisible();
  expect(orderPosted).toBe(false);
});
