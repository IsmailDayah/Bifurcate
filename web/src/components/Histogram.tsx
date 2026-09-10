"use client";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, ReferenceLine } from "recharts";

export default function Histogram({
  counts,
  color = "#f59e0b",
  uniform,
  height = 180,
}: {
  counts: number[];
  color?: string;
  uniform?: number;
  height?: number;
}) {
  const data = counts.map((c, i) => ({ i, c }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
        <XAxis dataKey="i" hide />
        <YAxis hide />
        {uniform !== undefined && (
          <ReferenceLine y={uniform} stroke="#16a34a" strokeDasharray="4 4" />
        )}
        <Bar dataKey="c" fill={color} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
