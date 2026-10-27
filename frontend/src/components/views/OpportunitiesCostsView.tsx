"use client";

import React, { useState, useEffect } from "react";
import { OpportunitiesResponse } from "@/types/api";
import { fetchOpportunities } from "@/lib/api";
import { KpiMetric } from "@/components/ui/KpiMetric";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { formatINR, formatNumber, formatDate } from "@/lib/utils";
import { Filter, AlertTriangle, ShieldAlert } from "lucide-react";

export const OpportunitiesCostsView: React.FC = () => {
  const [costScenario, setCostScenario] = useState<string>("base");
  const [symbolFilter, setSymbolFilter] = useState<string>("ALL");
  const [data, setData] = useState<OpportunitiesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (sc: string, sym: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOpportunities(sc, sym, 50);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load opportunities data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(costScenario, symbolFilter);
  }, [costScenario, symbolFilter]);

  return (
    <div className="space-y-6">
      {/* 1. Header & Filters Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[#17191D] sm:text-2xl">
            Opportunities & Modeled Costs
          </h2>
          <p className="text-xs text-[#707784]">
            Screen relative price disparities after deducting mandatory statutory levies, exchange fees, and execution slippage.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1">
            <span className="text-[11px] font-medium text-[#707784]">Cost Scenario:</span>
            <select
              value={costScenario}
              onChange={(e) => setCostScenario(e.target.value)}
              className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer capitalize"
            >
              <option value="base">Base Case (Realistic)</option>
              <option value="low">Low Cost (Discount)</option>
              <option value="high">High Cost (Stress)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1">
            <span className="text-[11px] font-medium text-[#707784]">Symbol:</span>
            <select
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer"
            >
              <option value="ALL">All Contracts</option>
              <option value="GOLDM">GOLDM</option>
              <option value="GOLDTEN">GOLDTEN</option>
              <option value="GOLDGUINEA">GOLDGUINEA</option>
              <option value="GOLDPETAL">GOLDPETAL</option>
            </select>
          </div>
        </div>
      </div>

      {/* Mandatory Risk Disclosure Banner (Concise, no giant box) */}
      <div className="flex items-start gap-2 rounded-md border border-[#E7E9ED] bg-white px-3.5 py-2.5 text-[11px] text-[#707784]">
        <ShieldAlert className="h-4 w-4 shrink-0 text-[#B89137] mt-0.5" />
        <div>
          <strong className="text-[#17191D]">Research Simulation Notice:</strong> Gross spread differences do not equal free money. 
          Physical delivery logistics, tender-notice margins, and statutory levies create non-trivial trading friction. 
          Opportunities represent historical model evaluations and are never guaranteed profits.
        </div>
      </div>

      {loading && <LoadingSkeleton rows={4} height="h-28" />}
      {error && <ErrorMessage message={error} onRetry={() => loadData(costScenario, symbolFilter)} />}

      {!loading && !error && data && (
        <>
          {/* 2. Screening Funnel Summary */}
          <div>
            <h3 className="text-sm font-semibold text-[#17191D] mb-3">
              Screening Funnel ({costScenario.toUpperCase()} Cost Scenario)
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {data.funnel.map((step, idx) => (
                <div
                  key={step.stage}
                  className="rounded-lg border border-[#E7E9ED] bg-white p-4 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between text-[11px] text-[#707784] mb-1">
                      <span>Step 0{idx + 1}</span>
                      {idx === data.funnel.length - 1 && (
                        <span className="rounded bg-[#ECFDF5] px-1.5 py-0.5 text-[10px] font-semibold text-[#0D8244]">
                          Eligible
                        </span>
                      )}
                    </div>
                    <div className="text-lg font-bold text-[#17191D]">
                      {formatNumber(step.count)}
                    </div>
                    <div className="text-xs font-medium text-[#17191D] mt-0.5">
                      {step.stage}
                    </div>
                  </div>
                  <div className="mt-2 text-[10px] text-[#707784] border-t border-[#F0F2F5] pt-1.5">
                    {step.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3. Transaction Cost Breakdown Table */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <h3 className="text-sm font-semibold text-[#17191D] mb-1">
              Modeled Transaction Cost Assumptions
            </h3>
            <p className="text-[11px] text-[#707784] mb-4">
              Detailed statutory and execution cost schedule applied to both legs of each trade.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                    <th className="py-2 font-medium">Scenario</th>
                    <th className="py-2 font-medium">Brokerage</th>
                    <th className="py-2 font-medium">Exchange Fee</th>
                    <th className="py-2 font-medium">CTT (Sell Leg)</th>
                    <th className="py-2 font-medium">Stamp Duty</th>
                    <th className="py-2 font-medium">SEBI Turnover</th>
                    <th className="py-2 font-medium">GST Rate</th>
                    <th className="py-2 text-right font-medium">Modeled Slippage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {data.cost_scenarios_breakdown.map((sc) => {
                    const isSelected = sc.scenario === costScenario;
                    return (
                      <tr
                        key={sc.scenario}
                        className={isSelected ? "bg-[#FBF7EE] font-medium" : "hover:bg-[#FAFBFC]"}
                      >
                        <td className="py-2 text-[#17191D]">
                          {sc.label} {isSelected && <span className="text-[#B89137] text-[10px]">(Active)</span>}
                        </td>
                        <td className="py-2 text-[#707784]">₹{sc.brokerage_per_crore} / Cr</td>
                        <td className="py-2 text-[#707784]">{sc.exchange_fee_pct}%</td>
                        <td className="py-2 text-[#707784]">{sc.ctt_pct}%</td>
                        <td className="py-2 text-[#707784]">{sc.stamp_duty_pct}%</td>
                        <td className="py-2 text-[#707784]">{sc.sebi_turnover_pct}%</td>
                        <td className="py-2 text-[#707784]">{sc.gst_pct}%</td>
                        <td className="py-2 text-right font-semibold text-[#17191D]">
                          {sc.slippage_bps} bps
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 4. Filterable Opportunities Table */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#17191D]">
                  Screened Historical Relative-Value Opportunities
                </h3>
                <p className="text-[11px] text-[#707784]">
                  Showing candidate pairs where observed gross spread exceeds modeled round-trip costs.
                </p>
              </div>
              <span className="text-xs text-[#707784]">
                {data.opportunities.length} opportunities shown
              </span>
            </div>

            {data.opportunities.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                      <th className="py-2 font-medium">Session Date</th>
                      <th className="py-2 font-medium">Candidate Pair</th>
                      <th className="py-2 font-medium">Contracts</th>
                      <th className="py-2 text-right font-medium">Gross Spread</th>
                      <th className="py-2 text-right font-medium">Modeled Cost</th>
                      <th className="py-2 text-right font-medium">Estimated Net</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F0F2F5]">
                    {data.opportunities.map((opp) => (
                      <tr key={opp.candidate_id} className="hover:bg-[#FAFBFC]">
                        <td className="py-2 text-[#707784]">{formatDate(opp.date)}</td>
                        <td className="py-2 font-medium text-[#17191D]">
                          {opp.symbol_leg_a} – {opp.symbol_leg_b}
                        </td>
                        <td className="py-2 text-[11px] text-[#707784]">
                          {opp.contract_key_leg_a} / {opp.contract_key_leg_b}
                        </td>
                        <td className="py-2 text-right text-[#17191D]">
                          {formatINR(opp.fine_price_spread_per_gram)}/g
                        </td>
                        <td className="py-2 text-right text-[#707784]">
                          {formatINR(opp.modeled_round_trip_cost_per_gram)}/g
                        </td>
                        <td className="py-2 text-right font-semibold text-[#0D8244]">
                          {formatINR(opp.modeled_net_spread_per_gram, { showSign: true })}/g
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="rounded border border-dashed border-[#E7E9ED] p-8 text-center text-xs text-[#707784]">
                No opportunities matching the selected filters.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
