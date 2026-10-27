"use client";

import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Line,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface FuturesCurveChartProps {
  data: Array<{
    contract_key: string;
    symbol: string;
    name: string;
    expiry_date: string;
    days_to_expiry: number;
    close_fine_per_gram: number;
    expiry_rank: number;
  }>;
}

export const FuturesCurveChart: React.FC<FuturesCurveChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-xs text-[#707784]">
        No forward curve points for the selected snapshot date.
      </div>
    );
  }

  // Group by symbol to plot distinct curves
  const goldm = data.filter((d) => d.symbol === "GOLDM");
  const goldten = data.filter((d) => d.symbol === "GOLDTEN");
  const guinea = data.filter((d) => d.symbol === "GOLDGUINEA");
  const petal = data.filter((d) => d.symbol === "GOLDPETAL");

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid stroke="#E7E9ED" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="days_to_expiry"
            name="Days to Expiry"
            unit="d"
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={{ stroke: "#E7E9ED" }}
          />
          <YAxis
            type="number"
            dataKey="close_fine_per_gram"
            name="Fine Price"
            domain={["auto", "auto"]}
            tick={{ fontSize: 10, fill: "#707784" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `₹${val.toFixed(0)}`}
            orientation="right"
          />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="rounded-md border border-[#E7E9ED] bg-white p-2.5 shadow-sm text-xs text-[#17191D]">
                    <div className="font-semibold text-xs mb-1">
                      {item.contract_key}
                    </div>
                    <div className="text-[11px] text-[#707784]">
                      Expiry: <span className="text-[#17191D] font-medium">{item.expiry_date}</span> ({item.days_to_expiry} days)
                    </div>
                    <div className="text-[11px] text-[#707784]">
                      Fine Price: <span className="text-[#17191D] font-medium">{formatINR(item.close_fine_per_gram)}/g</span>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingBottom: "12px" }}
          />
          {goldm.length > 0 && (
            <Scatter
              name="GOLDM"
              data={goldm}
              fill="#17191D"
              line={{ stroke: "#17191D", strokeWidth: 1.5 }}
            />
          )}
          {goldten.length > 0 && (
            <Scatter
              name="GOLDTEN"
              data={goldten}
              fill="#B89137"
              line={{ stroke: "#B89137", strokeWidth: 1.5 }}
            />
          )}
          {guinea.length > 0 && (
            <Scatter
              name="GOLDGUINEA"
              data={guinea}
              fill="#0D8244"
              line={{ stroke: "#0D8244", strokeWidth: 1.5 }}
            />
          )}
          {petal.length > 0 && (
            <Scatter
              name="GOLDPETAL"
              data={petal}
              fill="#2563EB"
              line={{ stroke: "#2563EB", strokeWidth: 1.5 }}
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
