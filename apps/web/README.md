This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Testing

> **Important**: Frontend tests MUST be run from the **host machine**, NOT from inside the Docker container.
> The `tukijuris-web-1` container does not install `devDependencies`, so `vitest` is not available inside it.

### Run all Vitest tests (canonical command)

```bash
cd apps/web
npx vitest run
```

### Run a focused subset

```bash
# Admin SaaS panel components only
cd apps/web
npx vitest run src/app/admin/_components/__tests__/
```

### Why not Docker?

`docker exec tukijuris-web-1 npx vitest run` will fail with `sh: vitest: not found`.
The production image skips `devDependencies`. Always run tests from the host where
`node_modules` is fully installed.

---

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
