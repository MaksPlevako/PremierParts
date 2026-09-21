import type { ReactNode } from "react";

const P = { fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round", strokeLinejoin: "round" } as const;

const ICONS: Record<string, ReactNode> = {
  light: (
    <>
      <path {...P} d="M9 5h7c3 0 5 3 5 7s-2 7-5 7H9c-1.5 0-2-2-2-7s.5-7 2-7z" />
      <path {...P} d="M3 8h2.5M2.5 12H5M3 16h2.5M13 9.5a2.5 2.5 0 1 1 0 5" />
    </>
  ),
  headlight: (
    <>
      <path {...P} d="M4 7.5C4 6 5 5 6.5 5H17c2.5 0 4 3 4 7s-1.5 7-4 7H6.5C5 19 4 18 4 16.5z" />
      <circle {...P} cx="15" cy="12" r="3" />
      <path {...P} d="M7 9h3M7 12h2M7 15h3" />
    </>
  ),
  taillight: (
    <>
      <path {...P} d="M4 6h11l5 3v6l-5 3H4z" />
      <path {...P} d="M8 6v12M4 12h4" />
    </>
  ),
  foglight: (
    <>
      <circle {...P} cx="13" cy="12" r="6" />
      <path {...P} d="M3 9h3M2.5 12H6M3 15h3M13 9v6" />
    </>
  ),
  "turn-signal": (
    <>
      <path {...P} d="M5 8h9l5 4-5 4H5z" />
      <path {...P} d="M8.5 10.5 10 12l-1.5 1.5" />
    </>
  ),
  body: (
    <>
      <path {...P} d="M2.5 15.5l1.8-4.6A3 3 0 0 1 7.1 9h9.8a3 3 0 0 1 2.8 1.9l1.8 4.6V18H2.5zM6 9l1.5-3h9L18 9" />
      <circle {...P} cx="7" cy="18" r="1.8" />
      <circle {...P} cx="17" cy="18" r="1.8" />
    </>
  ),
  hood: <path {...P} d="M4 16c2-6 5-9 8-9s6 3 8 9l-3 2H7zM9 10.5l3 1.5 3-1.5" />,
  panel: (
    <>
      <rect {...P} x="3" y="7" width="18" height="10" rx="2" />
      <path {...P} d="M7 7v10M17 7v10M7 12h10" />
    </>
  ),
  fender: <path {...P} d="M3 17c0-5 3-9 8-10 4-1 8 1 10 4v6h-4a5 5 0 0 0-10 0z" />,
  bumper: (
    <>
      <path {...P} d="M3 10c0-1 1-2 2-2h14c1 0 2 1 2 2v3c0 2-2 3-4 3H7c-2 0-4-1-4-3z" />
      <path {...P} d="M7 12h10" />
    </>
  ),
  door: (
    <>
      <path {...P} d="M6 3h9l4 5v13H6z" />
      <path {...P} d="M6 9h13M15 14h2" />
    </>
  ),
  grille: (
    <>
      <rect {...P} x="3" y="7" width="18" height="10" rx="3" />
      <path {...P} d="M7 7v10M11 7v10M15 7v10M19 8v8" />
    </>
  ),
  trunk: <path {...P} d="M4 12l3-6h10l3 6v6H4zM4 12h16M10 15h4" />,
  shield: <path {...P} d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z" />,
  frame: (
    <>
      <rect {...P} x="4" y="5" width="16" height="14" rx="2" />
      <path {...P} d="M4 10h16M4 14h16M9 5v14M15 5v14" />
    </>
  ),
  strut: (
    <>
      <path {...P} d="M5 19 19 5" />
      <path {...P} d="m9 13 2 2M13 9l2 2" />
      <circle {...P} cx="4" cy="20" r="1.5" />
      <circle {...P} cx="20" cy="4" r="1.5" />
    </>
  ),
  tank: (
    <>
      <path {...P} d="M7 6h10a2 2 0 0 1 2 2v10a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V8a2 2 0 0 1 2-2z" />
      <path {...P} d="M10 3h4v3h-4zM5 13h14" />
    </>
  ),
  radiator: (
    <>
      <rect {...P} x="3" y="5" width="18" height="14" rx="2" />
      <path {...P} d="M7 8v8M10.3 8v8M13.6 8v8M17 8v8" />
    </>
  ),
  fan: (
    <>
      <circle {...P} cx="12" cy="12" r="1.8" />
      <path {...P} d="M12 10.2c0-3 1-6 4-6 1.5 0 2 1.5 1 3l-3.4 3.6M13.8 12c3 0 6 1 6 4 0 1.5-1.5 2-3 1l-3.6-3.4M12 13.8c0 3-1 6-4 6-1.5 0-2-1.5-1-3l3.4-3.6M10.2 12c-3 0-6-1-6-4 0-1.5 1.5-2 3-1l3.6 3.4" />
    </>
  ),
  mirror: (
    <path
      {...P}
      d="M4 7.5C4 5.6 5.6 4 7.5 4h9C18.4 4 20 5.6 20 7.5v3c0 2.5-2 4.5-4.5 4.5h-8C5.6 15 4 13.4 4 11.5zM12 15v5M8.5 20h7"
    />
  ),
  glass: <path {...P} d="M6 6h12l3 12H3zM9 9.5l-1.5 5" />,
  "window-lift": (
    <>
      <path {...P} d="M5 4h14v9H5z" />
      <path {...P} d="M12 13v7M9 17l3 3 3-3" />
    </>
  ),
  wiper: <path {...P} d="M4 18 18 6M18 6l2 2M8 18h-4" />,
  exhaust: <path {...P} d="M2 14h9a3 3 0 0 0 3-3V9h4a3 3 0 0 1 0 6h-1M14 12h3M19 18c1 0 1.5-.8 1.5-1.5" />,
};

export function CategoryIcon({ name, className }: { name: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      {ICONS[name] ?? ICONS.body}
    </svg>
  );
}
