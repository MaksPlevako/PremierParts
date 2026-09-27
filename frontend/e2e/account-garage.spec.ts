import { expect, test } from "@playwright/test";

test("garage saves a car chosen from the catalog", async ({ page }) => {
  const car = {
    generation_id: 101, make: "Volkswagen", make_slug: "volkswagen",
    model: "Passat", model_slug: "passat", generation_slug: "passat-b7",
    label: "Passat B7 (2010–2014)", full_label: "Volkswagen Passat B7 (2010–2014)", years_label: "2010–2014", market: "eu",
  };
  const savedCars: { id: number; nickname: string; vin: string; car: typeof car }[] = [];
  let postedGeneration: number | null = null;

  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    const respond = (json: unknown) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(json) });
    if (path === "/api/account/profile") return respond({ email: "buyer@example.com", first_name: "Олена", last_name: "", email_verified: true, phone: "", city: "", address: "", np_branch: "", providers: [] });
    if (path === "/api/account/config") return respond({ google: false, apple: false });
    if (path === "/api/account/garage" && method === "GET") return respond(savedCars);
    if (path === "/api/account/garage" && method === "POST") {
      const body = route.request().postDataJSON();
      postedGeneration = body.generation_id;
      const saved = { id: 1, nickname: body.nickname ?? "", vin: body.vin, car };
      savedCars.push(saved);
      return respond(saved);
    }
    if (path === "/api/account/orders") return respond([]);
    if (path === "/api/account/recommendations") return respond({ reason: "garage", products: [] });
    if (path === "/api/makes") return respond([{ id: 1, name: "Volkswagen", slug: "volkswagen", logo: null, is_popular: true, product_count: 1 }]);
    if (path === "/api/makes/volkswagen") return respond({ id: 1, name: "Volkswagen", slug: "volkswagen", logo: null, families: [{ family: "Passat", models: [{ id: 7, name: "Passat", slug: "passat", market: "eu", product_count: 1, generations: [{ id: 101, slug: "passat-b7", label: "Passat B7 (2010–2014)", years_label: "2010–2014", year_from: 2010, year_to: 2014, product_count: 1 }] }] }] });
    return route.continue();
  });

  await page.goto("/account");
  const save = page.getByRole("button", { name: "Додати авто" });
  await expect(save).toBeDisabled();
  await page.getByLabel("Марка авто").selectOption("volkswagen");
  await page.getByLabel("Модель авто").selectOption("7");
  await page.getByLabel("Покоління авто").selectOption("101");
  await expect(save).toBeEnabled();
  await expect(page.getByLabel("Назва авто")).toHaveCount(0);
  await save.click();

  await expect(page.getByText("Volkswagen Passat B7 (2010–2014)", { exact: true })).toBeVisible();
  expect(postedGeneration).toBe(101);
});
