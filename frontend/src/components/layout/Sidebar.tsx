"use client";

import React from "react";
import {
  LayoutDashboard,
  ArrowLeftRight,
  TrendingUp,
  Zap,
  FlaskConical,
  BookOpen,
  ShieldCheck,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type NavPage =
  | "overview"
  | "compare"
  | "futures"
  | "opportunities"
  | "backtest"
  | "methodology";

interface SidebarProps {
  currentPage: NavPage;
  onSelectPage: (page: NavPage) => void;
  mobileOpen: boolean;
  onToggleMobile: () => void;
}

const NAV_ITEMS: Array<{
  id: NavPage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "compare", label: "Compare Contracts", icon: ArrowLeftRight },
  { id: "futures", label: "Futures Curve", icon: TrendingUp },
  { id: "opportunities", label: "Opportunities & Costs", icon: Zap },
  { id: "backtest", label: "Backtest Performance", icon: FlaskConical },
  { id: "methodology", label: "Data & Methodology", icon: BookOpen },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  mobileOpen,
  onToggleMobile,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-xs lg:hidden"
          onClick={onToggleMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 flex w-64 flex-col border-r border-[#E7E9ED] bg-white transition-transform duration-200 ease-in-out lg:static lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between border-b border-[#E7E9ED] px-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[#B89137] text-white font-bold text-xs tracking-wider">
              AU
            </div>
            <div>
              <div className="font-semibold text-sm tracking-tight text-[#17191D]">
                Gold Contract Radar
              </div>
              <div className="text-[10px] uppercase font-medium tracking-wider text-[#707784]">
                MCX Derivatives
              </div>
            </div>
          </div>
          <button
            onClick={onToggleMobile}
            className="rounded p-1 text-[#707784] hover:bg-[#F1F3F6] lg:hidden"
            aria-label="Close Navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectPage(item.id);
                  if (mobileOpen) onToggleMobile();
                }}
                className={cn(
                  "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-colors",
                  isActive
                    ? "bg-[#F1F3F6] text-[#17191D] font-semibold"
                    : "text-[#707784] hover:bg-[#FAFBFC] hover:text-[#17191D]"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 transition-colors",
                    isActive ? "text-[#B89137]" : "text-[#707784] group-hover:text-[#17191D]"
                  )}
                />
                <span>{item.label}</span>
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-[#B89137]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Compact Footer Status */}
        <div className="border-t border-[#E7E9ED] p-4 text-[11px] text-[#707784]">
          <div className="flex items-center gap-1.5 font-medium text-[#17191D] mb-1">
            <ShieldCheck className="h-3.5 w-3.5 text-[#0D8244]" />
            <span>Active Universe Verified</span>
          </div>
          <div className="text-[#9CA3AF] text-[10px] leading-relaxed">
            4 Contracts • 701 Sessions
            <br />
            12 Processed Datasets Online
          </div>
        </div>
      </aside>
    </>
  );
};
