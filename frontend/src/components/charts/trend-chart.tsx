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
import { useTranslations } from "next-intl";

import { formatDate, formatNumber } from "@/lib/format";

export type TrendPoint = { date: string; value: number };

/**
 * منحنى زمني واحد (الخطوة 7.8).
 *
 * ملاحظتان عن الاتجاه: المحور الأفقي `reversed` ليقرأ الزمن من اليمين
 * لليسار كبقية الواجهة، والمحور الرأسي على اليمين للسبب نفسه. Recharts
 * لا يقلب نفسه تلقائيًا مع `dir="rtl"`.
 */
export function TrendChart({
  points,
  color = "var(--color-primary)",
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

  if (points.length < 2) {
    return <p className="text-muted py-8 text-center text-sm">{t("notEnoughData")}</p>;
  }

  return (
    <div className="h-56 w-full" dir="ltr">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={[...points]} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            reversed
            tickFormatter={(value: string) => formatDate(value)}
            tick={{ fill: "var(--color-muted)", fontSize: 11 }}
            stroke="var(--color-border)"
            minTickGap={24}
          />
          <YAxis
            orientation="right"
            domain={domain ?? ["auto", "auto"]}
            tickFormatter={(value: number) => formatNumber(value, fractionDigits)}
            tick={{ fill: "var(--color-muted)", fontSize: 11 }}
            stroke="var(--color-border)"
            width={44}
          />
          <Tooltip
            labelFormatter={(value) => formatDate(String(value))}
            formatter={(value) => [
              `${formatNumber(Number(value), fractionDigits)}${unit ? ` ${unit}` : ""}`,
              "",
            ]}
            contentStyle={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "0.5rem",
              direction: "rtl",
              fontSize: "0.8rem",
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
