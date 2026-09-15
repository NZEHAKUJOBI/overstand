import Image from "next/image";
import logo from "@/app/logo.png";

/**
 * Society crest — the cooperative's seal, a gold anchor and portico on a forest
 * field. The artwork is masked to its circle with transparent corners, so it
 * sits directly on the forest ground with no plate behind it.
 *
 * `className` handles layout as before; `size` is the intrinsic width Next.js
 * optimises for, so set it to the largest CSS size the call site renders.
 * The seal is decorative wherever the society name sits beside it, which is
 * every current call site — pass `alt` only if that stops being true.
 */
export function Crest({
  className,
  size = 64,
  priority = false,
  alt = "",
}: {
  className?: string;
  size?: number;
  priority?: boolean;
  alt?: string;
}) {
  return (
    <Image
      src={logo}
      alt={alt}
      width={size}
      height={size}
      priority={priority}
      className={className}
    />
  );
}
