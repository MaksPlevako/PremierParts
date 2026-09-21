const money = new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 0 });

/** 3438 -> "3 438 ₴" (non-breaking spaces); 0 -> "Ціну уточнюйте". */
export function formatPrice(value: number | null | undefined, zeroLabel = "Ціну уточнюйте"): string {
  if (!value) return zeroLabel;
  return `${money.format(Math.round(value)).replace(/\s/g, " ")} ₴`;
}

export function finalPrice(p: { price: number; sale_price: number | null }): number {
  return p.sale_price ?? p.price;
}

export function formatPhoneHref(number: string): string {
  return `tel:${number.replace(/[^\d+]/g, "")}`;
}

export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export function pluralUk(n: number, forms: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1];
  return forms[2];
}

export function formatCount(n: number): string {
  return money.format(n).replace(/\s/g, " ");
}
