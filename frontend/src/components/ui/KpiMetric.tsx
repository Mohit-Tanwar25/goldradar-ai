import React from "react";
import { cn } from "@/lib/utils";

interface KpiMetricProps {
  label: string;
  value: string | number;
  subtext?: string;
  variant?: "default" | "gold" | "positive" | "negative" | "blue";
  className?: string;
}

export const KpiMetric: React.FC<KpiMetricProps> = ({
  label,
  value,
  subtext,
  variant = "default",
  className,
}) => {
  const valueColor = {
    default: "text-[#17191D]",
    gold: "text-[#B89137]",
    positive: "text-[#0D8244]",
    negative: "text-[#D32F2F]",
    blue: "text-[#2563EB]",
  }[variant];

  return (
    <div className={cn("flex flex-col py-1", className)}>
      <span className="text-[11px] font-medium uppercase tracking-wider text-[#707784]">
        {label}
      </span>
      <span className={cn("text-xl font-semibold tracking-tight sm:text-2xl mt-0.5", valueColor)}>
        {value}
      </span>
      {subtext && (
        <span className="text-[11px] text-[#707784] mt-0.5 font-normal">
          {subtext}
        </span>
      )}
    </div>
  );
};
