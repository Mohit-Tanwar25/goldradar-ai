"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface GoldPriceHistoryChartProps {
  data: Array<{
    date: string;
    GOLDM?: number | null;
    GOLDTEN?: number | null;
    GOLDGUINEA?: number | null;
    GOLDPETAL?: number | null;
  }>;
}

export const GoldPriceHistoryChart: React.FC<GoldPriceHistoryChartProps> = ({
  data,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-xs text-[#707784]">
        No historical price data available.
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
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
            tickFormatter={(val) => `₹${val.toLocaleString()}`}
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
            formatter={(value: any, name: any) => [
              value !== null ? formatINR(Number(value)) + "/g" : "—",
              `${name} (Prompt)`,
            ]}
            labelFormatter={(label) => `Session: ${label}`}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingBottom: "12px" }}
          />
          <Line
            type="monotone"
            dataKey="GOLDM"
            name="GOLDM (100g)"
            stroke="#17191D"
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="GOLDTEN"
            name="GOLDTEN (10g)"
            stroke="#B89137"
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="GOLDGUINEA"
            name="GOLDGUINEA (8g)"
            stroke="#0D8244"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="GOLDPETAL"
            name="GOLDPETAL (1g)"
            stroke="#2563EB"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
