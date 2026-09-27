import Image from "next/image";

type LogoTone = "black" | "white";

/** The icon-only Premier Parts mark used where a compact symbol is needed. */
export function LogoMark({ className, tone = "black" }: { className?: string; tone?: LogoTone }) {
  return (
    <Image
      src={`/brand/logo_${tone}_favicon.png`}
      alt=""
      width={1254}
      height={1254}
      className={className}
      aria-hidden="true"
    />
  );
}

/** The standalone vehicle mark used as a large decorative element. */
export function CarMark({ className }: { className?: string }) {
  return <LogoMark className={className} />;
}

/** The main stacked logo: car and wordmark. */
export function MainLogo({ className, tone = "black" }: { className?: string; tone?: LogoTone }) {
  return (
    <Image
      src={`/brand/logo_${tone}_main.png`}
      alt=""
      width={1254}
      height={1254}
      className={className}
      aria-hidden="true"
    />
  );
}

/** Horizontal logo: car first, wordmark second. */
export function Logo({ className, tone = "black" }: { className?: string; tone?: LogoTone }) {
  return (
    <span className={className}>
      <Image
        src={`/brand/logo_${tone}_row.png`}
        alt="Premier Parts"
        width={1916}
        height={821}
        className="h-auto w-[148px] sm:w-[172px]"
      />
    </span>
  );
}
