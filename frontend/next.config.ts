import createNextIntlPlugin from "next-intl/plugin";
import type { NextConfig } from "next";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // مخرجات مستقلة — تقلّل حجم صورة الإنتاج بشكل كبير.
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
};

export default withNextIntl(nextConfig);
