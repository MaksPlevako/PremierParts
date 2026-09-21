import { Slot } from "./Slot";

import { cn } from "@/lib/format";

type Variant = "gold" | "dark" | "outline" | "ghost" | "light";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  gold: "bg-gold text-[#1e1606] shadow-gold hover:bg-[position:100%_0] transition-[background-position,transform,box-shadow] duration-500",
  dark: "bg-ink text-white hover:bg-graphite-700",
  outline: "bg-white text-ink ring-1 ring-platinum-200 hover:ring-gold-400 hover:text-gold-800",
  ghost: "text-ink hover:bg-platinum-100",
  light: "bg-white/10 text-white ring-1 ring-white/20 hover:bg-white/20",
};

const SIZES: Record<Size, string> = {
  sm: "h-9 px-3.5 text-[13px] rounded-[10px] gap-1.5",
  md: "h-11 px-5 text-sm rounded-xl gap-2",
  lg: "h-13 px-7 text-[15px] rounded-[14px] gap-2.5",
};

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  asChild?: boolean;
};

export function buttonClass(variant: Variant = "dark", size: Size = "md", className?: string) {
  return cn(
    "inline-flex items-center justify-center font-semibold whitespace-nowrap select-none transition-colors active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
    className,
  );
}

export function Button({ variant = "dark", size = "md", asChild, className, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={buttonClass(variant, size, className)} {...props} />;
}
