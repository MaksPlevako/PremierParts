"use client";

import { CheckCircle2, Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Dialog } from "@/components/ui/Dialog";
import { browserApi } from "@/lib/browser-api";
import { formatPrice } from "@/lib/format";
import type { ProductCard } from "@/lib/types";
import { useMyCar } from "@/stores/my-car";

import { PhoneInput, isValidPhone } from "../checkout/PhoneInput";

export function QuickOrderDialog({
  product,
  open,
  onClose,
  mode = "buy",
}: {
  product: ProductCard;
  open: boolean;
  onClose: () => void;
  mode?: "buy" | "ask";
}) {
  const t = useTranslations();
  const car = useMyCar((s) => s.car);
  const [phone, setPhone] = useState("+380");
  const [name, setName] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [number, setNumber] = useState("");

  const submit = async () => {
    if (!isValidPhone(phone)) return setState("error");
    setState("sending");
    try {
      const res = await browserApi.quickOrder({
        phone,
        name,
        product_id: product.id,
        note: mode === "ask" ? "Запит ціни" : "",
        car_generation_id: car?.generation_id ?? null,
      });
      setNumber(res.number);
      setState("done");
    } catch {
      setState("error");
    }
  };

  const price = product.sale_price ?? product.price;
  return (
    <Dialog
      open={open}
      onClose={() => {
        onClose();
        setTimeout(() => setState("idle"), 300);
      }}
      title={mode === "ask" ? t("quick.askTitle") : t("quick.title")}
      description={mode === "ask" ? t("quick.askText") : t("quick.text")}
    >
      <div className="flex flex-col gap-4 p-6">
        <div className="flex items-center gap-3 rounded-[14px] bg-platinum-50 p-3">
          {product.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image} alt="" className="size-14 rounded-[10px] object-cover" />
          )}
          <div className="min-w-0">
            <p className="line-clamp-2 text-[13.5px] font-semibold">{product.name}</p>
            <p className="font-display text-[14px]">{formatPrice(price, t("common.priceOnRequest"))}</p>
          </div>
        </div>
        {state === "done" ? (
          <div className="flex items-start gap-3 rounded-[14px] bg-success-soft p-4 text-success">
            <CheckCircle2 className="size-5 shrink-0" />
            <p className="text-[14px] font-semibold">{t("quick.done", { number })}</p>
          </div>
        ) : (
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
          >
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("checkout.name")}
              className="h-12 rounded-[12px] px-4 ring-1 ring-platinum-200 outline-none focus:ring-2 focus:ring-gold-400"
            />
            <PhoneInput value={phone} onChange={setPhone} invalid={state === "error"} />
            {state === "error" && <p className="text-[13px] text-danger">{t("checkout.phoneInvalid")}</p>}
            <button
              type="submit"
              disabled={state === "sending"}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-[14px] bg-gold font-bold text-[#1e1606] shadow-gold"
            >
              {state === "sending" && <Loader2 className="size-4 animate-spin" />}
              {t("quick.send")}
            </button>
          </form>
        )}
      </div>
    </Dialog>
  );
}
