"use client";

import { ChevronLeft, ChevronRight, Expand, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Image from "next/image";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/format";

export function Gallery({ images, name }: { images: { url: string; alt: string }[]; name: string }) {
  const [index, setIndex] = useState(0);
  const [zoom, setZoom] = useState(false);
  const [origin, setOrigin] = useState("50% 50%");
  const [lightbox, setLightbox] = useState(false);
  const count = images.length;
  const go = (d: number) => setIndex((i) => (i + d + count) % count);

  useEffect(() => {
    if (!lightbox) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setLightbox(false);
      if (e.key === "ArrowRight") go(1);
      if (e.key === "ArrowLeft") go(-1);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  });

  if (!count) {
    return <div className="grid aspect-[4/3] place-items-center rounded-[24px] bg-platinum-100 text-platinum-400">Premier Parts</div>;
  }
  const current = images[index];

  return (
    <div className="flex flex-col gap-3">
      <div
        className="group relative aspect-[4/3] cursor-zoom-in overflow-hidden rounded-[24px] bg-platinum-100 ring-1 ring-platinum-200"
        onMouseMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setOrigin(`${((e.clientX - r.left) / r.width) * 100}% ${((e.clientY - r.top) / r.height) * 100}%`);
        }}
        onMouseEnter={() => setZoom(true)}
        onMouseLeave={() => setZoom(false)}
        onClick={() => setLightbox(true)}
      >
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.div
            key={current.url}
            className="absolute inset-0"
            initial={{ opacity: 0, scale: 1.02 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
          >
            <Image
              src={current.url}
              alt={current.alt || name}
              fill
              preload={index === 0}
              sizes="(min-width: 1024px) 640px, 100vw"
              className="object-cover transition-transform duration-300"
              style={{ transformOrigin: origin, transform: zoom ? "scale(1.8)" : "scale(1)" }}
            />
          </motion.div>
        </AnimatePresence>
        <span className="absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-[11.5px] font-semibold text-platinum-700 backdrop-blur">
          <Expand className="size-3.5" /> {index + 1}/{count}
        </span>
        {count > 1 && (
          <>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                go(-1);
              }}
              className="absolute top-1/2 left-3 grid size-10 -translate-y-1/2 place-items-center rounded-full bg-white/90 opacity-0 shadow transition group-hover:opacity-100"
              aria-label="Попереднє фото"
            >
              <ChevronLeft className="size-5" />
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                go(1);
              }}
              className="absolute top-1/2 right-3 grid size-10 -translate-y-1/2 place-items-center rounded-full bg-white/90 opacity-0 shadow transition group-hover:opacity-100"
              aria-label="Наступне фото"
            >
              <ChevronRight className="size-5" />
            </button>
          </>
        )}
      </div>
      {count > 1 && (
        <div className="flex gap-2 overflow-x-auto scrollbar-none">
          {images.map((img, i) => (
            <button
              key={img.url}
              type="button"
              onClick={() => setIndex(i)}
              className={cn(
                "relative h-18 w-24 shrink-0 overflow-hidden rounded-[12px] ring-2 transition",
                i === index ? "ring-gold-500" : "ring-transparent opacity-70 hover:opacity-100",
              )}
              aria-label={`Фото ${i + 1}`}
            >
              <Image src={img.url} alt="" fill sizes="96px" className="object-cover" />
            </button>
          ))}
        </div>
      )}
      {typeof document !== "undefined" &&
        createPortal(
          <AnimatePresence>
            {lightbox && (
              <motion.div
                className="fixed inset-0 z-[95] flex items-center justify-center bg-ink/92 p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setLightbox(false)}
              >
                <button type="button" className="absolute top-5 right-5 grid size-11 place-items-center rounded-full bg-white/10 text-white" aria-label="Закрити">
                  <X className="size-5" />
                </button>
                <motion.div
                  key={current.url}
                  initial={{ scale: 0.96, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="relative h-[80vh] w-full max-w-5xl"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Image src={current.url} alt={current.alt || name} fill sizes="100vw" className="object-contain" />
                </motion.div>
                {count > 1 && (
                  <>
                    <button type="button" onClick={(e) => { e.stopPropagation(); go(-1); }} className="absolute left-5 grid size-12 place-items-center rounded-full bg-white/10 text-white" aria-label="Попереднє фото">
                      <ChevronLeft className="size-6" />
                    </button>
                    <button type="button" onClick={(e) => { e.stopPropagation(); go(1); }} className="absolute right-5 grid size-12 place-items-center rounded-full bg-white/10 text-white" aria-label="Наступне фото">
                      <ChevronRight className="size-6" />
                    </button>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>,
          document.body,
        )}
    </div>
  );
}
