"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface SpreadChartProps {
  data: Array<{
    date: string;
    spread: number;
    relative_pct: number;
    rolling_mean: number | null;
    upper_band: number | null;
    lower_band: number | null;
  }>;
  pairLabel: string;
}

export const SpreadChart: React.FC<SpreadChartProps> = ({ data, pairLabel }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-xs text-[#707784]">
        No historical spread records for this contract pair.
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid stroke="#E7E9ED" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={{ stroke: "#E7E9ED" }}
            minTickGap={40}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `₹${val.toFixed(0)}`}
            orientation="right"
          />
          <ReferenceLine y={0} stroke="#707784" strokeDasharray="3 3" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#FFFFFF",
              borderColor: "#E7E9ED",
              borderRadius: "6px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
              fontSize: "11px",
              color: "#17191D",
            }}
            formatter={(value: any, name: any) => [
              value !== null ? `₹${Number(value).toFixed(2)}/g` : "—",
              name,
            ]}
            labelFormatter={(label) => `Session: ${label}`}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingBottom: "12px" }}
          />

          {/* 2-Sigma Statistical Bands */}
          <Line
            type="monotone"
            dataKey="upper_band"
            name="+2σ Band"
            stroke="#9CA3AF"
            strokeDasharray="2 2"
            strokeWidth={1}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="lower_band"
            name="-2σ Band"
            stroke="#9CA3AF"
            strokeDasharray="2 2"
            strokeWidth={1}
            dot={false}
          />

          {/* 30-Day Rolling Mean */}
          <Line
            type="monotone"
            dataKey="rolling_mean"
            name="30D Mean"
            stroke="#B89137"
            strokeWidth={1.5}
            dot={false}
          />

          {/* Observed Spread */}
          <Line
            type="monotone"
            dataKey="spread"
            name={`Observed Spread (${pairLabel})`}
            stroke="#17191D"
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
