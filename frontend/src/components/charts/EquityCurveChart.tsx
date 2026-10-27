"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface EquityCurveChartProps {
  data: Array<{
    date: string;
    trade_id: string;
    net_pnl: number;
    cum_net_pnl: number;
    running_peak: number;
    drawdown: number;
  }>;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-xs text-[#707784]">
        No completed trade executions to plot equity curve.
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0D8244" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0D8244" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="drawdownGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#D32F2F" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#D32F2F" stopOpacity={0.0} />
            </linearGradient>
          </defs>
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
            formatter={(value: any, name: any) => [
              formatINR(Number(value)),
              name,
            ]}
            labelFormatter={(label) => `Exit Date: ${label}`}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingBottom: "12px" }}
          />

          {/* Running Peak Line */}
          <Line
            type="stepAfter"
            dataKey="running_peak"
            name="Peak Equity"
            stroke="#9CA3AF"
            strokeDasharray="2 2"
            strokeWidth={1}
            dot={false}
          />

          {/* Cumulative Realized Equity Curve */}
          <Area
            type="monotone"
            dataKey="cum_net_pnl"
            name="Cumulative Net P&L (₹)"
            stroke="#0D8244"
            strokeWidth={2}
            fill="url(#equityGrad)"
            dot={false}
            activeDot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
