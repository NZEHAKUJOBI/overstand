"use client";

import {
  useEffect,
  useLayoutEffect,
  useRef,
  type ReactNode,
} from "react";

/**
 * Marks its child group visible once it enters the viewport, so sections settle
 * in rather than snapping. Travel is 10px and it fires once — anything larger
 * turns an institutional page into a demo reel.
 *
 * The hidden state is applied by this component, never by the server and never
 * by a bare CSS rule. That ordering is the whole point: if the script is
 * blocked, throws, or hydration is broken by a DOM-rewriting browser
 * extension, nothing is ever hidden and the page reads exactly as the server
 * sent it. An animation that can blank the page when it fails is not worth
 * having, and the failure is silent — the markup is all present, just at zero
 * opacity, which looks identical to a site with no content.
 *
 * The visible state is written straight to the DOM rather than held in React
 * state: it is presentation only, it avoids a cascading render per section, and
 * it keeps the server and client markup identical.
 */

// useLayoutEffect has no server equivalent and warns if called during SSR, but
// on the client it runs before paint, which is what keeps the hide invisible.
const useBeforePaint =
  typeof window === "undefined" ? useEffect : useLayoutEffect;

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

  useBeforePaint(() => {
    const node = ref.current;
    if (!node) return;

    // No observer, or the reader has asked for less motion: leave it alone.
    if (typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) return;

    // Already on screen when we mount — hiding it now only to fade it back in
    // would flash. This also covers anything the reader scrolled past before
    // hydration finished.
    if (node.getBoundingClientRect().top < window.innerHeight) return;

    // Built before anything is hidden, so a constructor that throws leaves the
    // content visible rather than stranded at zero opacity.
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          delete node.dataset.reveal;
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 },
    );

    node.dataset.reveal = "hidden";
    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
