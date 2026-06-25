"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Navigation hardening against two failure modes that leave the page
 * blank after the user presses the browser back/forward button.
 *
 * 1. bfcache restore — Chrome (and other browsers) freeze the whole
 *    DOM + JS state when you navigate away and restore it on back.
 *    None of React's effects re-run. If the page was mid-hydration or
 *    showing a loading state when frozen, you come back to a stale or
 *    blank view. `pageshow` with `event.persisted === true` signals
 *    this specific case; we reload to rehydrate cleanly.
 *
 * 2. popstate without bfcache — Next 16 + Turbopack in dev sometimes
 *    restores a history entry WITHOUT refiring hydration, leaving the
 *    document with just a `<div hidden>` suspense placeholder and no
 *    visible content. `router.refresh()` fetches a fresh RSC payload
 *    and forces React to re-render the current route.
 *
 * Mounted once at the root layout so both guards cover every route.
 * Renders nothing; all behaviour is side-effectful.
 */
export function BFCacheGuard() {
  const router = useRouter();

  useEffect(() => {
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        // Came back from bfcache — JS state is frozen. Only a full
        // reload rehydrates cleanly.
        window.location.reload();
      }
    };

    const onPopState = () => {
      // Browser back/forward. Force Next to refetch the RSC payload
      // for the restored route so stale/empty trees never win.
      router.refresh();
    };

    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("popstate", onPopState);
    return () => {
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("popstate", onPopState);
    };
  }, [router]);

  return null;
}
