"use client";

import React from "react";
import { Menu, Calendar, Database, RefreshCw } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface HeaderProps {
  title: string;
  subtitle?: string;
  latestDate?: string;
  onToggleMobile: () => void;
  actions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  latestDate,
  onToggleMobile,
  actions,
}) => {
  return (
    <header className="sticky top-0 z-30 flex min-h-[64px] items-center justify-between border-b border-[#E7E9ED] bg-white px-5 py-3 sm:px-8">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobile}
          className="rounded p-1.5 text-[#707784] hover:bg-[#F1F3F6] lg:hidden"
          aria-label="Toggle Navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div>
          <h1 className="text-base font-semibold tracking-tight text-[#17191D] sm:text-lg">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-[#707784] line-clamp-1">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {actions}

        {latestDate && (
          <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-[#E7E9ED] bg-[#F7F8FA] px-2.5 py-1 text-[11px] text-[#707784]">
            <Calendar className="h-3 w-3 text-[#B89137]" />
            <span>
              Recorded Session:{" "}
              <strong className="text-[#17191D] font-medium">
                {formatDate(latestDate)}
              </strong>
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
