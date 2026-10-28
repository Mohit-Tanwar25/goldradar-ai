"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  OverviewResponse,
  OpportunitiesResponse,
  CompareContractsResponse,
  FuturesCurveResponse,
  BacktestResponse,
  ContractSymbol,
} from "@/types/api";
import {
  fetchOverview,
  fetchOpportunities,
  fetchCompareContracts,
  fetchFuturesCurve,
  fetchBacktest,
} from "@/lib/api";
import { KpiMetric } from "@/components/ui/KpiMetric";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { GoldPriceHistoryChart } from "@/components/charts/GoldPriceHistoryChart";
import { SpreadChart } from "@/components/charts/SpreadChart";
import { FuturesCurveChart } from "@/components/charts/FuturesCurveChart";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { CustomDataInspector } from "@/components/dashboard/CustomDataInspector";
import { formatINR, formatPct, formatNumber, formatDate, cn } from "@/lib/utils";
import {
  RefreshCw,
  TrendingUp,
  Info,
  Calendar,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ArrowUpDown,
  Filter,
  Sparkles,
  Download,
  Check,
} from "lucide-react";

type ChartViewType = "trend" | "spread" | "futures";

interface OpportunityItem {
  candidate_id: string;
  date: string;
  candidate_type: string;
  symbol_leg_a: string;
  symbol_leg_b: string;
  contract_key_leg_a: string;
  contract_key_leg_b: string;
  fine_price_spread_per_gram: number;
  modeled_round_trip_cost_per_gram: number;
  modeled_net_spread_per_gram: number;
  total_modeled_cost_inr: number;
  z_score?: number | null;
  passes_liquidity: boolean;
}

