import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // توقيع الـ Server Action مفروض من React: (prevState, formData).
      // بعض الأفعال لا تحتاج أحدهما، وإسقاطه من التوقيع غير ممكن — فنتفق
      // على البادئة `_` كإعلان صريح بأن المعامل مقصود وغير مستخدَم.
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
