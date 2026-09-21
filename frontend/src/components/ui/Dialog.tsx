"use client";

import { X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/format";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  className?: string;
  /** "center" dialog on desktop, bottom sheet on phones; "side" slides from the right. */
  variant?: "center" | "side";
}

export function Dialog({ open, onClose, title, description, children, className, variant = "center" }: DialogProps) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";
    requestAnimationFrame(() => panel.current?.querySelector<HTMLElement>("input, button, [tabindex]")?.focus());
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previous?.focus?.();
    };
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const side = variant === "side";
  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[80] flex items-end justify-center sm:items-center" role="presentation">
          <motion.div
            className="absolute inset-0 bg-ink/45 backdrop-blur-[3px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            ref={panel}
            role="dialog"
            aria-modal="true"
            className={cn(
              "relative z-10 flex max-h-[92dvh] w-full flex-col overflow-hidden bg-white shadow-2xl",
              side
                ? "ml-auto h-full max-h-none self-stretch sm:max-w-md sm:rounded-l-[22px]"
                : "rounded-t-[24px] sm:max-w-lg sm:rounded-[24px]",
              className,
            )}
            initial={side ? { x: "100%" } : { y: 40, opacity: 0, scale: 0.98 }}
            animate={side ? { x: 0 } : { y: 0, opacity: 1, scale: 1 }}
            exit={side ? { x: "100%" } : { y: 30, opacity: 0, scale: 0.98 }}
            transition={{ type: "spring", damping: 30, stiffness: 320 }}
          >
            {(title || description) && (
              <div className="flex items-start gap-4 border-b border-platinum-100 px-6 pt-6 pb-4">
                <div className="min-w-0 flex-1">
                  {title && <h2 className="font-display text-lg font-medium text-ink">{title}</h2>}
                  {description && <p className="mt-1 text-sm text-platinum-600">{description}</p>}
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="-mt-1 -mr-2 grid size-9 place-items-center rounded-full text-platinum-500 hover:bg-platinum-100 hover:text-ink"
                  aria-label="Закрити"
                >
                  <X className="size-5" />
                </button>
              </div>
            )}
            <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
