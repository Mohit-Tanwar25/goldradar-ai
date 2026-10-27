"use client";

import React, { useState, useEffect } from "react";
import { BacktestResponse } from "@/types/api";
import { fetchBacktest } from "@/lib/api";
import { KpiMetric } from "@/components/ui/KpiMetric";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { formatINR, formatPct, formatNumber, formatDate } from "@/lib/utils";
import { ShieldCheck, TrendingDown, Layers, FileSpreadsheet } from "lucide-react";

export const BacktestPerformanceView: React.FC = () => {
  const [costScenario, setCostScenario] = useState<string>("base");
  const [strategy, setStrategy] = useState<string>("All Strategies");
  const [fold, setFold] = useState<string>("All Folds");

  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (sc: string, strat: string, f: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchBacktest(sc, strat, f);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load backtest performance data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(costScenario, strategy, fold);
  }, [costScenario, strategy, fold]);

  return (
    <div className="space-y-6">
      {/* 1. Header & Filters Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[#17191D] sm:text-2xl">
            Walk-Forward Backtest Performance
          </h2>
          <p className="text-xs text-[#707784]">
            Strict anchored historical walk-forward simulation across 10 out-of-sample testing folds.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2 py-1">
            <span className="text-[11px] font-medium text-[#707784]">Scenario:</span>
            <select
              value={costScenario}
              onChange={(e) => setCostScenario(e.target.value)}
              className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer capitalize"
            >
              <option value="base">Base Scenario</option>
              <option value="low">Low Cost</option>
              <option value="high">High Cost</option>
            </select>
          </div>

          {data?.available_strategies && (
            <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2 py-1">
              <span className="text-[11px] font-medium text-[#707784]">Strategy:</span>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer"
              >
                {data.available_strategies.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          )}

          {data?.available_folds && (
            <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2 py-1">
              <span className="text-[11px] font-medium text-[#707784]">Fold:</span>
              <select
                value={fold}
                onChange={(e) => setFold(e.target.value)}
                className="text-xs font-semibold text-[#17191D] bg-transparent outline-none cursor-pointer"
              >
                {data.available_folds.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {loading && <LoadingSkeleton rows={4} height="h-28" />}
      {error && <ErrorMessage message={error} onRetry={() => loadData(costScenario, strategy, fold)} />}

      {!loading && !error && data && (
        <>
          {/* 2. Executive KPIs Row (6 compact metrics) */}
          <div className="grid grid-cols-2 gap-4 border-y border-[#E7E9ED] py-4 sm:grid-cols-3 lg:grid-cols-6">
            <KpiMetric
              label="Net Strategy P&L"
              value={formatINR(data.kpis.net_pnl_inr, { showSign: true })}
              subtext="Realized Historical [Net]"
              variant={data.kpis.net_pnl_inr >= 0 ? "positive" : "negative"}
            />
            <KpiMetric
              label="Gross P&L"
              value={formatINR(data.kpis.gross_pnl_inr, { showSign: true })}
              subtext="Before Deducting Fees"
            />
            <KpiMetric
              label="Modeled Transaction Costs"
              value={formatINR(data.kpis.total_costs_inr)}
              subtext="Statutory + Exchange + Slippage"
              variant="negative"
            />
            <KpiMetric
              label="Win Rate"
              value={formatPct(data.kpis.win_rate_pct)}
              subtext={`${data.kpis.winning_trades}W / ${data.kpis.losing_trades}L`}
              variant="default"
            />
            <KpiMetric
              label="Max Drawdown"
              value={formatINR(data.kpis.realized_max_drawdown_inr)}
              subtext="Peak-to-Trough Decline"
              variant="negative"
            />
            <KpiMetric
              label="Profit Factor"
              value={data.kpis.profit_factor ? data.kpis.profit_factor.toFixed(2) : "—"}
              subtext={`Avg Holding: ${data.kpis.mean_holding_days.toFixed(1)}d`}
            />
          </div>

          {/* Mathematical Reconciliation Banner */}
          <div className="flex items-center justify-between rounded-md border border-[#E7E9ED] bg-white px-3.5 py-2 text-[11px] text-[#707784]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[#0D8244]" />
              <span>
                <strong>Mathematical Reconciliation Status:</strong> Gross P&L ({formatINR(data.kpis.gross_pnl_inr)}) − Modeled Costs ({formatINR(data.kpis.total_costs_inr)}) = Net P&L ({formatINR(data.kpis.net_pnl_inr)}).
              </span>
            </div>
            <span className="font-medium text-[#0D8244]">10⁻⁴ Rupee Tolerance Verified</span>
          </div>

          {/* 3. Cumulative Realized Equity Curve */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-[#17191D]">
                Cumulative Realized Net P&L Equity Curve (₹)
              </h3>
              <p className="text-[11px] text-[#707784]">
                Chronological equity trajectory of out-of-sample walk-forward trade executions.
              </p>
            </div>
            <EquityCurveChart data={data.equity_curve} />
          </div>

          {/* 4. Strategy Performance Summary Table */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <h3 className="text-sm font-semibold text-[#17191D] mb-1">
              Strategy Performance Comparison
            </h3>
            <p className="text-[11px] text-[#707784] mb-4">
              Aggregated results for each research strategy under the {costScenario.toUpperCase()} cost model.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                    <th className="py-2 font-medium">Strategy Name</th>
                    <th className="py-2 text-right font-medium">Attempts</th>
                    <th className="py-2 text-right font-medium">Completed</th>
                    <th className="py-2 text-right font-medium">Win Rate</th>
                    <th className="py-2 text-right font-medium">Gross P&L</th>
                    <th className="py-2 text-right font-medium">Modeled Costs</th>
                    <th className="py-2 text-right font-medium">Net P&L</th>
                    <th className="py-2 text-right font-medium">Profit Factor</th>
                    <th className="py-2 text-right font-medium">Max Drawdown</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {data.strategies.map((st) => (
                    <tr key={st.strategy_name} className="hover:bg-[#FAFBFC]">
                      <td className="py-2 font-medium text-[#17191D]">{st.strategy_name}</td>
                      <td className="py-2 text-right text-[#707784]">{st.total_trade_attempts}</td>
                      <td className="py-2 text-right text-[#17191D]">{st.completed_trades}</td>
                      <td className="py-2 text-right text-[#17191D]">{formatPct(st.win_rate_pct)}</td>
                      <td className="py-2 text-right text-[#17191D]">{formatINR(st.gross_pnl_inr)}</td>
                      <td className="py-2 text-right text-[#D32F2F]">{formatINR(st.total_costs_inr)}</td>
                      <td className="py-2 text-right font-semibold text-[#0D8244]">
                        {formatINR(st.net_pnl_inr, { showSign: true })}
                      </td>
                      <td className="py-2 text-right text-[#17191D]">
                        {st.profit_factor ? st.profit_factor.toFixed(2) : "—"}
                      </td>
                      <td className="py-2 text-right text-[#D32F2F]">
                        {formatINR(st.realized_max_drawdown_inr)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 5. Walk-Forward Fold Results Table */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <h3 className="text-sm font-semibold text-[#17191D] mb-1">
              Walk-Forward Out-of-Sample Folds (1 to 10)
            </h3>
            <p className="text-[11px] text-[#707784] mb-4">
              Individual fold performance preventing look-ahead bias and curve fitting.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                    <th className="py-2 font-medium">Fold ID</th>
                    <th className="py-2 font-medium">Strategy</th>
                    <th className="py-2 font-medium">Testing Window</th>
                    <th className="py-2 text-right font-medium">Completed Trades</th>
                    <th className="py-2 text-right font-medium">Win Rate</th>
                    <th className="py-2 text-right font-medium">Net P&L (₹)</th>
                    <th className="py-2 text-right font-medium">Max Drawdown</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {data.walk_forward_folds.map((f, i) => (
                    <tr key={`${f.fold_id}_${i}`} className="hover:bg-[#FAFBFC]">
                      <td className="py-2 font-medium text-[#17191D]">{f.fold_id}</td>
                      <td className="py-2 text-[#707784]">{f.strategy_name}</td>
                      <td className="py-2 text-[#707784]">
                        {formatDate(f.test_start_date)} → {formatDate(f.test_end_date)}
                      </td>
                      <td className="py-2 text-right text-[#17191D]">{f.completed_trades}</td>
                      <td className="py-2 text-right text-[#17191D]">{formatPct(f.win_rate_pct)}</td>
                      <td
                        className={`py-2 text-right font-semibold ${
                          f.net_pnl_inr >= 0 ? "text-[#0D8244]" : "text-[#D32F2F]"
                        }`}
                      >
                        {formatINR(f.net_pnl_inr, { showSign: true })}
                      </td>
                      <td className="py-2 text-right text-[#707784]">
                        {formatINR(f.realized_max_drawdown_inr)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 6. Filterable Simulated Trade Ledger (Sample) */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#17191D]">
                  Simulated Trade Execution Ledger (Recent 25 Trades)
                </h3>
                <p className="text-[11px] text-[#707784]">
                  Authoritative trade executions reflecting actual entry/exit settlement logs.
                </p>
              </div>
              <span className="text-xs text-[#707784]">
                Showing {data.trade_ledger.length} trades
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                    <th className="py-2 font-medium">Trade ID</th>
                    <th className="py-2 font-medium">Signal Date</th>
                    <th className="py-2 font-medium">Pair Legs</th>
                    <th className="py-2 font-medium">Direction</th>
                    <th className="py-2 text-right font-medium">Gross P&L</th>
                    <th className="py-2 text-right font-medium">Modeled Costs</th>
                    <th className="py-2 text-right font-medium">Net P&L</th>
                    <th className="py-2 text-center font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {data.trade_ledger.map((tr) => (
                    <tr key={tr.trade_id} className="hover:bg-[#FAFBFC]">
                      <td className="py-2 font-mono text-[11px] text-[#707784]">{tr.trade_id}</td>
                      <td className="py-2 text-[#707784]">{formatDate(tr.signal_date)}</td>
                      <td className="py-2 font-medium text-[#17191D]">
                        {tr.symbol_leg_a} – {tr.symbol_leg_b}
                      </td>
                      <td className="py-2 text-[#707784]">{tr.signal_direction}</td>
                      <td className="py-2 text-right text-[#17191D]">
                        {tr.gross_pnl_inr !== null ? formatINR(tr.gross_pnl_inr) : "—"}
                      </td>
                      <td className="py-2 text-right text-[#D32F2F]">
                        {tr.total_modeled_cost_inr !== null ? formatINR(tr.total_modeled_cost_inr) : "—"}
                      </td>
                      <td
                        className={`py-2 text-right font-semibold ${
                          (tr.net_pnl_inr ?? 0) >= 0 ? "text-[#0D8244]" : "text-[#D32F2F]"
                        }`}
                      >
                        {tr.net_pnl_inr !== null ? formatINR(tr.net_pnl_inr, { showSign: true }) : "—"}
                      </td>
                      <td className="py-2 text-center">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                            tr.trade_completion_status === "COMPLETED"
                              ? "bg-[#ECFDF5] text-[#0D8244]"
                              : "bg-[#FEF2F2] text-[#D32F2F]"
                          }`}
                        >
                          {tr.trade_completion_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
