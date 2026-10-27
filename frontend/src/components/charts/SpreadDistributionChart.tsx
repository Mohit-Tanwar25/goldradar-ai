"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface SpreadDistributionChartProps {
  data: Array<{
    bin_center: number;
    bin_start: number;
    bin_end: number;
    count: number;
  }>;
}

export const SpreadDistributionChart: React.FC<SpreadDistributionChartProps> = ({
  data,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-xs text-[#707784]">
        Insufficient distribution observations.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid stroke="#E7E9ED" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="bin_center"
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={{ stroke: "#E7E9ED" }}
            tickFormatter={(val) => `₹${val}`}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={false}
            orientation="right"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#FFFFFF",
              borderColor: "#E7E9ED",
              borderRadius: "6px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
              fontSize: "11px",
              color: "#17191D",
            }}
            formatter={(value: any) => [`${value} sessions`, "Frequency"]}
            labelFormatter={(label) => `Spread Range: ~₹${label}/g`}
          />
          <Bar dataKey="count" fill="#B89137" radius={[2, 2, 0, 0]} opacity={0.85} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
