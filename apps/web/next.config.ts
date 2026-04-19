import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  output: isVercel ? undefined : "standalone",
};

export default nextConfig;
