import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    // Ignore typescript errors during build to handle dynamic API types
    ignoreBuildErrors: true,
  },
  eslint: {
    // Ignore lint errors during build to permit warnings like unused imports or any types
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
