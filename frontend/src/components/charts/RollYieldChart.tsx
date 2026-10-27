"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface RollYieldChartProps {
  data: Array<{
    date: string;
    symbol: string;
    annualized_spread_pct: number;
    regime: string;
  }>;
}

export const RollYieldChart: React.FC<RollYieldChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-xs text-[#707784]">
        No roll yield observations available.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
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
            tickFormatter={(val) => `${val.toFixed(0)}%`}
            orientation="right"
          />
          <ReferenceLine y={0} stroke="#707784" strokeDasharray="2 2" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#FFFFFF",
              borderColor: "#E7E9ED",
              borderRadius: "6px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
              fontSize: "11px",
              color: "#17191D",
            }}
            formatter={(value: any, _: any, item: any) => [
              `${Number(value).toFixed(2)}% p.a. (${item.payload.regime})`,
              `${item.payload.symbol} Annualized Spread`,
            ]}
            labelFormatter={(label) => `Session: ${label}`}
          />
          <Line
            type="monotone"
            dataKey="annualized_spread_pct"
            name="Roll Yield"
            stroke="#B89137"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
