import "server-only";

import { cookies } from "next/headers";

export const CAR_COOKIE = "pp_car";

/** «Моє авто» generation id stored by the client; read on the server to render fitted listings. */
export async function readCarCookie(): Promise<number | null> {
  const store = await cookies();
  const raw = store.get(CAR_COOKIE)?.value;
  const id = raw ? Number.parseInt(raw, 10) : NaN;
  return Number.isFinite(id) && id > 0 ? id : null;
}
