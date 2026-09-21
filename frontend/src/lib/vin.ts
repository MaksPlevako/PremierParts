const VIN_RE = /^[A-HJ-NPR-Z0-9]{17}$/;

export function cleanVin(raw: string): string {
  return raw.replace(/[\s-]/g, "").toUpperCase();
}

/** 17 chars, Latin letters (no I/O/Q) and digits, at least one of each. */
export function looksLikeVin(raw: string): boolean {
  const vin = cleanVin(raw);
  return VIN_RE.test(vin) && /[A-Z]/.test(vin) && /\d/.test(vin);
}
