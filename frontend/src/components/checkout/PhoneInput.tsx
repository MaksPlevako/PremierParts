"use client";

import { cn } from "@/lib/format";

/** "+380631234567" -> "+380 63 123 45 67" */
export function formatPhone(raw: string): string {
  let digits = raw.replace(/\D/g, "");
  if (digits.startsWith("0")) digits = `38${digits}`;
  if (!digits.startsWith("380")) digits = `380${digits.replace(/^3?8?0?/, "")}`;
  digits = digits.slice(0, 12);
  const rest = digits.slice(3);
  const parts = [rest.slice(0, 2), rest.slice(2, 5), rest.slice(5, 7), rest.slice(7, 9)].filter(Boolean);
  return `+380${parts.length ? " " + parts.join(" ") : ""}`;
}

export function isValidPhone(value: string): boolean {
  return /^380\d{9}$/.test(value.replace(/\D/g, ""));
}

export function PhoneInput({
  value,
  onChange,
  invalid,
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  invalid?: boolean;
  id?: string;
}) {
  return (
    <input
      id={id}
      type="tel"
      inputMode="tel"
      autoComplete="tel"
      value={value}
      onChange={(e) => onChange(formatPhone(e.target.value))}
      placeholder="+380 XX XXX XX XX"
      className={cn(
        "h-12 rounded-[12px] px-4 font-medium tracking-wide ring-1 outline-none focus:ring-2",
        invalid ? "ring-danger focus:ring-danger" : "ring-platinum-200 focus:ring-gold-400",
      )}
    />
  );
}
