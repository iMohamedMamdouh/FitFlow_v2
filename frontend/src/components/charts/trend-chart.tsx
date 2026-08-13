"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLocale, useTranslations } from "next-intl";

import { directionOf, type Locale } from "@/i18n/config";
import { formatAxisDate, formatDate, formatNumber } from "@/lib/format";

export type TrendPoint = { date: string; value: number };

/**
 * منحنى زمني واحد.
 *
 * Recharts لا يقلب نفسه مع `dir="rtl"`، فالاتجاه يُحسب من اللغة النشطة:
 * في العربية يُقرأ الزمن من اليمين لليسار ويقف المحور الرأسي يمينًا،
 * وفي الإنجليزية العكس. ربطه باللغة لا بقيمة ثابتة هو ما يجعل التبديل
 * بين اللغتين صحيحًا بلا نسختين من المكوّن.
 */
export function TrendChart({
  points,
  color = "var(--color-accent)",
  fractionDigits = 1,
  domain,
  unit,
}: {
  points: readonly TrendPoint[];
  color?: string;
  fractionDigits?: number;
  domain?: [number, number];
  unit?: string;
}) {
  const t = useTranslations("dashboard");
  const locale = useLocale() as Locale;
  const rtl = directionOf(locale) === "rtl";

  if (points.length < 2) {
    return (
      <div className="border-line text-subtle flex h-56 items-center justify-center rounded-lg border border-dashed text-sm">
        {t("notEnoughData")}
      </div>
    );
  }

  return (
    <div className="h-56 w-full" dir="ltr">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={[...points]} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="var(--color-line)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            reversed={rtl}
            tickFormatter={(value: string) => formatAxisDate(locale, value)}
            tick={{ fill: "var(--color-faint)", fontSize: 11 }}
            stroke="var(--color-line)"
            tickLine={false}
            minTickGap={28}
          />
          <YAxis
            orientation={rtl ? "right" : "left"}
            domain={domain ?? ["auto", "auto"]}
            tickFormatter={(value: number) => formatNumber(locale, value, fractionDigits)}
            tick={{ fill: "var(--color-faint)", fontSize: 11 }}
            stroke="var(--color-line)"
            tickLine={false}
            width={44}
          />
          <Tooltip
            labelFormatter={(value) => formatDate(locale, String(value))}
            formatter={(value) => [
              `${formatNumber(locale, Number(value), fractionDigits)}${unit ? ` ${unit}` : ""}`,
              "",
            ]}
            contentStyle={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-line)",
              borderRadius: "0.5rem",
              direction: rtl ? "rtl" : "ltr",
              fontSize: "0.8rem",
              color: "var(--color-ink)",
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 2, fill: color }}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
