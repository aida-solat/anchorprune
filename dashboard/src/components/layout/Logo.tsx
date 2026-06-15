import Image from "next/image";

interface LogoProps {
  size?: number;
  className?: string;
}

// AnchorPrune brand mark: pruning shears.
// Same logo used in the app favicon (app/icon.png) and GitHub social preview.
export function Logo({ size = 24, className }: LogoProps) {
  return (
    <Image
      src="/logo.png"
      alt="AnchorPrune"
      width={size}
      height={size}
      priority
      className={className}
    />
  );
}
