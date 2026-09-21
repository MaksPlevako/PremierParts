"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { CarRef } from "@/lib/types";

export const CAR_COOKIE = "pp_car";

function writeCookie(id: number | null) {
  if (typeof document === "undefined") return;
  const maxAge = id ? 60 * 60 * 24 * 365 : 0;
  document.cookie = `${CAR_COOKIE}=${id ?? ""}; path=/; max-age=${maxAge}; samesite=lax`;
}

interface MyCarState {
  car: CarRef | null;
  pickerOpen: boolean;
  setCar: (car: CarRef | null) => void;
  openPicker: () => void;
  closePicker: () => void;
}

/** «Моє авто»: kept in localStorage for the UI and mirrored to a cookie so server pages can filter by it. */
export const useMyCar = create<MyCarState>()(
  persist(
    (set) => ({
      car: null,
      pickerOpen: false,
      setCar: (car) => {
        writeCookie(car?.generation_id ?? null);
        set({ car, pickerOpen: false });
      },
      openPicker: () => set({ pickerOpen: true }),
      closePicker: () => set({ pickerOpen: false }),
    }),
    {
      name: "pp-my-car",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ car: state.car }),
      onRehydrateStorage: () => (state) => writeCookie(state?.car?.generation_id ?? null),
    },
  ),
);

export function fitsCar(generationIds: number[], car: CarRef | null): boolean | null {
  if (!car) return null;
  return generationIds.includes(car.generation_id);
}
