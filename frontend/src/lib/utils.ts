import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(
  val: number | null | undefined,
  options?: { showSign?: boolean; decimals?: number }
): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  const decimals = options?.decimals ?? 2;
  const absVal = Math.abs(val);
  const formatted = new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(absVal);

  if (val > 0 && options?.showSign) {
    return `+₹${formatted}`;
  }
  if (val < 0) {
    return `-₹${formatted}`;
  }
  return `₹${formatted}`;
}

export function formatPct(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  return `${val >= 0 ? "+" : ""}${val.toFixed(decimals)}%`;
}

export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  return new Intl.NumberFormat("en-IN").format(val);
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}
