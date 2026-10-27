"use client";

import React, { useState, useEffect } from "react";
import { FuturesCurveResponse } from "@/types/api";
import { fetchFuturesCurve } from "@/lib/api";
import { KpiMetric } from "@/components/ui/KpiMetric";
import { FuturesCurveChart } from "@/components/charts/FuturesCurveChart";
import { RollYieldChart } from "@/components/charts/RollYieldChart";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { formatINR, formatDate } from "@/lib/utils";
import { Calendar, TrendingUp, Info } from "lucide-react";

export const FuturesCurveView: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [data, setData] = useState<FuturesCurveResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (dateStr?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchFuturesCurve(dateStr || undefined);
      setData(res);
      if (!selectedDate && res.selected_date) {
        setSelectedDate(res.selected_date);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load futures curve data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedDate);
  }, [selectedDate]);

  return (
    <div className="space-y-6">
      {/* 1. Header & Date Selector Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[#17191D] sm:text-2xl">
            Futures Term Structure & Carry Curve
          </h2>
          <p className="text-xs text-[#707784]">
            Forward price curve and calendar spread roll yield across MCX gold maturities.
          </p>
        </div>

        {/* Snapshot Selector */}
        {data?.available_dates && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#707784]">Snapshot Date:</span>
            <select
              value={selectedDate || data.selected_date}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1 text-xs font-medium text-[#17191D] outline-none cursor-pointer"
            >
              {data.available_dates.map((d) => (
                <option key={d} value={d}>
                  {formatDate(d)}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading && <LoadingSkeleton rows={4} height="h-28" />}
      {error && <ErrorMessage message={error} onRetry={() => loadData(selectedDate)} />}

      {!loading && !error && data && (
        <>
          {/* 2. Top Metrics */}
          <div className="grid grid-cols-2 gap-4 border-y border-[#E7E9ED] py-4 sm:grid-cols-4">
            <KpiMetric
              label="Observed Curve State"
              value={data.market_structure}
              subtext="Forward Price Slope"
              variant={data.market_structure === "Contango" ? "blue" : "default"}
            />
            <KpiMetric
              label="Median Annualized Carry"
              value={`+${data.median_annualized_roll_yield_pct}% p.a.`}
              subtext="Calendar Spread Roll Yield"
              variant="gold"
            />
            <KpiMetric
              label="Maturity Snapshots"
              value={`${data.curve_points.length} Expiries`}
              subtext="Active Forward Contracts"
            />
            <KpiMetric
              label="Snapshot Session"
              value={formatDate(data.selected_date)}
              subtext="Settlement Observation Date"
            />
          </div>

          {/* 3. Primary Forward Curve Chart */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-[#17191D]">
                MCX Gold Forward Curve Snapshot (₹ / gram vs Days to Expiry)
              </h3>
              <p className="text-[11px] text-[#707784]">
                Standardized 999 fine gold price along the forward maturity schedule.
              </p>
            </div>
            <FuturesCurveChart data={data.curve_points} />
          </div>

          {/* 4. Forward Curve Points Data Table */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <h3 className="text-sm font-semibold text-[#17191D] mb-1">
              Active Forward Contracts Breakdown
            </h3>
            <p className="text-[11px] text-[#707784] mb-4">
              All active maturities recorded on session {formatDate(data.selected_date)}.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                    <th className="py-2 font-medium">Contract Key</th>
                    <th className="py-2 font-medium">Symbol</th>
                    <th className="py-2 font-medium">Expiry Date</th>
                    <th className="py-2 text-right font-medium">Days to Expiry</th>
                    <th className="py-2 text-right font-medium">Expiry Rank</th>
                    <th className="py-2 text-right font-medium">Normalized Fine Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {data.curve_points.map((pt) => (
                    <tr key={pt.contract_key} className="hover:bg-[#FAFBFC]">
                      <td className="py-2 font-medium text-[#17191D]">{pt.contract_key}</td>
                      <td className="py-2 text-[#707784]">{pt.symbol}</td>
                      <td className="py-2 text-[#707784]">{formatDate(pt.expiry_date)}</td>
                      <td className="py-2 text-right text-[#707784]">{pt.days_to_expiry}d</td>
                      <td className="py-2 text-right text-[#707784]">#{pt.expiry_rank}</td>
                      <td className="py-2 text-right font-semibold text-[#B89137]">
                        {formatINR(pt.close_fine_per_gram)}/g
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 5. Historical Annualized Roll Yield History */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-[#17191D]">
                Annualized Roll Yield History (% p.a.)
              </h3>
              <p className="text-[11px] text-[#707784]">
                Implied annual carry return across consecutive calendar contract expiries.
              </p>
            </div>
            <RollYieldChart data={data.roll_yield_history} />
          </div>
        </>
      )}
    </div>
  );
};
