"use client";

import { CheckCircle2, Info } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { create } from "zustand";

import { cn } from "@/lib/format";

interface Toast {
  id: number;
  title: string;
  text?: string;
  tone?: "success" | "info";
  image?: string | null;
}

interface ToastState {
  toasts: Toast[];
  push: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: number) => void;
}

let seq = 0;

export const useToasts = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = ++seq;
    set((s) => ({ toasts: [...s.toasts.slice(-2), { ...toast, id }] }));
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 3800);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export const toast = (t: Omit<Toast, "id">) => useToasts.getState().push(t);

export function Toaster() {
  const { toasts, dismiss } = useToasts();
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[90] flex flex-col items-center gap-2 px-4 sm:right-6 sm:left-auto sm:items-end">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.button
            type="button"
            key={t.id}
            layout
            onClick={() => dismiss(t.id)}
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.96 }}
            transition={{ type: "spring", damping: 26, stiffness: 340 }}
            className="pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-2xl bg-ink px-4 py-3 text-left text-white shadow-2xl ring-1 ring-white/10"
          >
            {t.image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={t.image} alt="" className="size-11 shrink-0 rounded-lg object-cover" />
            ) : t.tone === "info" ? (
              <Info className="size-5 shrink-0 text-gold-300" />
            ) : (
              <CheckCircle2 className="size-5 shrink-0 text-gold-300" />
            )}
            <span className="min-w-0">
              <span className={cn("block text-sm font-semibold")}>{t.title}</span>
              {t.text && <span className="line-clamp-1 block text-xs text-platinum-300">{t.text}</span>}
            </span>
          </motion.button>
        ))}
      </AnimatePresence>
    </div>
  );
}
