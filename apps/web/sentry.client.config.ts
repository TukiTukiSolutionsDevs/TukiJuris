/**
 * Sentry initialization for the Next.js client.
 *
 * Loaded only when NEXT_PUBLIC_SENTRY_DSN is set. In dev or staging without
 * a DSN, this file is effectively a no-op and adds zero runtime cost.
 *
 * Wire it up via apps/web/instrumentation-client.ts (Next 16) or import from
 * a root component once. For now this file is the placeholder; the actual
 * `@sentry/nextjs` package install + register call is deferred until
 * NEXT_PUBLIC_SENTRY_DSN is populated.
 *
 * Steps to enable in production:
 *   1. npm install --save @sentry/nextjs
 *   2. Set NEXT_PUBLIC_SENTRY_DSN in .env.production
 *   3. Uncomment the import + init block below
 *   4. Run `npx @sentry/wizard@latest -i nextjs` once to generate
 *      withSentryConfig + auth tokens for source-map upload
 */

// import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (typeof window !== "undefined" && dsn) {
  // Sentry.init({
  //   dsn,
  //   environment: process.env.NEXT_PUBLIC_APP_ENV || "production",
  //   tracesSampleRate: 0.1,
  //   replaysSessionSampleRate: 0.0,
  //   replaysOnErrorSampleRate: 1.0,
  // });
  // eslint-disable-next-line no-console
  console.info("[sentry] client config detected DSN — install @sentry/nextjs to activate");
}

export {};
