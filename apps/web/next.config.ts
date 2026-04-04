import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the production Docker build (Dockerfile.prod).
  // Generates a standalone output directory with a minimal node_modules tree.
  output: "standalone",
};

export default nextConfig;
