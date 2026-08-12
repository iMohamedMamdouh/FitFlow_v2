import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // مخرجات مستقلة — تقلّل حجم صورة الإنتاج بشكل كبير.
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
