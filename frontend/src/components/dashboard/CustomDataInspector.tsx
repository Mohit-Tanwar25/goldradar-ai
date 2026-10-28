"use client";

import React, { useState, useId, useMemo, useCallback } from "react";
import { formatINR, cn } from "@/lib/utils";
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  Trash2,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  Info,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface ContractSpec {
  symbol: string;
  name: string;
  tradingUnitGrams: number;
  quotationDivisorGrams: number;
  purityFineness: number;
  fineDivisor: number; // quotationDivisor * (purityFineness / 1000)
}

const MCX_SPECS: Record<string, ContractSpec> = {
  GOLDM: {
    symbol: "GOLDM",
    name: "Gold Mini (100g)",
    tradingUnitGrams: 100,
    quotationDivisorGrams: 10.0,
    purityFineness: 995,
    fineDivisor: 9.95, // 10 * 0.995
  },
  GOLDTEN: {
    symbol: "GOLDTEN",
    name: "Gold Ten (10g)",
    tradingUnitGrams: 10,
    quotationDivisorGrams: 10.0,
    purityFineness: 999,
    fineDivisor: 9.99, // 10 * 0.999
  },
  GOLDGUINEA: {
    symbol: "GOLDGUINEA",
    name: "Gold Guinea (8g)",
    tradingUnitGrams: 8,
    quotationDivisorGrams: 8.0,
    purityFineness: 999,
    fineDivisor: 7.992, // 8 * 0.999
  },
  GOLDPETAL: {
    symbol: "GOLDPETAL",
    name: "Gold Petal (1g)",
    tradingUnitGrams: 1,
    quotationDivisorGrams: 1.0,
    purityFineness: 999,
    fineDivisor: 0.999, // 1 * 0.999
  },
  GOLD: {
    symbol: "GOLD",
    name: "Gold Standard (1kg)",
    tradingUnitGrams: 1000,
    quotationDivisorGrams: 10.0,
    purityFineness: 995,
    fineDivisor: 9.95,
  },
};

interface ParsedRecord {
  id: string;
  date: string;
  symbol: string;
  expiryDate?: string;
  quotedPrice: number;
  normalizedPrice: number;
  volumeLots?: number;
  openInterest?: number;
  notes?: string;
}

interface AnalyzedPair {
  id: string;
  date: string;
  contractA: string;
  contractB: string;
  priceA: number;
  priceB: number;
  finePriceA: number;
  finePriceB: number;
  grossSpread: number;
  modeledCost: number;
  netSpread: number;
  status: "eligible" | "hurdle_not_met" | "negative";
  statusText: string;
}

function calculateRoundTripFriction(pricePerGram: number, scenario: "base" | "low" | "high" = "base"): {
  totalFriction: number;
  ctt: number;
  stampDuty: number;
  exchangeFee: number;
  sebiFee: number;
  gst: number;
  slippage: number;
} {
  const slippageBps = scenario === "low" ? 1.0 : scenario === "high" ? 3.0 : 1.5;
  const brokeragePerCr = scenario === "low" ? 100 : scenario === "high" ? 300 : 200;

  // Turnovers per gram (assuming buy on Leg A and sell on Leg B or vice-versa)
  const turnover = pricePerGram * 2;

  // CTT: 0.01% on sell side (1 turn)
  const ctt = pricePerGram * 0.0001;

  // Stamp duty: 0.002% on buy side (1 turn)
  const stampDuty = pricePerGram * 0.00002;

  // Exchange turnover fee: 0.0021% on total round trip
  const exchangeFee = turnover * 0.000021;

  // SEBI turnover charge: 0.0001% on total round trip
  const sebiFee = turnover * 0.000001;

  // Brokerage: ₹X per crore on total turnover
  const brokerage = turnover * (brokeragePerCr / 10000000);

  // GST: 18% on (Brokerage + Exchange fee)
  const gst = (brokerage + exchangeFee) * 0.18;

  // Execution slippage buffer
  const slippage = pricePerGram * (slippageBps / 10000);

  const totalFriction = ctt + stampDuty + exchangeFee + sebiFee + brokerage + gst + slippage;

  return { totalFriction, ctt, stampDuty, exchangeFee, sebiFee, gst, slippage };
}

const SAMPLE_CSV_CONTENT = `Date,Symbol,Expiry_Date,Price,Volume,Open_Interest
2026-10-22,GOLDM,05NOV2026,82540,14520,3850
2026-10-22,GOLDTEN,30NOV2026,82980,8920,2410
2026-10-22,GOLDGUINEA,30NOV2026,66420,4120,1180
2026-10-22,GOLDPETAL,30NOV2026,8310,18900,9400
2026-10-21,GOLDM,05NOV2026,82150,13200,3710
2026-10-21,GOLDTEN,30NOV2026,82510,8100,2350
2026-10-21,GOLDGUINEA,30NOV2026,66050,3900,1150
2026-10-21,GOLDPETAL,30NOV2026,8270,17500,9100`;

