import { beforeEach, describe, expect, it } from "vitest";

import { formatPrice, pluralUk } from "@/lib/format";
import type { ProductCard } from "@/lib/types";
import { cleanVin, looksLikeVin } from "@/lib/vin";
import { cartCount, cartTotals, useCart } from "@/stores/cart";
import { fitsCar } from "@/stores/my-car";

const card = (over: Partial<ProductCard> = {}): ProductCard => ({
  id: 1,
  slug: "fara",
  name: "Фара",
  sku: "FP1",
  manufacturer: "TYC",
  image: null,
  price: 3438,
  sale_price: null,
  old_price: null,
  discount_percent: null,
  promotion_id: null,
  stock_status: "in_stock",
  generation_ids: [7],
  category: { slug: "fary", name: "Фари" },
  ...over,
});

describe("format", () => {
  it("formats hryvnia with non-breaking spaces", () => {
    expect(formatPrice(3438)).toBe("3 438 ₴");
    expect(formatPrice(0)).toBe("Ціну уточнюйте");
  });
  it("pluralizes Ukrainian", () => {
    const forms: [string, string, string] = ["деталь", "деталі", "деталей"];
    expect(pluralUk(1, forms)).toBe("деталь");
    expect(pluralUk(3, forms)).toBe("деталі");
    expect(pluralUk(11, forms)).toBe("деталей");
    expect(pluralUk(25, forms)).toBe("деталей");
  });
});

describe("vin", () => {
  it("detects VINs", () => {
    expect(looksLikeVin(" 1vwbp7a3xcc012345 ")).toBe(true);
    expect(looksLikeVin("1VWBP7A3XCC01234")).toBe(false);
    expect(looksLikeVin("1VWBP7A3XCC0I2345")).toBe(false);
    expect(cleanVin("wvw zzz-3cz")).toBe("WVWZZZ3CZ");
  });
});

describe("cart", () => {
  beforeEach(() => useCart.setState({ lines: [] }));

  it("merges quantities of the same product", () => {
    useCart.getState().add(card());
    useCart.getState().add(card(), 2);
    expect(useCart.getState().lines).toHaveLength(1);
    expect(cartCount(useCart.getState().lines)).toBe(3);
  });

  it("uses sale price for totals", () => {
    useCart.getState().add(card({ sale_price: 2922, old_price: 3438, discount_percent: 15 }), 2);
    const totals = cartTotals(useCart.getState().lines);
    expect(totals.total).toBe(5844);
    expect(totals.subtotal).toBe(6876);
    expect(totals.discount).toBe(1032);
  });

  it("clamps quantity between 1 and 99", () => {
    useCart.getState().add(card(), 500);
    expect(useCart.getState().lines[0].qty).toBe(99);
    useCart.getState().setQty(1, 0);
    expect(useCart.getState().lines[0].qty).toBe(1);
  });
});

describe("my car", () => {
  it("knows whether a part fits", () => {
    const car = { generation_id: 7 } as never;
    expect(fitsCar([7, 8], car)).toBe(true);
    expect(fitsCar([8], car)).toBe(false);
    expect(fitsCar([8], null)).toBeNull();
  });
});
