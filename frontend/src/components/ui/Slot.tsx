import { cloneElement, isValidElement, type ReactElement, type ReactNode } from "react";

import { cn } from "@/lib/format";

/** Minimal Radix-style Slot: merges className/props into the single child element. */
export function Slot({ children, className, ...props }: { children?: ReactNode; className?: string } & Record<string, unknown>) {
  if (!isValidElement(children)) return null;
  const child = children as ReactElement<{ className?: string }>;
  return cloneElement(child, { ...props, className: cn(className, child.props.className) } as never);
}