export const CustomDataInspector: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"simulator" | "file_upload">("simulator");
  const fileInputId = useId();

  // -------------------------------------------------------------
  // Simulator State (Quick Interactive Mode)
  // -------------------------------------------------------------
  const [simSymbolA, setSimSymbolA] = useState<string>("GOLDM");
  const [simPriceA, setSimPriceA] = useState<number>(82540);
  const [simSymbolB, setSimSymbolB] = useState<string>("GOLDTEN");
  const [simPriceB, setSimPriceB] = useState<number>(82980);
  const [simScenario, setSimScenario] = useState<"base" | "low" | "high">("base");

  // -------------------------------------------------------------
  // File Upload State (Batch Mode)
  // -------------------------------------------------------------
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRecord[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [isCopiedTemplate, setIsCopiedTemplate] = useState<boolean>(false);

  // Normalize single quoted price according to MCX standard
  const normalizePrice = useCallback((symbol: string, price: number): number => {
    const spec = MCX_SPECS[symbol.toUpperCase().trim()];
    if (!spec || !spec.fineDivisor || spec.fineDivisor <= 0) {
      return price / 10;
    }
    return price / spec.fineDivisor;
  }, []);

  // Simulator dynamic computation
  const simResults = useMemo(() => {
    const fineA = normalizePrice(simSymbolA, simPriceA);
    const fineB = normalizePrice(simSymbolB, simPriceB);
    const grossSpread = fineA - fineB;
    const absSpread = Math.abs(grossSpread);
    const avgFine = (fineA + fineB) / 2;

    const friction = calculateRoundTripFriction(avgFine, simScenario);
    const hurdle = friction.totalFriction * 1.25;
    const netSpread = absSpread - friction.totalFriction;

    let status: "eligible" | "hurdle_not_met" | "negative" = "negative";
    let statusLabel = "Negative Edge (Spread Below Friction)";

    if (absSpread >= hurdle) {
      status = "eligible";
      statusLabel = "Eligible MCX Opportunity (Clears 1.25x Hurdle)";
    } else if (netSpread > 0) {
      status = "hurdle_not_met";
      statusLabel = "Waiting for Trigger (Positive, but < 1.25x Buffer)";
    }

    return {
      fineA,
      fineB,
      grossSpread,
      absSpread,
      friction,
      hurdle,
      netSpread,
      status,
      statusLabel,
    };
  }, [simSymbolA, simPriceA, simSymbolB, simPriceB, simScenario, normalizePrice]);

// Robust CSV line parser that handles quotes and commas within numeric fields
function parseCsvRow(row: string): string[] {
  const result: string[] = [];
  let current = "";
  let insideQuotes = false;
  for (let i = 0; i < row.length; i++) {
    const char = row[i];
    if (char === '"' || char === "'") {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      result.push(current.trim().replace(/^["']|["']$/g, ""));
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current.trim().replace(/^["']|["']$/g, ""));
  return result;
}

  // Handle CSV file upload
  const handleFileUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // Protection against massive files causing memory exhaustion
      if (file.size > 25 * 1024 * 1024) {
        setParseError("File size exceeds 25 MB. Please provide a daily or trimmed MCX Bhavcopy file.");
        return;
      }

      setFileName(file.name);
      setParseError(null);

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          if (!text) {
            setParseError("The uploaded file is empty.");
            return;
          }

          const lines = text
            .split(/\r?\n/)
            .map((l) => l.trim())
            .filter((l) => l.length > 0);

          if (lines.length < 2) {
            setParseError("CSV file must have a header row and at least one data row.");
            return;
          }

          const headers = parseCsvRow(lines[0]).map((h) => h.trim().toLowerCase().replace(/['"]/g, ""));

          // 1. Symbol column: prioritize exact symbol/commodity/ticker (DO NOT match "instrument name"!)
          let symbolIdx = headers.findIndex((h) => h === "symbol" || h === "tckrsymb" || h === "commodity");
          if (symbolIdx === -1) {
            symbolIdx = headers.findIndex((h) => (h.includes("symbol") || h.includes("tckrsymb") || h.includes("commodity")) && !h.includes("instrument"));
          }
          if (symbolIdx === -1) {
            symbolIdx = headers.findIndex((h) => (h.includes("contract") || h.includes("scrip") || h.includes("fininstrmnm")) && !h.includes("type"));
          }
          if (symbolIdx === -1) {
            symbolIdx = headers.findIndex((h) => h.includes("instrument"));
          }

          // 2. Price column: Close / Settle / LTP (EXCLUDE Strike Price, Previous Close)
          let priceIdx = headers.findIndex((h) =>
            (h.includes("settle") || h.includes("close") || h === "clspric" || h === "close_price" || h === "settle_pr" || h === "settlement_price") &&
            !h.includes("prev") && !h.includes("prvs") && !h.includes("strike") && !h.includes("strk")
          );
          if (priceIdx === -1) {
            priceIdx = headers.findIndex((h) =>
              (h.includes("price") || h.includes("pric") || h.includes("ltp") || h.includes("last")) &&
              !h.includes("strike") && !h.includes("strk") && !h.includes("prev") && !h.includes("prvs")
            );
          }
          if (priceIdx === -1) {
            priceIdx = headers.findIndex((h) => h.includes("open") && !h.includes("interest"));
          }

          // 3. Strike Price column (to filter options)
          const strikeIdx = headers.findIndex((h) => h.includes("strike") || h.includes("strk"));

          // 4. Option Type column (to filter CE / PE options)
          const optTypeIdx = headers.findIndex((h) => (h.includes("option") || h.includes("optn") || h === "opt_type") && !h.includes("name"));

          // 5. Expiry Date column
          const expiryIdx = headers.findIndex((h) => h.includes("expiry") || h.includes("xpry") || h.includes("exp_date") || h.includes("exp_dt"));

          // 6. Trade Date column
          let dateIdx = headers.findIndex((h) => (h.includes("date") || h.includes("traddt") || h.includes("bizdt") || h.includes("timestamp")) && !h.includes("expiry") && !h.includes("xpry"));

          // 7. Volume column
          const volumeIdx = headers.findIndex((h) => (h.includes("volume") || h.includes("vol") || h.includes("ttltradgvol") || h.includes("contracts") || h.includes("qty")) && !h.includes("value") && !h.includes("val"));

          // 8. Open Interest column
          const oiIdx = headers.findIndex((h) => h.includes("open_int") || h.includes("openinterest") || h === "oi" || (h.includes("interest") && !h.includes("chg")));

          if (priceIdx === -1) {
            setParseError("Could not identify a settlement or closing price column in the CSV header.");
            return;
          }

          // Pre-scan: Check if the file contains specific gold contracts
          let hasGoldContracts = false;
          for (let i = 1; i < Math.min(lines.length, 500); i++) {
            const cols = parseCsvRow(lines[i]);
            const s = symbolIdx !== -1 && cols[symbolIdx] ? cols[symbolIdx].toUpperCase() : "";
            if (s.includes("GOLD") || s.startsWith("AU")) {
              hasGoldContracts = true;
              break;
            }
          }

          const records: ParsedRecord[] = [];
          const seenKeys = new Set<string>();
          const MAX_IMPORTED_ROWS = 300;

          for (let i = 1; i < lines.length; i++) {
            if (records.length >= MAX_IMPORTED_ROWS) break;

            const cols = parseCsvRow(lines[i]);
            if (cols.length <= priceIdx) continue;

            // Raw contract symbol extracted from matched column
            const extractedSym = symbolIdx !== -1 && cols[symbolIdx] ? cols[symbolIdx].toUpperCase().trim() : "GOLDM";

            // If file contains gold contracts, filter out non-gold commodities (like Crude, Silver, Copper, Agri)
            if (hasGoldContracts && !extractedSym.includes("GOLD") && !extractedSym.startsWith("AU")) {
              continue;
            }

            // Skip option strikes if strike price or option type is present (only futures for parity radar)
            if (strikeIdx !== -1 && cols[strikeIdx]) {
              const strike = parseFloat(cols[strikeIdx].replace(/[₹,\s]/g, ""));
              if (!isNaN(strike) && strike > 0) continue;
            }
            if (optTypeIdx !== -1 && cols[optTypeIdx]) {
              const opt = cols[optTypeIdx].toUpperCase().trim();
              if (opt === "CE" || opt === "PE" || opt === "CA" || opt === "PA") continue;
            }

            const cleanPrice = cols[priceIdx].replace(/[₹,\s]/g, "");
            const rawPrice = parseFloat(cleanPrice);
            if (isNaN(rawPrice) || rawPrice <= 0) continue;

            // Normalize symbol to recognized MCX key (GOLD, GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL)
            let canonicalSymbol = extractedSym;
            const rootWord = extractedSym.split(/[\s_-]+/)[0];
            if (MCX_SPECS[rootWord]) {
              canonicalSymbol = rootWord;
            } else if (extractedSym.includes("GOLDM")) {
              canonicalSymbol = "GOLDM";
            } else if (extractedSym.includes("GOLDTEN")) {
              canonicalSymbol = "GOLDTEN";
            } else if (extractedSym.includes("GOLDGUINEA")) {
              canonicalSymbol = "GOLDGUINEA";
            } else if (extractedSym.includes("GOLDPETAL")) {
              canonicalSymbol = "GOLDPETAL";
            } else if (extractedSym.startsWith("GOLD")) {
              canonicalSymbol = "GOLD";
            }

            const dateStr = dateIdx !== -1 && cols[dateIdx] ? cols[dateIdx].trim() : new Date().toISOString().split("T")[0];
            const expStr = expiryIdx !== -1 && cols[expiryIdx] ? cols[expiryIdx].trim() : undefined;
            const vol = volumeIdx !== -1 ? parseInt(cols[volumeIdx].replace(/[,\s]/g, ""), 10) : undefined;
            const oi = oiIdx !== -1 ? parseInt(cols[oiIdx].replace(/[,\s]/g, ""), 10) : undefined;

            // Deduplicate rows with identical contract date, symbol and expiry
            const dedupKey = `${dateStr}_${canonicalSymbol}_${expStr || ""}`;
            if (seenKeys.has(dedupKey)) continue;
            seenKeys.add(dedupKey);

            const normPrice = normalizePrice(canonicalSymbol, rawPrice);

            records.push({
              id: `rec_${i}_${canonicalSymbol}_${expStr || ""}_${records.length}`,
              date: dateStr,
              symbol: canonicalSymbol,
              expiryDate: expStr,
              quotedPrice: rawPrice,
              normalizedPrice: normPrice,
              volumeLots: vol,
              openInterest: oi,
            });
          }

          if (records.length === 0) {
            setParseError("No valid gold contract rows could be processed. Please check column names or ensure the file contains MCX Gold contracts.");
            return;
          }

          setParsedRows(records);
        } catch (err: any) {
          console.error("CSV parse error:", err);
          setParseError(`Failed to parse CSV: ${err.message || "Unknown error"}`);
        }
      };

      reader.readAsText(file);
      // Reset input value so the same file can be re-selected if modified
      event.target.value = "";
    },
    [normalizePrice]
  );

  // Load sample demo data in one click
  const handleLoadDemo = useCallback(() => {
    setFileName("sample_mcx_bhavcopy_demo.csv");
    setParseError(null);

    const lines = SAMPLE_CSV_CONTENT.split("\n").filter((l) => l.trim().length > 0);
    const records: ParsedRecord[] = [];

    for (let i = 1; i < lines.length; i++) {
      const [date, symbol, expiry, price, vol, oi] = lines[i].split(",");
      const rawPrice = parseFloat(price);
      records.push({
        id: `demo_${i}_${symbol}`,
        date,
        symbol,
        expiryDate: expiry,
        quotedPrice: rawPrice,
        normalizedPrice: normalizePrice(symbol, rawPrice),
        volumeLots: parseInt(vol),
        openInterest: parseInt(oi),
      });
    }

    setParsedRows(records);
  }, [normalizePrice]);

  // Download template CSV
  const handleDownloadTemplate = useCallback(() => {
    const blob = new Blob([SAMPLE_CSV_CONTENT], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mcx_gold_sample_template.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setIsCopiedTemplate(true);
    setTimeout(() => setIsCopiedTemplate(false), 2000);
  }, []);

  // Compute pairwise relative spread candidates from uploaded records
  const analyzedPairs: AnalyzedPair[] = useMemo(() => {
    if (parsedRows.length < 2) return [];

    // Group by date
    const byDate: Record<string, ParsedRecord[]> = {};
    parsedRows.forEach((r) => {
      if (!byDate[r.date]) byDate[r.date] = [];
      byDate[r.date].push(r);
    });

    const pairs: AnalyzedPair[] = [];

    Object.entries(byDate).forEach(([date, recs]) => {
      // Cap per-date contracts to 25 to prevent quadratic combinatorial explosion
      const safeRecs = recs.slice(0, 25);
      for (let i = 0; i < safeRecs.length; i++) {
        for (let j = i + 1; j < safeRecs.length; j++) {
          const a = safeRecs[i];
          const b = safeRecs[j];
          if (a.symbol === b.symbol && (a.expiryDate || "") === (b.expiryDate || "")) continue;

          const gross = a.normalizedPrice - b.normalizedPrice;
          const absSpread = Math.abs(gross);
          const avgFine = (a.normalizedPrice + b.normalizedPrice) / 2;
          const { totalFriction } = calculateRoundTripFriction(avgFine, "base");
          const hurdle = totalFriction * 1.25;
          const net = absSpread - totalFriction;

          let status: "eligible" | "hurdle_not_met" | "negative" = "negative";
          let statusText = "Spread < Modeled Costs";

          if (absSpread >= hurdle) {
            status = "eligible";
            statusText = "Clears 1.25x MCX Buffer";
          } else if (net > 0) {
            status = "hurdle_not_met";
            statusText = "Positive Edge, Below 1.25x Buffer";
          }

          pairs.push({
            id: `pair_${date}_${a.symbol}_${a.expiryDate || i}_${b.symbol}_${b.expiryDate || j}_${i}_${j}`,
            date,
            contractA: a.expiryDate ? `${a.symbol} (${a.expiryDate})` : a.symbol,
            contractB: b.expiryDate ? `${b.symbol} (${b.expiryDate})` : b.symbol,
            priceA: a.quotedPrice,
            priceB: b.quotedPrice,
            finePriceA: a.normalizedPrice,
            finePriceB: b.normalizedPrice,
            grossSpread: gross,
            modeledCost: totalFriction,
            netSpread: net,
            status,
            statusText,
          });
        }
      }
    });

    // Sort by largest absolute net spread descending and cap to top 100 high-opportunity pairs
    pairs.sort((x, y) => Math.abs(y.netSpread) - Math.abs(x.netSpread));
    return pairs.slice(0, 100);
  }, [parsedRows]);

  return (
    <div className="rounded-lg border border-[#E7E9ED] bg-white overflow-hidden shadow-xs">
      {/* Accordion / Header Bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-white hover:bg-[#FAFBFC] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#B89137]/10 text-[#B89137] border border-[#B89137]/25">
            <Sliders className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-[#17191D]">
                Interactive MCX Custom Data Inspector
              </span>
            </div>
            <p className="text-xs text-[#707784] mt-0.5">
              Simulate custom MCX contract quotes or upload Bhavcopy CSV files to evaluate parity, spreads & statutory friction.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-medium text-[#707784]">
          <span>{isOpen ? "Collapse" : "Open Simulator & Upload"}</span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {/* Main Expanded Workspace */}
      {isOpen && (
        <div className="border-t border-[#E7E9ED] p-5 space-y-6 bg-[#FAFBFC]">
          {/* View Mode Tabs */}
          <div className="flex items-center justify-between border-b border-[#E7E9ED] pb-3">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setActiveTab("simulator")}
                className={cn(
                  "px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5",
                  activeTab === "simulator"
                    ? "bg-[#17191D] text-white"
                    : "bg-white border border-[#E7E9ED] text-[#707784] hover:bg-[#F1F3F6] hover:text-[#17191D]"
                )}
              >
                <Sliders className="h-3.5 w-3.5" />
                <span>Live Quote Simulator</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("file_upload")}
                className={cn(
                  "px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5",
                  activeTab === "file_upload"
                    ? "bg-[#17191D] text-white"
                    : "bg-white border border-[#E7E9ED] text-[#707784] hover:bg-[#F1F3F6] hover:text-[#17191D]"
                )}
              >
                <UploadCloud className="h-3.5 w-3.5" />
                <span>Upload CSV / Bhavcopy</span>
                {parsedRows.length > 0 && (
                  <span className="rounded-full bg-[#B89137] text-white text-[9px] px-1.5 py-0.2">
                    {parsedRows.length}
                  </span>
                )}
              </button>
            </div>

            <div className="text-[11px] text-[#707784]">
              Strictly adheres to official MCX Purity & Quotation Divisors
            </div>
          </div>

          {/* TAB 1: LIVE QUOTE SIMULATOR */}
          {activeTab === "simulator" && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Leg A Input Card */}
                <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#17191D] uppercase tracking-wider">
                      Contract Leg A
                    </span>
                    <span className="text-[11px] text-[#707784]">
                      Quoted: {MCX_SPECS[simSymbolA]?.quotationDivisorGrams}g @ {MCX_SPECS[simSymbolA]?.purityFineness} Purity
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-medium text-[#707784] mb-1">
                        Contract Symbol
                      </label>
                      <select
                        value={simSymbolA}
                        onChange={(e) => setSimSymbolA(e.target.value)}
                        className="w-full rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1.5 text-xs font-semibold text-[#17191D] outline-none"
                      >
                        {Object.keys(MCX_SPECS).map((sym) => (
                          <option key={sym} value={sym}>
                            {sym} — {MCX_SPECS[sym].name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-[#707784] mb-1">
                        Quoted Price (₹)
                      </label>
                      <input
                        type="number"
                        value={simPriceA}
                        onChange={(e) => setSimPriceA(parseFloat(e.target.value) || 0)}
                        step={10}
                        className="w-full rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1.5 text-xs font-mono font-semibold text-[#17191D] outline-none"
                      />
                    </div>
                  </div>

                  <div className="rounded bg-[#FAFBFC] p-2.5 border border-[#F0F2F5] flex justify-between items-baseline text-xs">
                    <span className="text-[#707784]">Normalized Fine Gold (₹/g):</span>
                    <strong className="font-mono text-sm text-[#17191D]">
                      {formatINR(simResults.fineA)}/g
                    </strong>
                  </div>
                </div>

                {/* Leg B Input Card */}
                <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#17191D] uppercase tracking-wider">
                      Contract Leg B
                    </span>
                    <span className="text-[11px] text-[#707784]">
                      Quoted: {MCX_SPECS[simSymbolB]?.quotationDivisorGrams}g @ {MCX_SPECS[simSymbolB]?.purityFineness} Purity
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-medium text-[#707784] mb-1">
                        Contract Symbol
                      </label>
                      <select
                        value={simSymbolB}
                        onChange={(e) => setSimSymbolB(e.target.value)}
                        className="w-full rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1.5 text-xs font-semibold text-[#17191D] outline-none"
                      >
                        {Object.keys(MCX_SPECS).map((sym) => (
                          <option key={sym} value={sym}>
                            {sym} — {MCX_SPECS[sym].name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-[#707784] mb-1">
                        Quoted Price (₹)
                      </label>
                      <input
                        type="number"
                        value={simPriceB}
                        onChange={(e) => setSimPriceB(parseFloat(e.target.value) || 0)}
                        step={10}
                        className="w-full rounded-md border border-[#E7E9ED] bg-white px-2.5 py-1.5 text-xs font-mono font-semibold text-[#17191D] outline-none"
                      />
                    </div>
                  </div>

                  <div className="rounded bg-[#FAFBFC] p-2.5 border border-[#F0F2F5] flex justify-between items-baseline text-xs">
                    <span className="text-[#707784]">Normalized Fine Gold (₹/g):</span>
                    <strong className="font-mono text-sm text-[#17191D]">
                      {formatINR(simResults.fineB)}/g
                    </strong>
                  </div>
                </div>
              </div>

              {/* Friction Tier Selector */}
              <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-[#E7E9ED] text-xs">
                <span className="text-[#707784] font-medium">MCX Statutory & Friction Tier:</span>
                <div className="flex items-center gap-2">
                  {(["low", "base", "high"] as const).map((sc) => (
                    <button
                      key={sc}
                      type="button"
                      onClick={() => setSimScenario(sc)}
                      className={cn(
                        "px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors",
                        simScenario === sc
                          ? "bg-[#B89137] text-white font-semibold"
                          : "bg-[#F7F8FA] text-[#707784] hover:bg-[#E7E9ED]"
                      )}
                    >
                      {sc} Case
                    </button>
                  ))}
                </div>
              </div>

              {/* Simulation Result KPI Box */}
              <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#F0F2F5] pb-3">
                  <div>
                    <span className="text-xs text-[#707784] uppercase font-semibold">Parity Evaluation</span>
                    <h3 className="text-base font-bold text-[#17191D]">
                      {simSymbolA} vs {simSymbolB} Spread
                    </h3>
                  </div>

                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold",
                      simResults.status === "eligible" && "bg-[#ECFDF5] text-[#0D8244] border border-[#0D8244]/25",
                      simResults.status === "hurdle_not_met" && "bg-[#EFF6FF] text-[#2563EB] border border-[#2563EB]/25",
                      simResults.status === "negative" && "bg-[#F7F8FA] text-[#707784] border border-[#E7E9ED]"
                    )}
                  >
                    {simResults.status === "eligible" ? (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5" />
                    )}
                    {simResults.statusLabel}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 bg-[#FAFBFC] rounded border border-[#F0F2F5]">
                    <div className="text-[10px] text-[#707784] uppercase font-medium">Fine Price Spread</div>
                    <div className="text-base font-bold font-mono text-[#17191D] mt-0.5">
                      {formatINR(simResults.grossSpread, { showSign: true })}/g
                    </div>
                  </div>

                  <div className="p-3 bg-[#FAFBFC] rounded border border-[#F0F2F5]">
                    <div className="text-[10px] text-[#707784] uppercase font-medium">Modeled Friction</div>
                    <div className="text-base font-bold font-mono text-[#707784] mt-0.5">
                      {formatINR(simResults.friction.totalFriction)}/g
                    </div>
                  </div>

                  <div className="p-3 bg-[#FAFBFC] rounded border border-[#F0F2F5]">
                    <div className="text-[10px] text-[#707784] uppercase font-medium">Strategy Hurdle (1.25x)</div>
                    <div className="text-base font-bold font-mono text-[#B89137] mt-0.5">
                      {formatINR(simResults.hurdle)}/g
                    </div>
                  </div>

                  <div className="p-3 bg-[#FAFBFC] rounded border border-[#F0F2F5]">
                    <div className="text-[10px] text-[#707784] uppercase font-medium">Net Realized Edge</div>
                    <div
                      className={cn(
                        "text-base font-bold font-mono mt-0.5",
                        simResults.netSpread > 0 ? "text-[#0D8244]" : "text-[#707784]"
                      )}
                    >
                      {formatINR(simResults.netSpread, { showSign: true })}/g
                    </div>
                  </div>
                </div>

                {/* Statutory Fee Breakdown Itemized */}
                <div className="border-t border-[#F0F2F5] pt-3 text-[11px] text-[#707784]">
                  <div className="font-semibold text-[#17191D] mb-1.5">
                    Estimated Statutory & Exchange Charges (Round-trip per gram):
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                    <div>CTT (Sell Leg): ₹{simResults.friction.ctt.toFixed(2)}/g</div>
                    <div>Stamp Duty: ₹{simResults.friction.stampDuty.toFixed(2)}/g</div>
                    <div>Exchange Fee: ₹{simResults.friction.exchangeFee.toFixed(2)}/g</div>
                    <div>SEBI Charge: ₹{simResults.friction.sebiFee.toFixed(2)}/g</div>
                    <div>GST (18%): ₹{simResults.friction.gst.toFixed(2)}/g</div>
                    <div>Slippage: ₹{simResults.friction.slippage.toFixed(2)}/g</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CSV FILE UPLOAD & BATCH INSPECTOR */}
          {activeTab === "file_upload" && (
            <div className="space-y-4">
              {/* Dropzone & Quick Action Bar */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2 rounded-lg border-2 border-dashed border-[#E7E9ED] bg-white p-5 text-center hover:border-[#B89137] transition-colors relative">
                  <input
                    id={fileInputId}
                    type="file"
                    accept=".csv,.txt"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="flex flex-col items-center justify-center space-y-2 pointer-events-none">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#B89137]/10 text-[#B89137]">
                      <UploadCloud className="h-5 w-5" />
                    </div>
                    <div className="text-xs font-semibold text-[#17191D]">
                      {fileName ? (
                        <span className="text-[#0D8244] font-mono">Loaded: {fileName}</span>
                      ) : (
                        "Click or drag MCX Bhavcopy CSV file here"
                      )}
                    </div>
                    <p className="text-[11px] text-[#707784]">
                      Accepts standard MCX Bhavcopy export or custom CSV with columns: Date, Symbol, Price
                    </p>
                  </div>
                </div>

                {/* Quick Demo & Template Helpers */}
                <div className="rounded-lg border border-[#E7E9ED] bg-white p-4 flex flex-col justify-between space-y-3">
                  <div>
                    <span className="text-xs font-bold text-[#17191D] uppercase tracking-wider block mb-1">
                      Quick Start Samples
                    </span>
                    <p className="text-[11px] text-[#707784]">
                      Don&apos;t have a file ready? Load sample MCX records or download our verified template.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <button
                      type="button"
                      onClick={handleLoadDemo}
                      className="w-full flex items-center justify-center gap-1.5 rounded-md bg-[#17191D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#2A2E35] transition-colors"
                    >
                      <Sparkles className="h-3.5 w-3.5 text-[#B89137]" />
                      <span>Load Sample MCX Quotes</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleDownloadTemplate}
                      className="w-full flex items-center justify-center gap-1.5 rounded-md border border-[#E7E9ED] bg-white px-3 py-1.5 text-xs font-medium text-[#707784] hover:bg-[#F1F3F6] hover:text-[#17191D] transition-colors"
                    >
                      {isCopiedTemplate ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-[#0D8244]" />
                          <span className="text-[#0D8244]">Downloaded Template!</span>
                        </>
                      ) : (
                        <>
                          <Download className="h-3.5 w-3.5" />
                          <span>Download Template (.csv)</span>
                        </>
                      )}
                    </button>

                    {parsedRows.length > 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          setParsedRows([]);
                          setFileName(null);
                        }}
                        className="w-full flex items-center justify-center gap-1 text-[11px] text-[#D32F2F] hover:underline pt-1"
                      >
                        <Trash2 className="h-3 w-3" />
                        <span>Clear Uploaded Data</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {parseError && (
                <div className="rounded-lg bg-[#FEF2F2] border border-[#D32F2F]/20 p-3 text-xs text-[#D32F2F] flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{parseError}</span>
                </div>
              )}

              {/* Processed Results Table */}
              {parsedRows.length > 0 && (
                <div className="rounded-lg border border-[#E7E9ED] bg-white overflow-hidden space-y-3">
                  <div className="p-3 border-b border-[#E7E9ED] bg-[#FAFBFC] flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#17191D]">
                      Parsed Records ({parsedRows.length} quotes loaded)
                    </span>
                    <span className="text-[11px] text-[#707784]">
                      Derived Pairs: {analyzedPairs.length} relative-value opportunities evaluated
                    </span>
                  </div>

                  {/* Summary of evaluated pairs */}
                  {analyzedPairs.length > 0 && (
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-semibold text-xs text-[#17191D]">
                          MCX Relative-Spread Cross Matrix:
                        </div>
                        {analyzedPairs.length > 50 && (
                          <span className="text-[10px] text-[#707784] font-medium bg-[#F1F3F6] px-2 py-0.5 rounded">
                            Showing top 50 of {analyzedPairs.length} highest-edge pairs
                          </span>
                        )}
                      </div>
                      <div className="overflow-x-auto max-h-56">
                        <table className="w-full text-left text-xs">
                          <thead className="sticky top-0 bg-[#F7F8FA] border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                            <tr>
                              <th className="py-2 px-3">Date</th>
                              <th className="py-2 px-2">Contract Pair</th>
                              <th className="py-2 px-2 text-right">Fine Price A</th>
                              <th className="py-2 px-2 text-right">Fine Price B</th>
                              <th className="py-2 px-2 text-right">Gross Spread</th>
                              <th className="py-2 px-2 text-right">Modeled Friction</th>
                              <th className="py-2 px-3 text-right">Net Edge</th>
                              <th className="py-2 px-3">MCX Verdict</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#F0F2F5]">
                            {analyzedPairs.slice(0, 50).map((p) => (
                              <tr key={p.id} className="hover:bg-[#FAFBFC]">
                                <td className="py-2 px-3 text-[#707784] font-mono text-[11px]">{p.date}</td>
                                <td className="py-2 px-2 font-medium text-[#17191D]">
                                  {p.contractA} vs {p.contractB}
                                </td>
                                <td className="py-2 px-2 text-right font-mono text-[#707784]">
                                  {formatINR(p.finePriceA)}/g
                                </td>
                                <td className="py-2 px-2 text-right font-mono text-[#707784]">
                                  {formatINR(p.finePriceB)}/g
                                </td>
                                <td className="py-2 px-2 text-right font-mono font-medium">
                                  {formatINR(p.grossSpread, { showSign: true })}/g
                                </td>
                                <td className="py-2 px-2 text-right font-mono text-[#707784]">
                                  {formatINR(p.modeledCost)}/g
                                </td>
                                <td className="py-2 px-3 text-right font-mono font-semibold">
                                  <span className={p.netSpread > 0 ? "text-[#0D8244]" : "text-[#707784]"}>
                                    {formatINR(p.netSpread, { showSign: true })}/g
                                  </span>
                                </td>
                                <td className="py-2 px-3">
                                  <span
                                    className={cn(
                                      "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold",
                                      p.status === "eligible" && "bg-[#ECFDF5] text-[#0D8244]",
                                      p.status === "hurdle_not_met" && "bg-[#EFF6FF] text-[#2563EB]",
                                      p.status === "negative" && "bg-[#F1F3F6] text-[#707784]"
                                    )}
                                  >
                                    {p.statusText}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Raw Uploaded Records list */}
                  <div className="p-3 border-t border-[#F0F2F5]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-semibold text-xs text-[#17191D]">
                        Individual Normalized Quotes:
                      </div>
                      {parsedRows.length > 50 && (
                        <span className="text-[10px] text-[#707784] font-medium bg-[#F1F3F6] px-2 py-0.5 rounded">
                          Showing first 50 of {parsedRows.length} imported quotes
                        </span>
                      )}
                    </div>
                    <div className="overflow-x-auto max-h-48">
                      <table className="w-full text-left text-[11px]">
                        <thead className="sticky top-0 bg-[#F7F8FA] border-b border-[#E7E9ED] text-[#707784]">
                          <tr>
                            <th className="py-1.5 px-3">Date</th>
                            <th className="py-1.5 px-2">Symbol</th>
                            <th className="py-1.5 px-2">Expiry</th>
                            <th className="py-1.5 px-2 text-right">Quoted Price</th>
                            <th className="py-1.5 px-2 text-right">Normalized (₹/g)</th>
                            <th className="py-1.5 px-2 text-right">Volume</th>
                            <th className="py-1.5 px-3 text-right">OI</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#F0F2F5]">
                          {parsedRows.slice(0, 50).map((r) => (
                            <tr key={r.id} className="hover:bg-[#FAFBFC]">
                              <td className="py-1.5 px-3 text-[#707784] font-mono">{r.date}</td>
                              <td className="py-1.5 px-2 font-medium text-[#17191D]">{r.symbol}</td>
                              <td className="py-1.5 px-2 text-[#707784]">{r.expiryDate || "—"}</td>
                              <td className="py-1.5 px-2 text-right font-mono">{formatINR(r.quotedPrice)}</td>
                              <td className="py-1.5 px-2 text-right font-mono font-medium text-[#B89137]">
                                {formatINR(r.normalizedPrice)}/g
                              </td>
                              <td className="py-1.5 px-2 text-right font-mono text-[#707784]">
                                {r.volumeLots ? r.volumeLots.toLocaleString() : "—"}
                              </td>
                              <td className="py-1.5 px-3 text-right font-mono text-[#707784]">
                                {r.openInterest ? r.openInterest.toLocaleString() : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