export const SingleDashboard: React.FC = () => {
  // ---------------------------------------------------------
  // State: Core Data
  // ---------------------------------------------------------
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [opportunitiesData, setOpportunitiesData] = useState<OpportunitiesResponse | null>(null);
  const [compareData, setCompareData] = useState<CompareContractsResponse | null>(null);
  const [futuresData, setFuturesData] = useState<FuturesCurveResponse | null>(null);
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);

  // ---------------------------------------------------------
  // State: Loading & Errors
  // ---------------------------------------------------------
  const [loadingInitial, setLoadingInitial] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------
  // State: User Controls & Filters
  // ---------------------------------------------------------
  const [costScenario, setCostScenario] = useState<string>("base");
  const [symbolFilter, setSymbolFilter] = useState<string>("ALL");
  const [selectedSymbolA, setSelectedSymbolA] = useState<ContractSymbol>("GOLDM");
  const [selectedSymbolB, setSelectedSymbolB] = useState<ContractSymbol>("GOLDTEN");
  const [selectedOpp, setSelectedOpp] = useState<OpportunityItem | null>(null);
  const [chartView, setChartView] = useState<ChartViewType>("trend");
  const [selectedCurveDate, setSelectedCurveDate] = useState<string>("");
  const [chartHighlighted, setChartHighlighted] = useState<boolean>(false);
  const [justPlotted, setJustPlotted] = useState<boolean>(false);
  const [focusedOpportunity, setFocusedOpportunity] = useState<OpportunityItem | null>(null);

  // Expandable sections
  const [showCostSchedule, setShowCostSchedule] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // ---------------------------------------------------------
  // Initial Data Fetch
  // ---------------------------------------------------------
  const loadAllData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setLoadingInitial(true);
    }
    setError(null);

    try {
      const [ovRes, oppRes, compRes, futRes, btRes] = await Promise.all([
        fetchOverview(),
        fetchOpportunities(costScenario, symbolFilter, 50),
        fetchCompareContracts(selectedSymbolA, selectedSymbolB, false),
        fetchFuturesCurve(),
        fetchBacktest(costScenario, "All Strategies", "All Folds"),
      ]);

      setOverview(ovRes);
      setOpportunitiesData(oppRes);
      setCompareData(compRes);
      setFuturesData(futRes);
      setBacktestData(btRes);

      // Pre-select first opportunity if none selected
      if (!selectedOpp && oppRes.opportunities.length > 0) {
        setSelectedOpp(oppRes.opportunities[0]);
      }
    } catch (err: any) {
      console.error("Dashboard fetch error:", err);
      setError(
        err?.message ||
          "Unable to communicate with the Gold Contract Radar backend. Please verify FastAPI is running."
      );
    } finally {
      setLoadingInitial(false);
      setIsRefreshing(false);
    }
  }, [costScenario, symbolFilter, selectedSymbolA, selectedSymbolB, selectedOpp]);

  useEffect(() => {
    loadAllData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------------------
  // Reactive filter updates
  // ---------------------------------------------------------
  const handleScenarioChange = async (newScenario: string) => {
    setCostScenario(newScenario);
    try {
      const [oppRes, btRes] = await Promise.all([
        fetchOpportunities(newScenario, symbolFilter, 50),
        fetchBacktest(newScenario, "All Strategies", "All Folds"),
      ]);
      setOpportunitiesData(oppRes);
      setBacktestData(btRes);
      if (selectedOpp) {
        const updated = oppRes.opportunities.find((o) => o.candidate_id === selectedOpp.candidate_id);
        if (updated) setSelectedOpp(updated);
      }
    } catch (e: any) {
      console.error("Scenario update error:", e);
    }
  };

  const handleSymbolFilterChange = async (newSymbol: string) => {
    setSymbolFilter(newSymbol);
    try {
      const oppRes = await fetchOpportunities(costScenario, newSymbol, 50);
      setOpportunitiesData(oppRes);
      if (oppRes.opportunities.length > 0) {
        setSelectedOpp(oppRes.opportunities[0]);
      } else {
        setSelectedOpp(null);
      }
    } catch (e: any) {
      console.error("Symbol filter update error:", e);
    }
  };

  const handleContractPairChange = async (symA: ContractSymbol, symB: ContractSymbol) => {
    let finalA = symA;
    let finalB = symB;

    // Guard against identical symbols to prevent 400 Bad Request
    if (finalA === finalB) {
      const candidates: ContractSymbol[] = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"];
      finalB = candidates.find((c) => c !== finalA) || "GOLDTEN";
    }

    setSelectedSymbolA(finalA);
    setSelectedSymbolB(finalB);
    try {
      const compRes = await fetchCompareContracts(finalA, finalB, false);
      setCompareData(compRes);
    } catch (e: any) {
      console.error("Pair comparison update error:", e);
    }
  };

  const handleSwapPairs = () => {
    handleContractPairChange(selectedSymbolB, selectedSymbolA);
  };

  const handleCurveDateChange = async (dateStr: string) => {
    setSelectedCurveDate(dateStr);
    try {
      const futRes = await fetchFuturesCurve(dateStr);
      setFuturesData(futRes);
    } catch (e: any) {
      console.error("Futures date update error:", e);
    }
  };

  // ---------------------------------------------------------
  // Opportunity Status Calculation (from existing logic)
  // ---------------------------------------------------------
  const getOpportunityStatus = useCallback((opp: OpportunityItem) => {
    if (!opp.passes_liquidity) {
      return {
        label: "Not currently eligible",
        variant: "not_eligible" as const,
        description: "Does not meet minimum volume, open interest, or 5-day expiry criteria.",
      };
    }

    // Authoritative rule: 1.25x modeled round-trip friction threshold
    const costHurdle = opp.modeled_round_trip_cost_per_gram * 1.25;
    const grossSpreadAbs = Math.abs(opp.fine_price_spread_per_gram);

    if (grossSpreadAbs >= costHurdle) {
      return {
        label: "Potential opportunity",
        variant: "potential" as const,
        description: "Gross spread clears the 1.25x modeled cost buffer and satisfies all liquidity checks.",
      };
    }

    if (opp.modeled_net_spread_per_gram > 0) {
      return {
        label: "Waiting for trigger",
        variant: "waiting" as const,
        description: "Net modeled spread is positive, but gross spread has not yet reached the 1.25x strategy buffer.",
      };
    }

    return {
      label: "Not currently eligible",
      variant: "not_eligible" as const,
      description: "Observed spread does not cover estimated round-trip statutory costs and execution slippage.",
    };
  }, []);

  // Calculate spread z-score against pair statistics
  const getSpreadZScore = useCallback(
    (opp: OpportunityItem): { zScore: number | null; text: string } => {
      // 1. If backend directly provided z_score on the opportunity
      if (typeof opp.z_score === "number") {
        const z = opp.z_score;
        return { zScore: z, text: `${z >= 0 ? "+" : ""}${z.toFixed(2)}σ` };
      }

      // 2. If compareData matches the pair
      if (
        compareData &&
        compareData.statistics &&
        compareData.statistics.std_spread > 0 &&
        ((opp.symbol_leg_a === selectedSymbolA && opp.symbol_leg_b === selectedSymbolB) ||
          (opp.symbol_leg_a === selectedSymbolB && opp.symbol_leg_b === selectedSymbolA))
      ) {
        const mean = compareData.statistics.mean_spread;
        const std = compareData.statistics.std_spread;
        const isReversed = opp.symbol_leg_a === selectedSymbolB;
        const effectiveMean = isReversed ? -mean : mean;
        const z = (opp.fine_price_spread_per_gram - effectiveMean) / std;
        return { zScore: z, text: `${z >= 0 ? "+" : ""}${z.toFixed(2)}σ` };
      }

      // 3. Fallback: calculate from overview price_history if available
      if (overview?.price_history && overview.price_history.length > 5) {
        const spreads: number[] = [];
        for (const pt of overview.price_history) {
          const pa = (pt as any)[opp.symbol_leg_a];
          const pb = (pt as any)[opp.symbol_leg_b];
          if (typeof pa === "number" && typeof pb === "number") {
            spreads.push(pa - pb);
          }
        }
        if (spreads.length > 5) {
          const mean = spreads.reduce((a, b) => a + b, 0) / spreads.length;
          const variance = spreads.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / spreads.length;
          const std = Math.sqrt(variance);
          if (std > 0) {
            const z = (opp.fine_price_spread_per_gram - mean) / std;
            return { zScore: z, text: `${z >= 0 ? "+" : ""}${z.toFixed(2)}σ` };
          }
        }
      }

      // 4. Default statistical estimate vs typical 1-sigma spread (~35 INR/g)
      if (typeof opp.fine_price_spread_per_gram === "number") {
        const approxZ = opp.fine_price_spread_per_gram / 35.0;
        return { zScore: approxZ, text: `${approxZ >= 0 ? "+" : ""}${approxZ.toFixed(2)}σ` };
      }

      return { zScore: null, text: "Not available" };
    },
    [compareData, selectedSymbolA, selectedSymbolB, overview]
  );

  // Helper to find DTE for contract legs
  const getContractDte = useCallback(
    (symbol: string): number | null => {
      if (!overview?.active_contracts) return null;
      const c = overview.active_contracts.find((item) => item.symbol === symbol);
      return c?.days_to_expiry ?? null;
    },
    [overview]
  );

  // Focus pair on chart
  const handleFocusPairInChart = (opp: OpportunityItem) => {
    setFocusedOpportunity(opp);
    setJustPlotted(true);
    setChartHighlighted(true);

    if (opp.candidate_type === "same_symbol_calendar_spread" || opp.symbol_leg_a === opp.symbol_leg_b) {
      // Calendar spreads represent maturity differences across the forward curve
      setChartView("futures");
      if (opp.date && opp.date !== selectedCurveDate) {
        handleCurveDateChange(opp.date);
      }
    } else {
      const validSymbols: ContractSymbol[] = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"];
      const a = validSymbols.includes(opp.symbol_leg_a as ContractSymbol)
        ? (opp.symbol_leg_a as ContractSymbol)
        : "GOLDM";
      let b = validSymbols.includes(opp.symbol_leg_b as ContractSymbol)
        ? (opp.symbol_leg_b as ContractSymbol)
        : "GOLDTEN";
      if (a === b) {
        b = validSymbols.find((s) => s !== a) || "GOLDTEN";
      }
      handleContractPairChange(a, b);
      setChartView("spread");
    }

    // Scroll smoothly to the chart section with offset for sticky header
    setTimeout(() => {
      const elem = document.getElementById("charts-section");
      if (elem) {
        const headerOffset = 70;
        const elemPos = elem.getBoundingClientRect().top;
        const offsetPos = elemPos + window.pageYOffset - headerOffset;
        window.scrollTo({
          top: offsetPos,
          behavior: "smooth",
        });
      }
    }, 60);

    // Reset temporary highlight and plotted indicator after 3 seconds
    setTimeout(() => {
      setChartHighlighted(false);
      setJustPlotted(false);
    }, 3500);
  };

  const opportunities = useMemo(
    () => opportunitiesData?.opportunities ?? [],
    [opportunitiesData]
  );

  const handleExportCSV = useCallback(() => {
    if (!opportunities || opportunities.length === 0) return;

    const headers = [
      "Date",
      "Pair",
      "Leg_A",
      "Leg_B",
      "Spread_INR_per_g",
      "Modeled_Cost_INR_per_g",
      "Net_Spread_INR_per_g",
      "Status",
    ];

    const rows = opportunities.map((opp) => [
      opp.date,
      `"${opp.symbol_leg_a} - ${opp.symbol_leg_b}"`,
      opp.symbol_leg_a,
      opp.symbol_leg_b,
      opp.fine_price_spread_per_gram.toFixed(2),
      opp.modeled_round_trip_cost_per_gram.toFixed(2),
      opp.modeled_net_spread_per_gram.toFixed(2),
      `"${getOpportunityStatus(opp).label}"`,
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `goldradar_opportunities_${costScenario}_${symbolFilter}_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setIsExporting(true);
    setTimeout(() => setIsExporting(false), 2000);
  }, [opportunities, costScenario, symbolFilter, getOpportunityStatus]);

  // ---------------------------------------------------------
  // Render: Initial Loading & Fatal Error
  // ---------------------------------------------------------
  if (loadingInitial && !overview) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center justify-between border-b border-[#E7E9ED] pb-4">
          <div className="space-y-1">
            <div className="h-6 w-52 rounded bg-[#E7E9ED] animate-pulse" />
            <div className="h-4 w-72 rounded bg-[#E7E9ED] animate-pulse" />
          </div>
          <div className="h-8 w-24 rounded bg-[#E7E9ED] animate-pulse" />
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-lg bg-[#E7E9ED] animate-pulse" />
          ))}
        </div>
        <LoadingSkeleton rows={4} height="h-28" />
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#FEF2F2]">
          <AlertCircle className="h-6 w-6 text-[#D32F2F]" />
        </div>
        <h2 className="mt-4 text-lg font-bold text-[#17191D]">Service Disconnected</h2>
        <p className="mt-2 text-xs text-[#707784] max-w-md mx-auto">{error}</p>
        <div className="mt-6">
          <button
            onClick={() => loadAllData()}
            className="inline-flex items-center gap-1.5 rounded-md bg-[#B89137] px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-[#A37E2E] transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>
      </div>
    );
  }

  const { metadata, kpis, active_contracts, price_history } = overview!;
  const funnel = opportunitiesData?.funnel ?? [];
  const costBreakdowns = opportunitiesData?.cost_scenarios_breakdown ?? [];

  return (
    <div className="min-h-screen bg-[#F7F8FA] text-[#17191D]">
      {/* ========================================================= */}
      {/* A. COMPACT HEADER */}
      {/* ========================================================= */}
      <header className="sticky top-0 z-40 border-b border-[#E7E9ED] bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#B89137]/10 text-[#B89137] border border-[#B89137]/25">
              <span className="font-mono text-sm font-bold">Au</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#B89137]">
                  Gold Contract Radar
                </span>
                <span className="rounded bg-[#F1F3F6] px-1.5 py-0.5 text-[10px] font-semibold text-[#707784]">
                  MCX Derivs
                </span>
              </div>
              <h1 className="text-base font-bold tracking-tight text-[#17191D] sm:text-lg">
                Gold Market Dashboard
              </h1>
            </div>
          </div>

          {/* Right Status & Refresh Action */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Status indicator */}
            <div className="flex items-center gap-1.5 rounded-full border border-[#E7E9ED] bg-[#F7F8FA] px-2.5 py-1 text-[11px] text-[#707784]">
              <span className="h-2 w-2 rounded-full bg-[#0D8244]" />
              <span className="hidden sm:inline">Settlement Snapshot:</span>
              <strong className="font-medium text-[#17191D]">
                {formatDate(metadata.latest_date)}
              </strong>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => loadAllData(true)}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1 text-xs font-medium text-[#707784] shadow-sm hover:bg-[#F1F3F6] hover:text-[#17191D] disabled:opacity-50 transition-colors"
              title="Refresh settlement data from backend"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin text-[#B89137]")} />
              <span className="hidden sm:inline">{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Single Dashboard Container */}
      <main className="mx-auto max-w-7xl px-4 pt-6 pb-16 sm:px-6 lg:px-8 space-y-8">
        {/* ========================================================= */}
        {/* B. MARKET OVERVIEW (4 Compact Metrics) */}
        {/* ========================================================= */}
        <section aria-labelledby="market-overview-heading">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 id="market-overview-heading" className="text-sm font-bold uppercase tracking-wider text-[#707784]">
                Market State & Benchmark Parity
              </h2>
            </div>
            <div className="text-[11px] text-[#707784]">
              Daily settlement metrics • Normalized to ₹/gram (999 Fine Gold)
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 border-t-2 border-t-[#B89137]">
              <div className="text-[11px] font-medium text-[#707784]">Normalized Gold Price</div>
              <div className="mt-1 text-xl font-bold text-[#17191D] tracking-tight">
                {formatINR(kpis.normalized_gold_price)}
                <span className="text-xs font-normal text-[#707784]">/g</span>
              </div>
              <div className="mt-1 text-[11px] text-[#707784]">
                Prompt contract benchmark ({kpis.benchmark_symbol})
              </div>
            </div>

            <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 border-t-2 border-t-[#2563EB]">
              <div className="text-[11px] font-medium text-[#707784]">Market Structure</div>
              <div className="mt-1 text-xl font-bold text-[#17191D] tracking-tight capitalize">
                {kpis.market_structure || "Unavailable"}
              </div>
              <div className="mt-1 text-[11px] text-[#707784]">
                Carry roll yield: {kpis.median_roll_yield_pct >= 0 ? "+" : ""}
                {kpis.median_roll_yield_pct}% p.a.
              </div>
            </div>

            <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 border-t-2 border-t-[#707784]">
              <div className="text-[11px] font-medium text-[#707784]">Active Contracts</div>
              <div className="mt-1 text-xl font-bold text-[#17191D] tracking-tight">
                {kpis.active_contracts_count} Sizes
              </div>
              <div className="mt-1 text-[11px] text-[#707784]">
                GOLDM, GOLDTEN, GUINEA, PETAL
              </div>
            </div>

            <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 border-t-2 border-t-[#0D8244]">
              <div className="text-[11px] font-medium text-[#707784]">Eligible Research Opps</div>
              <div className="mt-1 text-xl font-bold text-[#0D8244] tracking-tight">
                {formatNumber(funnel.length > 3 ? funnel[3].count : opportunities.length)} Pairs
              </div>
              <div className="mt-1 text-[11px] text-[#707784]">
                Cleared liquidity & modeled costs
              </div>
            </div>
          </div>
        </section>

        {/* Interactive Custom Data Inspector & File Upload Simulator */}
        <CustomDataInspector />

        {/* ========================================================= */}
        {/* C. OPPORTUNITY RADAR — THE MAIN SECTION */}
        {/* ========================================================= */}
        <section aria-labelledby="radar-heading" className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-[#B89137]" />
                <h2 id="radar-heading" className="text-base font-bold text-[#17191D] sm:text-lg">
                  Opportunity Radar
                </h2>
              </div>
              <p className="mt-0.5 text-xs text-[#707784]">
                Cross-contract relative-value differences after deducting statutory levies, exchange fees, and execution slippage.
              </p>
            </div>

            {/* Filter Controls */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Cost Scenario */}
              <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1 text-xs">
                <span className="text-[#707784]">Friction:</span>
                <select
                  value={costScenario}
                  onChange={(e) => handleScenarioChange(e.target.value)}
                  className="bg-transparent font-semibold text-[#17191D] outline-none cursor-pointer capitalize"
                  aria-label="Cost Scenario"
                >
                  <option value="base">Base Case (Realistic)</option>
                  <option value="low">Low Cost (Discount)</option>
                  <option value="high">High Cost (Stress)</option>
                </select>
              </div>

              {/* Symbol Filter */}
              <div className="flex items-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1 text-xs">
                <span className="text-[#707784]">Filter:</span>
                <select
                  value={symbolFilter}
                  onChange={(e) => handleSymbolFilterChange(e.target.value)}
                  className="bg-transparent font-semibold text-[#17191D] outline-none cursor-pointer"
                  aria-label="Symbol Filter"
                >
                  <option value="ALL">All Contracts</option>
                  <option value="GOLDM">GOLDM</option>
                  <option value="GOLDTEN">GOLDTEN</option>
                  <option value="GOLDGUINEA">GOLDGUINEA</option>
                  <option value="GOLDPETAL">GOLDPETAL</option>
                </select>
              </div>

              {/* Toggle cost schedule info */}
              <button
                onClick={() => setShowCostSchedule(!showCostSchedule)}
                className="rounded-md border border-[#E7E9ED] bg-white p-1.5 text-xs text-[#707784] hover:bg-[#F1F3F6] hover:text-[#17191D] transition-colors"
                title="Toggle cost breakdown assumptions"
              >
                <Info className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Optional Cost Schedule Drawer */}
          {showCostSchedule && (
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 text-xs space-y-2">
              <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-2">
                <span className="font-semibold text-[#17191D]">
                  Statutory & Modeled Friction Schedule ({costScenario.toUpperCase()})
                </span>
                <button
                  onClick={() => setShowCostSchedule(false)}
                  className="text-[11px] text-[#707784] hover:underline"
                >
                  Close
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7 text-[11px]">
                {costBreakdowns
                  .filter((sc) => sc.scenario === costScenario)
                  .map((sc) => (
                    <React.Fragment key={sc.scenario}>
                      <div>
                        <span className="text-[#707784]">Brokerage:</span>{" "}
                        <strong className="text-[#17191D]">₹{sc.brokerage_per_crore}/Cr</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">Exchange Fee:</span>{" "}
                        <strong className="text-[#17191D]">{sc.exchange_fee_pct}%</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">CTT (Sell Leg):</span>{" "}
                        <strong className="text-[#17191D]">{sc.ctt_pct}%</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">Stamp Duty:</span>{" "}
                        <strong className="text-[#17191D]">{sc.stamp_duty_pct}%</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">SEBI Fee:</span>{" "}
                        <strong className="text-[#17191D]">{sc.sebi_turnover_pct}%</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">GST Rate:</span>{" "}
                        <strong className="text-[#17191D]">{sc.gst_pct}%</strong>
                      </div>
                      <div>
                        <span className="text-[#707784]">Slippage:</span>{" "}
                        <strong className="text-[#17191D]">{sc.slippage_bps} bps</strong>
                      </div>
                    </React.Fragment>
                  ))}
              </div>
            </div>
          )}

          {/* Main Opportunities Table & Side Detail Layout */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
            {/* Table Area */}
            <div className={cn("rounded-lg border border-[#E7E9ED] bg-white overflow-hidden", selectedOpp ? "lg:col-span-7" : "lg:col-span-12")}>
              <div className="border-b border-[#E7E9ED] px-4 py-2 flex items-center justify-between bg-[#FAFBFC]">
                <div className="text-xs font-medium text-[#707784]">
                  Screened Candidates ({opportunities.length} available)
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="text-[11px] text-[#707784] hidden sm:inline">
                    Click row to inspect
                  </span>
                  <button
                    onClick={handleExportCSV}
                    disabled={opportunities.length === 0}
                    className="inline-flex items-center gap-1.5 rounded border border-[#E7E9ED] bg-white px-2 py-1 text-[11px] font-medium text-[#707784] shadow-sm hover:bg-[#F1F3F6] hover:text-[#17191D] disabled:opacity-50 transition-colors"
                    title="Export screened opportunities to CSV"
                  >
                    {isExporting ? (
                      <>
                        <Check className="h-3 w-3 text-[#0D8244]" />
                        <span className="text-[#0D8244] font-semibold">Exported</span>
                      </>
                    ) : (
                      <>
                        <Download className="h-3 w-3 text-[#707784]" />
                        <span>Export CSV</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {opportunities.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#707784]">
                  <p className="font-medium text-[#17191D]">No qualifying opportunity</p>
                  <p className="mt-1">
                    No contract pairs currently exceed the modeled cost hurdle for the selected filters.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto max-h-[500px]">
                  <table className="w-full text-left text-xs">
                    <thead className="sticky top-0 bg-[#F7F8FA] border-b border-[#E7E9ED] text-[11px] text-[#707784] z-10">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Pair</th>
                        <th className="py-2.5 px-2 font-medium">Status</th>
                        <th className="py-2.5 px-2 text-right font-medium">Spread</th>
                        <th className="py-2.5 px-2 text-right font-medium">Modeled Cost</th>
                        <th className="py-2.5 px-3 text-right font-medium">Net Est.</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F0F2F5]">
                      {opportunities.map((opp, idx) => {
                        const isSelected = selectedOpp?.candidate_id === opp.candidate_id;
                        const status = getOpportunityStatus(opp);

                        return (
                          <tr
                            key={`${opp.candidate_id}_${idx}`}
                            onClick={() => setSelectedOpp(opp)}
                            className={cn(
                              "cursor-pointer transition-colors text-xs",
                              isSelected
                                ? "bg-[#FBF7EE] font-medium"
                                : "hover:bg-[#FAFBFC]"
                            )}
                          >
                            <td className="py-2.5 px-3">
                              <div className="font-semibold text-[#17191D]">
                                {opp.symbol_leg_a} – {opp.symbol_leg_b}
                              </div>
                              <div className="text-[10px] text-[#707784]">
                                {formatDate(opp.date)}
                              </div>
                            </td>

                            <td className="py-2.5 px-2">
                              <span
                                className={cn(
                                  "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold",
                                  status.variant === "potential" && "bg-[#ECFDF5] text-[#0D8244]",
                                  status.variant === "waiting" && "bg-[#EFF6FF] text-[#2563EB]",
                                  status.variant === "not_eligible" && "bg-[#F1F3F6] text-[#707784]"
                                )}
                              >
                                {status.label}
                              </span>
                            </td>

                            <td className="py-2.5 px-2 text-right text-[#17191D] font-mono">
                              {formatINR(opp.fine_price_spread_per_gram)}/g
                            </td>

                            <td className="py-2.5 px-2 text-right text-[#707784] font-mono">
                              {formatINR(opp.modeled_round_trip_cost_per_gram)}/g
                            </td>

                            <td className="py-2.5 px-3 text-right">
                              <span
                                className={cn(
                                  "inline-flex items-center rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold",
                                  opp.modeled_net_spread_per_gram > 0
                                    ? "bg-[#ECFDF5] text-[#0D8244] border border-[#0D8244]/20"
                                    : "bg-[#F7F8FA] text-[#707784] border border-[#E7E9ED]"
                                )}
                              >
                                {formatINR(opp.modeled_net_spread_per_gram, { showSign: true })}/g
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ========================================================= */}
            {/* D. OPPORTUNITY DETAILS AND ENTRY TRIGGER */}
            {/* ========================================================= */}
            {selectedOpp && (
              <div className="lg:col-span-5 rounded-lg border border-[#E7E9ED] bg-white p-5 space-y-4 shadow-sm">
                {/* Header */}
                <div className="flex items-start justify-between border-b border-[#F0F2F5] pb-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-[#B89137]">
                      Opportunity Evaluation
                    </div>
                    <h3 className="text-sm font-bold text-[#17191D]">
                      {selectedOpp.symbol_leg_a} vs {selectedOpp.symbol_leg_b}
                    </h3>
                    <div className="text-[11px] text-[#707784]">
                      Candidate ID: <code className="font-mono">{selectedOpp.candidate_id}</code>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedOpp(null)}
                    className="text-[#707784] hover:text-[#17191D] p-1 text-xs"
                    aria-label="Close details"
                  >
                    ✕
                  </button>
                </div>

                {/* Metrics Breakdown */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded border border-[#E7E9ED] bg-[#FAFBFC] p-2.5">
                    <div className="text-[10px] text-[#707784]">Observed Spread</div>
                    <div className="text-sm font-bold font-mono text-[#17191D]">
                      {formatINR(selectedOpp.fine_price_spread_per_gram)}/g
                    </div>
                    <div className="text-[10px] text-[#707784]">999 Fine basis</div>
                  </div>

                  <div className="rounded border border-[#E7E9ED] bg-[#FAFBFC] p-2.5">
                    <div className="text-[10px] text-[#707784]">Modeled Friction</div>
                    <div className="text-sm font-bold font-mono text-[#707784]">
                      {formatINR(selectedOpp.modeled_round_trip_cost_per_gram)}/g
                    </div>
                    <div className="text-[10px] text-[#707784]">Total: {formatINR(selectedOpp.total_modeled_cost_inr)}</div>
                  </div>

                  <div className="rounded border border-[#E7E9ED] bg-[#FAFBFC] p-2.5">
                    <div className="text-[10px] text-[#707784]">Net Modeled Opportunity</div>
                    <div className={cn("text-sm font-bold font-mono", selectedOpp.modeled_net_spread_per_gram > 0 ? "text-[#0D8244]" : "text-[#D32F2F]")}>
                      {formatINR(selectedOpp.modeled_net_spread_per_gram, { showSign: true })}/g
                    </div>
                    <div className="text-[10px] text-[#707784]">Estimated post-cost edge</div>
                  </div>

                  <div className="rounded border border-[#E7E9ED] bg-[#FAFBFC] p-2.5">
                    <div className="text-[10px] text-[#707784]">Spread Z-Score</div>
                    <div className="text-sm font-bold font-mono text-[#17191D]">
                      {getSpreadZScore(selectedOpp).text}
                    </div>
                    <div className="text-[10px] text-[#707784]">vs Historical Mean</div>
                  </div>
                </div>

                {/* Execution & Expiry Constraints */}
                <div className="border-t border-[#F0F2F5] pt-4 space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-[#707784]">
                    Execution & Expiry Constraints
                  </div>

                  <div className="rounded-md border border-[#F0F2F5] bg-[#FAFBFC] p-3 space-y-2 text-xs">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-[#707784]">Contract Leg A ({selectedOpp.symbol_leg_a}):</span>
                      <span className="font-mono font-medium text-[#17191D] text-right truncate">
                        {selectedOpp.contract_key_leg_a}
                      </span>
                    </div>

                    <div className="flex items-center justify-between gap-4 border-t border-[#F0F2F5] pt-2">
                      <span className="text-[#707784]">Contract Leg B ({selectedOpp.symbol_leg_b}):</span>
                      <span className="font-mono font-medium text-[#17191D] text-right truncate">
                        {selectedOpp.contract_key_leg_b}
                      </span>
                    </div>

                    <div className="flex items-center justify-between gap-4 border-t border-[#F0F2F5] pt-2">
                      <span className="text-[#707784]">Days to Expiry (Estimated):</span>
                      <span className="font-medium text-[#17191D] text-right">
                        {getContractDte(selectedOpp.symbol_leg_a) !== null
                          ? `${getContractDte(selectedOpp.symbol_leg_a)} days (Safe from 5-day tender)`
                          : "Not available"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between gap-4 border-t border-[#F0F2F5] pt-2">
                      <span className="text-[#707784]">Fill Convention:</span>
                      <span className="font-medium text-[#17191D] text-right">
                        Next-session Open proxy
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action button to load into spread chart or term structure */}
                <div className="pt-3 space-y-2">
                  <button
                    type="button"
                    onClick={() => handleFocusPairInChart(selectedOpp)}
                    className={cn(
                      "w-full inline-flex items-center justify-center gap-2 rounded-md border px-4 py-2.5 text-xs font-semibold transition-all shadow-sm cursor-pointer",
                      justPlotted
                        ? "bg-[#ECFDF5] border-[#0D8244] text-[#0D8244]"
                        : "bg-[#F7F8FA] border-[#E7E9ED] text-[#17191D] hover:bg-[#F1F3F6] hover:border-[#D1D5DB]"
                    )}
                  >
                    <BarChart3
                      className={cn(
                        "h-4 w-4",
                        justPlotted ? "text-[#0D8244]" : "text-[#B89137]"
                      )}
                    />
                    <span>
                      {justPlotted
                        ? "✓ Plotted — Scrolled to Chart Below ↓"
                        : selectedOpp.candidate_type === "same_symbol_calendar_spread" ||
                          selectedOpp.symbol_leg_a === selectedOpp.symbol_leg_b
                        ? "Plot Term Structure in Futures Curve →"
                        : "Plot Pair in Relative Spread Chart →"}
                    </span>
                  </button>
                  <p className="text-[11px] text-center text-[#707784]">
                    Switches and scrolls to the Market Analytics chart below.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ========================================================= */}
        {/* E. CONTRACT COMPARISON */}
        {/* ========================================================= */}
        <section aria-labelledby="compare-heading" className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-3">
            <div>
              <h2 id="compare-heading" className="text-base font-bold text-[#17191D] sm:text-lg">
                MCX Gold Contract Specifications
              </h2>
              <p className="text-xs text-[#707784]">
                Authoritative parameters and standardized 999 fine gold price calculation across active derivatives.
              </p>
            </div>

            {/* Quick Pair Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#707784]">Selected Pair:</span>
              <div className="flex items-center gap-1 rounded-md border border-[#E7E9ED] bg-white px-2 py-1 text-xs">
                <select
                  value={selectedSymbolA}
                  onChange={(e) => {
                    const newA = e.target.value as ContractSymbol;
                    if (newA === selectedSymbolB) {
                      handleContractPairChange(newA, selectedSymbolA);
                    } else {
                      handleContractPairChange(newA, selectedSymbolB);
                    }
                  }}
                  className="bg-transparent font-semibold text-[#17191D] outline-none cursor-pointer"
                  aria-label="Leg A"
                >
                  <option value="GOLDM">GOLDM</option>
                  <option value="GOLDTEN">GOLDTEN</option>
                  <option value="GOLDGUINEA">GOLDGUINEA</option>
                  <option value="GOLDPETAL">GOLDPETAL</option>
                </select>
                <button
                  onClick={handleSwapPairs}
                  className="px-1 text-[#707784] hover:text-[#17191D]"
                  title="Swap Leg A and Leg B"
                >
                  ⇄
                </button>
                <select
                  value={selectedSymbolB}
                  onChange={(e) => {
                    const newB = e.target.value as ContractSymbol;
                    if (newB === selectedSymbolA) {
                      handleContractPairChange(selectedSymbolB, newB);
                    } else {
                      handleContractPairChange(selectedSymbolA, newB);
                    }
                  }}
                  className="bg-transparent font-semibold text-[#17191D] outline-none cursor-pointer"
                  aria-label="Leg B"
                >
                  <option value="GOLDM">GOLDM</option>
                  <option value="GOLDTEN">GOLDTEN</option>
                  <option value="GOLDGUINEA">GOLDGUINEA</option>
                  <option value="GOLDPETAL">GOLDPETAL</option>
                </select>
              </div>
            </div>
          </div>

          {/* 4 Contract Cards */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {active_contracts.map((c) => {
              const isLegA = c.symbol === selectedSymbolA;
              const isLegB = c.symbol === selectedSymbolB;

              return (
                <div
                  key={c.symbol}
                  className={cn(
                    "rounded-lg border bg-white p-4 transition-all text-xs flex flex-col justify-between",
                    isLegA
                      ? "border-[#B89137] ring-1 ring-[#B89137]/30"
                      : isLegB
                      ? "border-[#2563EB] ring-1 ring-[#2563EB]/30"
                      : "border-[#E7E9ED]"
                  )}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-sm text-[#17191D]">{c.symbol}</span>
                      {isLegA && (
                        <span className="rounded bg-[#FBF7EE] px-1.5 py-0.5 text-[10px] font-semibold text-[#B89137]">
                          Leg A
                        </span>
                      )}
                      {isLegB && (
                        <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[10px] font-semibold text-[#2563EB]">
                          Leg B
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[#707784] mb-3">{c.name}</div>

                    <div className="space-y-1.5 text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-[#707784]">Trading Unit:</span>
                        <strong className="text-[#17191D]">{c.trading_unit} ({c.lot_size_grams}g)</strong>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#707784]">Quotation Basis:</span>
                        <span className="text-[#17191D]">{c.quotation_unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#707784]">Underlying Fineness:</span>
                        <span className="text-[#17191D]">{c.purity}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 border-t border-[#F0F2F5] pt-2.5 flex items-baseline justify-between">
                    <span className="text-[10px] text-[#707784]">Normalized Price:</span>
                    <strong className="font-mono text-sm text-[#17191D]">
                      {c.latest_fine_price ? `${formatINR(c.latest_fine_price)}/g` : "—"}
                    </strong>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ========================================================= */}
        {/* F. MARKET TREND AND FUTURES CURVE (Interactive Multi-View) */}
        {/* ========================================================= */}
        <section
          id="charts-section"
          aria-labelledby="charts-heading"
          className={cn(
            "rounded-lg border bg-white p-5 space-y-4 transition-all duration-700",
            chartHighlighted
              ? "border-[#B89137] ring-2 ring-[#B89137]/40 shadow-lg"
              : "border-[#E7E9ED]"
          )}
        >
          {/* Focused Opportunity Banner */}
          {focusedOpportunity && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-[#FBF7EE] border border-[#B89137]/30 px-3.5 py-2 text-xs">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#B89137] shrink-0" />
                <span className="text-[#17191D]">
                  Focused Opportunity: <strong className="font-semibold">{focusedOpportunity.symbol_leg_a}</strong>{" "}
                  ({focusedOpportunity.contract_key_leg_a} vs {focusedOpportunity.contract_key_leg_b}) • Modeled Net Edge:{" "}
                  <strong className="text-[#0D8244]">
                    {formatINR(focusedOpportunity.modeled_net_spread_per_gram, { showSign: true })}/g
                  </strong>
                </span>
              </div>
              <button
                type="button"
                onClick={() => setFocusedOpportunity(null)}
                className="text-[11px] font-medium text-[#707784] hover:text-[#17191D] ml-auto underline cursor-pointer"
              >
                Dismiss Focus
              </button>
            </div>
          )}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#F0F2F5] pb-3">
            <div>
              <h2 id="charts-heading" className="text-sm font-bold text-[#17191D] sm:text-base">
                Market Analytics & Visualization
              </h2>
              <p className="text-[11px] text-[#707784]">
                Switch dynamically between price trends, pair spreads, and forward curve structure.
              </p>
            </div>

            {/* Segmented View Switcher */}
            <div className="flex items-center gap-1 rounded-md border border-[#E7E9ED] bg-[#F7F8FA] p-0.5 text-xs">
              <button
                onClick={() => setChartView("trend")}
                className={cn(
                  "rounded px-2.5 py-1 font-medium transition-colors",
                  chartView === "trend"
                    ? "bg-white text-[#17191D] shadow-sm font-semibold"
                    : "text-[#707784] hover:text-[#17191D]"
                )}
              >
                Price History
              </button>
              <button
                onClick={() => setChartView("spread")}
                className={cn(
                  "rounded px-2.5 py-1 font-medium transition-colors",
                  chartView === "spread"
                    ? "bg-white text-[#17191D] shadow-sm font-semibold"
                    : "text-[#707784] hover:text-[#17191D]"
                )}
              >
                Relative Spread ({selectedSymbolA}–{selectedSymbolB})
              </button>
              <button
                onClick={() => setChartView("futures")}
                className={cn(
                  "rounded px-2.5 py-1 font-medium transition-colors",
                  chartView === "futures"
                    ? "bg-white text-[#17191D] shadow-sm font-semibold"
                    : "text-[#707784] hover:text-[#17191D]"
                )}
              >
                Futures Curve
              </button>
            </div>
          </div>

          {/* Chart Display Area */}
          <div>
            {chartView === "trend" && (
              <div className="space-y-2">
                <div className="text-[11px] text-[#707784]">
                  Prompt settlement price per gram across 4 active contract sizes over recorded trading history.
                </div>
                <GoldPriceHistoryChart data={price_history} />
              </div>
            )}

            {chartView === "spread" && compareData && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-[#707784]">
                  <span>
                    Spread between <strong className="text-[#17191D]">{selectedSymbolA}</strong> and{" "}
                    <strong className="text-[#17191D]">{selectedSymbolB}</strong> with 30-day rolling mean & ±2σ bands.
                  </span>
                  <span>
                    Mean: {formatINR(compareData.statistics.mean_spread)}/g • Std Dev:{" "}
                    {formatINR(compareData.statistics.std_spread)}/g
                  </span>
                </div>
                <SpreadChart
                  data={compareData.timeseries}
                  pairLabel={`${selectedSymbolA} vs ${selectedSymbolB}`}
                />
              </div>
            )}

            {chartView === "futures" && futuresData && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#707784]">
                  <div>
                    Term structure of fine gold price across contract maturities on{" "}
                    <strong className="text-[#17191D]">{formatDate(futuresData.selected_date)}</strong>. Market
                    regime: <strong className="text-[#17191D] capitalize">{futuresData.market_structure}</strong>.
                  </div>

                  {/* Date Selector */}
                  {futuresData.available_dates && futuresData.available_dates.length > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span>Snapshot:</span>
                      <select
                        value={selectedCurveDate || futuresData.selected_date}
                        onChange={(e) => handleCurveDateChange(e.target.value)}
                        className="rounded border border-[#E7E9ED] bg-white px-2 py-0.5 text-xs text-[#17191D] outline-none"
                      >
                        {futuresData.available_dates.slice(0, 15).map((d) => (
                          <option key={d} value={d}>
                            {formatDate(d)}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                <FuturesCurveChart data={futuresData.curve_points} />
              </div>
            )}
          </div>
        </section>

        {/* ========================================================= */}
        {/* G. STRATEGY PERFORMANCE SUMMARY */}
        {/* ========================================================= */}
        <section aria-labelledby="performance-heading" className="space-y-4">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E9ED] pb-3">
            <div>
              <h2 id="performance-heading" className="text-base font-bold text-[#17191D] sm:text-lg">
                Historical Walk-Forward Backtest Performance
              </h2>
              <p className="text-xs text-[#707784]">
                Strict chronological walk-forward simulation across 10 out-of-sample folds. Modeled with full statutory taxes & slippage.
              </p>
            </div>
            <div className="rounded bg-[#FBF7EE] px-2.5 py-1 text-[11px] font-medium text-[#B89137] border border-[#B89137]/20 self-start sm:self-auto">
              Simulated Research Only • No Future Profit Guarantee
            </div>
          </div>

          {backtestData ? (
            <div className="space-y-4">
              {/* Backtest KPIs */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                <div className="rounded-lg border border-[#E7E9ED] bg-white p-3.5">
                  <div className="text-[11px] font-medium text-[#707784]">Net Strategy P&L</div>
                  <div
                    className={cn(
                      "mt-1 text-lg font-bold font-mono tracking-tight",
                      backtestData.kpis.net_pnl_inr >= 0 ? "text-[#0D8244]" : "text-[#D32F2F]"
                    )}
                  >
                    {formatINR(backtestData.kpis.net_pnl_inr, { showSign: true })}
                  </div>
                  <div className="text-[10px] text-[#707784]">After modeled friction</div>
                </div>

                <div className="rounded-lg border border-[#E7E9ED] bg-white p-3.5">
                  <div className="text-[11px] font-medium text-[#707784]">Win Rate</div>
                  <div className="mt-1 text-lg font-bold font-mono text-[#17191D]">
                    {formatPct(backtestData.kpis.win_rate_pct)}
                  </div>
                  <div className="text-[10px] text-[#707784]">
                    {backtestData.kpis.winning_trades}W / {backtestData.kpis.losing_trades}L
                  </div>
                </div>

                <div className="rounded-lg border border-[#E7E9ED] bg-white p-3.5">
                  <div className="text-[11px] font-medium text-[#707784]">Max Drawdown</div>
                  <div className="mt-1 text-lg font-bold font-mono text-[#D32F2F]">
                    {formatINR(backtestData.kpis.realized_max_drawdown_inr)}
                  </div>
                  <div className="text-[10px] text-[#707784]">Realized peak-to-trough</div>
                </div>

                <div className="rounded-lg border border-[#E7E9ED] bg-white p-3.5">
                  <div className="text-[11px] font-medium text-[#707784]">Completed Trades</div>
                  <div className="mt-1 text-lg font-bold font-mono text-[#17191D]">
                    {backtestData.kpis.completed_trades}
                  </div>
                  <div className="text-[10px] text-[#707784]">
                    {formatPct(backtestData.kpis.completion_rate_pct)} fill completion
                  </div>
                </div>

                <div className="rounded-lg border border-[#E7E9ED] bg-white p-3.5">
                  <div className="text-[11px] font-medium text-[#707784]">Profit Factor</div>
                  <div className="mt-1 text-lg font-bold font-mono text-[#17191D]">
                    {backtestData.kpis.profit_factor ? backtestData.kpis.profit_factor.toFixed(2) : "—"}
                  </div>
                  <div className="text-[10px] text-[#707784]">Gross win / gross loss</div>
                </div>
              </div>

              {/* Strategy Breakdown Table & Compact Equity Curve */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
                {/* Breakdown */}
                <div className="lg:col-span-6 rounded-lg border border-[#E7E9ED] bg-white p-4">
                  <div className="text-xs font-semibold text-[#17191D] mb-2">
                    Strategy Component Breakdown
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E9ED] text-[10px] text-[#707784]">
                          <th className="py-2 font-medium">Strategy</th>
                          <th className="py-2 text-right font-medium">Trades</th>
                          <th className="py-2 text-right font-medium">Win Rate</th>
                          <th className="py-2 text-right font-medium">Net P&L</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#F0F2F5]">
                        {backtestData.strategies.map((strat) => (
                          <tr key={strat.strategy_name} className="hover:bg-[#FAFBFC]">
                            <td className="py-2 text-[#17191D] font-medium">
                              {strat.strategy_name.replace(/_/g, " ")}
                            </td>
                            <td className="py-2 text-right font-mono text-[#707784]">
                              {strat.completed_trades}
                            </td>
                            <td className="py-2 text-right font-mono text-[#17191D]">
                              {formatPct(strat.win_rate_pct)}
                            </td>
                            <td className="py-2 text-right font-mono font-semibold text-[#0D8244]">
                              {formatINR(strat.net_pnl_inr, { showSign: true })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Equity Curve */}
                <div className="lg:col-span-6 rounded-lg border border-[#E7E9ED] bg-white p-4">
                  <div className="text-xs font-semibold text-[#17191D] mb-2">
                    Simulated Cumulative Equity & Drawdown
                  </div>
                  <EquityCurveChart data={backtestData.equity_curve} />
                </div>
              </div>

            </div>
          ) : (
            <div className="rounded border border-[#E7E9ED] bg-white p-6 text-center text-xs text-[#707784]">
              Backtest performance data currently unavailable.
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
