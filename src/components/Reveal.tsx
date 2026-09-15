"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * Marks its child group visible once it enters the viewport, so sections settle
 * in rather than snapping. Travel is 10px and it fires once — anything larger
 * turns an institutional page into a demo reel.
 *
 * The visible state is written straight to the DOM rather than held in React
 * state: it is presentation only, it avoids a cascading render per section, and
 * it keeps the server and client markup identical. Reduced motion is handled in
 * CSS; a `noscript` rule in the layout covers JS being unavailable.
 */
export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const show = () => {
      node.dataset.shown = "true";
    };

    if (typeof IntersectionObserver === "undefined") {
      show();
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          show();
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal ${className}`}
      data-shown="false"
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
