"use client";

import React, { useState, useEffect } from "react";
import { MethodologyResponse } from "@/types/api";
import { fetchMethodology } from "@/lib/api";
import { LoadingSkeleton, ErrorMessage } from "@/components/ui/Feedback";
import { formatNumber } from "@/lib/utils";
import { ShieldCheck, BookOpen, AlertCircle, FileText, CheckCircle2 } from "lucide-react";

export const DataMethodologyView: React.FC = () => {
  const [data, setData] = useState<MethodologyResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchMethodology();
        setData(res);
      } catch (err: any) {
        setError(err?.message || "Failed to load methodology documentation.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-8 max-w-5xl">
      {/* 1. Header */}
      <div className="border-b border-[#E7E9ED] pb-4">
        <h2 className="text-xl font-bold tracking-tight text-[#17191D] sm:text-2xl">
          Data Architecture & Research Methodology
        </h2>
        <p className="mt-1 text-xs text-[#707784]">
          Comprehensive technical specifications, mathematical normalization formulas, dataset inventory, and backtesting protocols.
        </p>
      </div>

      {loading && <LoadingSkeleton rows={5} height="h-32" />}
      {error && <ErrorMessage message={error} />}

      {!loading && !error && data && (
        <>
          {/* 2. Active Universe vs Excluded Contracts */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#17191D] uppercase tracking-wider text-[#707784]">
              01. Contract Universe & Rationale
            </h3>
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                      <th className="py-2 font-medium">Symbol</th>
                      <th className="py-2 font-medium">Contract Name</th>
                      <th className="py-2 font-medium">Lot Size</th>
                      <th className="py-2 font-medium">Quotation Unit</th>
                      <th className="py-2 font-medium">Fineness</th>
                      <th className="py-2 font-medium">Delivery Logic</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F0F2F5]">
                    {data.active_universe.contracts.map((c) => (
                      <tr key={c.symbol} className="hover:bg-[#FAFBFC]">
                        <td className="py-2.5 font-bold text-[#17191D]">{c.symbol}</td>
                        <td className="py-2.5 text-[#707784]">{c.name}</td>
                        <td className="py-2.5 font-medium text-[#17191D]">{c.lot_size_grams} grams</td>
                        <td className="py-2.5 text-[#707784]">{c.quotation_unit}</td>
                        <td className="py-2.5 text-[#707784]">{c.purity_fineness}</td>
                        <td className="py-2.5 text-[#707784]">{c.delivery_logic}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Exclusion Note */}
              <div className="rounded bg-[#F7F8FA] p-3 text-xs leading-relaxed text-[#707784]">
                <strong className="text-[#17191D]">Why Standard Wholesale GOLD (1 kg) is Excluded:</strong> The benchmark 1kg wholesale contract has a notional value exceeding ₹85 Lakh per lot. 
                Pairing a 1kg contract against 1g GOLDPETAL creates an extreme 1:1,000 lot ratio. 
                This leads to integer-lot distortion, severe portfolio drawdowns, and illiquid rebalancing. 
                Our research focuses on the 4 accessible retail & mini products.
              </div>
            </div>
          </div>

          {/* 3. Mathematical Normalization Formula */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#17191D] uppercase tracking-wider text-[#707784]">
              02. Mathematical Normalization
            </h3>
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-5 space-y-3">
              <div className="font-semibold text-xs text-[#17191D]">
                {data.normalization_formula.title}
              </div>
              <div className="rounded bg-[#FBF7EE] p-3 font-mono text-xs text-[#B89137] border border-[#E7E9ED]">
                {data.normalization_formula.formula}
              </div>
              <p className="text-xs text-[#707784] leading-relaxed">
                {data.normalization_formula.explanation}
              </p>
            </div>
          </div>

          {/* 4. Canonical Dataset Inventory */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#17191D] uppercase tracking-wider text-[#707784]">
              03. Production Datasets & SHA-256 Integrity
            </h3>
            <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#E7E9ED] text-[11px] text-[#707784]">
                      <th className="py-2 font-medium">Dataset File</th>
                      <th className="py-2 font-medium">Phase Description</th>
                      <th className="py-2 text-right font-medium">Rows</th>
                      <th className="py-2 text-right font-medium">Size</th>
                      <th className="py-2 text-center font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F0F2F5]">
                    {data.datasets.map((ds) => (
                      <tr key={ds.filename} className="hover:bg-[#FAFBFC]">
                        <td className="py-2 font-mono text-[11px] text-[#17191D]">{ds.filename}</td>
                        <td className="py-2 text-[#707784]">{ds.description}</td>
                        <td className="py-2 text-right text-[#17191D]">{formatNumber(ds.rows)}</td>
                        <td className="py-2 text-right text-[#707784]">
                          {(ds.size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </td>
                        <td className="py-2 text-center">
                          <span className="inline-flex items-center gap-1 rounded bg-[#ECFDF5] px-1.5 py-0.5 text-[10px] font-semibold text-[#0D8244]">
                            <CheckCircle2 className="h-3 w-3" />
                            {ds.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* 5. Walk-Forward Protocol & Execution Rules */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#17191D] uppercase tracking-wider text-[#707784]">
              04. Backtesting Assumptions & Risk Controls
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-[#E7E9ED] bg-white p-5 text-xs text-[#707784] space-y-2">
                <h4 className="font-semibold text-xs text-[#17191D]">Walk-Forward Anchoring</h4>
                <p className="leading-relaxed">
                  10 distinct out-of-sample test folds prevent curve overfitting. Parameter estimation is locked during training windows and evaluated strictly on subsequent unseen sessions.
                </p>
                <div className="pt-2 border-t border-[#F0F2F5] text-[11px]">
                  <strong>Lookahead Bias:</strong> Zero lookahead. Signals triggered at session T enter strictly on session T+1.
                </div>
              </div>

              <div className="rounded-lg border border-[#E7E9ED] bg-white p-5 text-xs text-[#707784] space-y-2">
                <h4 className="font-semibold text-xs text-[#17191D]">Tender Window Restrictions</h4>
                <p className="leading-relaxed">
                  MCX mandates a 5-day pre-expiry tender notice period where physical delivery intentions are submitted and margin requirements increase steeply.
                </p>
                <div className="pt-2 border-t border-[#F0F2F5] text-[11px]">
                  <strong>Execution Filter:</strong> No new positions are permitted within 5 business days of contract maturity.
                </div>
              </div>
            </div>
          </div>

          {/* 6. Institutional Research Disclaimer */}
          <div className="rounded-lg border border-[#E7E9ED] bg-white p-5">
            <h4 className="font-semibold text-xs text-[#17191D] mb-1">
              Institutional Research & Regulatory Disclaimer
            </h4>
            <p className="text-xs text-[#707784] leading-relaxed">
              {data.disclaimer}
            </p>
          </div>
        </>
      )}
    </div>
  );
};
