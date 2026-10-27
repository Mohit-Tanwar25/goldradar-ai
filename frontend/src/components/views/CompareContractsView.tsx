"use client";

import React, { useState, useEffect } from "react";
import { CompareContractsResponse, ContractSymbol } from "@/types/api";
import { fetchCompareContracts } from "@/lib/api";
import { KpiMetric } from "@/components/ui/KpiMetric";
import { SpreadChart } from "@/components/charts/SpreadChart";
import { SpreadDistributionChart } from "@/components/charts/SpreadDistributionChart";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { formatINR, formatPct } from "@/lib/utils";
import { Info, HelpCircle } from "lucide-react";

const CONTRACT_OPTIONS: ContractSymbol[] = [
  "GOLDM",
  "GOLDTEN",
  "GOLDGUINEA",
  "GOLDPETAL",
];

export const CompareContractsView: React.FC = () => {
  const [symbolA, setSymbolA] = useState<ContractSymbol>("GOLDM");
  const [symbolB, setSymbolB] = useState<ContractSymbol>("GOLDTEN");
  const [liquidityFilter, setLiquidityFilter] = useState<boolean>(false);
  const [showFormula, setShowFormula] = useState<boolean>(false);

  const [data, setData] = useState<CompareContractsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (symA: ContractSymbol, symB: ContractSymbol, liq: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCompareContracts(symA, symB, liq);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load contract comparison data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(symbolA, symbolB, liquidityFilter);
  }, [symbolA, symbolB, liquidityFilter]);

  const handleSwap = () => {
    setSymbolA(symbolB);
    setSymbolB(symbolA);
  };

  return (
    <div className="space-y-6">
      {/* 1. Page Header & Compact Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[#17191D] sm:text-2xl">
            Compare Contracts
          </h2>
          <p className="text-xs text-[#707784]">
            Inspect price differences and historical spread parity on a standardized 999 fine gold basis.
          </p>
        </div>

        {/* Compact Single Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2 py-1">
            <span className="text-[11px] font-medium text-[#707784]">Leg A:</span>
            <select
              value={symbolA}
              onChange={(e) => {
                const newA = e.target.value as ContractSymbol;
                if (newA === symbolB) {
                  setSymbolB(symbolA);
                }
                setSymbolA(newA);
              }}
              className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer"
            >
              {CONTRACT_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleSwap}
            className="rounded border border-[#E7E9ED] bg-white px-2 py-1 text-xs text-[#707784] hover:bg-[#F1F3F6] hover:text-[#17191D] transition-colors"
            title="Swap base and comparison leg"
          >
            ⇄
          </button>

          <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2 py-1">
            <span className="text-[11px] font-medium text-[#707784]">Leg B:</span>
            <select
              value={symbolB}
              onChange={(e) => {
                const newB = e.target.value as ContractSymbol;
                if (newB === symbolA) {
                  setSymbolA(symbolB);
                }
                setSymbolB(newB);
              }}
              className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer"
            >
              {CONTRACT_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-1.5 text-xs text-[#707784] ml-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={liquidityFilter}
              onChange={(e) => setLiquidityFilter(e.target.checked)}
              className="rounded border-[#E7E9ED] text-[#B89137] focus:ring-0"
            />
            <span>Traded volume only</span>
          </label>
        </div>
      </div>

      {/* Expandable Mathematical Normalization Tooltip */}
      <div className="text-xs text-[#707784]">
        <button
          onClick={() => setShowFormula(!showFormula)}
          className="flex items-center gap-1 text-[11px] font-medium text-[#B89137] hover:underline"
        >
          <HelpCircle className="h-3 w-3" />
          <span>{showFormula ? "Hide" : "How is fine-gold price normalized?"}</span>
        </button>

        {showFormula && (
          <div className="mt-2 rounded-md border border-[#E7E9ED] bg-white p-3 text-xs leading-relaxed text-[#17191D]">
            <strong className="text-[#B89137]">Fine Gold Parity Equation:</strong>{" "}
            <code>Normalized Price (₹/g) = (Raw Quoted Price / Quotation Divisor) × (Purity Fineness / 0.999)</code>
            <p className="mt-1 text-[#707784] text-[11px]">
              A positive spread ({symbolA} &gt; {symbolB}) means {symbolA} trades at a pure-gold premium. A negative spread indicates a discount. Differences reflect lot liquidity and delivery friction.
            </p>
          </div>
        )}
      </div>

      {loading && <LoadingSkeleton rows={4} height="h-28" />}
      {error && <ErrorMessage message={error} onRetry={() => loadData(symbolA, symbolB, liquidityFilter)} />}

      {!loading && !error && data && (
        <>
          {/* 2. Key Spread Statistics Row */}
          <div className="grid grid-cols-2 gap-4 border-y border-[#E7E9ED] py-4 sm:grid-cols-3 lg:grid-cols-6">
            <KpiMetric
              label="Latest Observed Spread"
              value={formatINR(data.statistics.latest_spread) + "/g"}
              subtext={`Relative: ${formatPct(data.statistics.latest_relative_pct)}`}
              variant="gold"
            />
            <KpiMetric
              label="Mean Historical Spread"
              value={formatINR(data.statistics.mean_spread) + "/g"}
              subtext="Historical Benchmark"
            />
            <KpiMetric
              label="Median Spread"
              value={formatINR(data.statistics.median_spread) + "/g"}
              subtext="50th Percentile"
            />
            <KpiMetric
              label="Spread Std Dev (σ)"
              value={`±₹${data.statistics.std_spread.toFixed(2)}`}
              subtext="Dispersion Volatility"
            />
            <KpiMetric
              label="Historical Range"
              value={`₹${data.statistics.min_spread.toFixed(0)} to ₹${data.statistics.max_spread.toFixed(0)}`}
              subtext="Min / Max Observed"
            />
            <KpiMetric
              label="Observations"
              value={`${data.statistics.total_observations} Sessions`}
              subtext="Concurrent Trading Days"
            />
          </div>

          {/* 3. Primary Historical Spread Chart */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-[#17191D]">
                Historical Normalized Spread: {symbolA} – {symbolB} (₹ / gram)
              </h3>
              <p className="text-[11px] text-[#707784]">
                With 30-day moving average and ±2 standard deviation rolling volatility channels.
              </p>
            </div>
            <SpreadChart
              data={data.timeseries}
              pairLabel={`${symbolA} – ${symbolB}`}
            />
          </div>

          {/* 4. Side-by-Side: Spread Distribution & Contract Spec Comparison */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Spread Distribution Histogram */}
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-[#17191D]">
                  Spread Distribution Histogram
                </h3>
                <p className="text-[11px] text-[#707784]">
                  Empirical frequency of spread observations across historical sessions.
                </p>
              </div>
              <SpreadDistributionChart data={data.distribution} />
            </div>

            {/* Specifications Comparison Table */}
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-5 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#17191D] mb-1">
                  Contract Specifications Comparison
                </h3>
                <p className="text-[11px] text-[#707784] mb-4">
                  Physical and quotation attributes driving relative pricing friction.
                </p>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                        <th className="py-2 font-medium">Attribute</th>
                        <th className="py-2 font-medium">{symbolA}</th>
                        <th className="py-2 font-medium">{symbolB}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F0F2F5]">
                      <tr>
                        <td className="py-2 text-[#707784]">Trading Unit (Lot)</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_a.trading_unit}</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_b.trading_unit}</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-[#707784]">Quotation Divisor</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_a.quotation_unit}</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_b.quotation_unit}</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-[#707784]">Purity Fineness</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_a.purity}</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_b.purity}</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-[#707784]">Delivery Settlement</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_a.delivery_logic}</td>
                        <td className="py-2 font-medium text-[#17191D]">{data.contract_b.delivery_logic}</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-[#707784]">Latest Fine Price</td>
                        <td className="py-2 font-medium text-[#B89137]">
                          {data.contract_a.latest_fine_price ? formatINR(data.contract_a.latest_fine_price) + "/g" : "—"}
                        </td>
                        <td className="py-2 font-medium text-[#B89137]">
                          {data.contract_b.latest_fine_price ? formatINR(data.contract_b.latest_fine_price) + "/g" : "—"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 text-[10px] text-[#707784] border-t border-[#F0F2F5] pt-2">
                All spreads are measured in Indian Rupees (₹) per gram of 999 fine gold equivalent.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
