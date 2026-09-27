"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { useMyCar } from "@/stores/my-car";

const MyCarPicker = dynamic(() => import("./MyCarPicker").then((module) => module.MyCarPicker), { ssr: false });

export function LazyMyCarPicker() {
  const [hasOpened, setHasOpened] = useState(() => useMyCar.getState().pickerOpen);

  useEffect(() => useMyCar.subscribe((state) => {
    if (state.pickerOpen) setHasOpened(true);
  }), []);

  return hasOpened ? <MyCarPicker /> : null;
}
