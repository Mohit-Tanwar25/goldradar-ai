import {
  OverviewResponse,
  CompareContractsResponse,
  FuturesCurveResponse,
  OpportunitiesResponse,
  BacktestResponse,
  MethodologyResponse,
} from "@/types/api";

const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
let cleanBaseUrl = RAW_API_URL.trim().replace(/\/+$/, "");
if (cleanBaseUrl && !cleanBaseUrl.startsWith("http://") && !cleanBaseUrl.startsWith("https://")) {
  cleanBaseUrl = `https://${cleanBaseUrl}`;
}
const API_BASE_URL = cleanBaseUrl;

async function fetchJson<T>(endpoint: string): Promise<T> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;
  try {
    const res = await fetch(url, {
      headers: {
        Accept: "application/json",
      },
      next: { revalidate: 60 },
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(
        `API request failed with status ${res.status}: ${errText || res.statusText}`
      );
    }

    return (await res.json()) as T;
  } catch (error: any) {
    console.error(`Fetch error at ${url}:`, error);
    if (error?.message?.includes("Failed to fetch") || error?.name === "TypeError") {
      throw new Error(
        "Unable to reach the analytics backend. If the service was idle on Render Free tier, it may take 30–50 seconds to wake up. Please click Retry."
      );
    }
    throw error;
  }
}

export async function fetchOverview(): Promise<OverviewResponse> {
  return fetchJson<OverviewResponse>("/api/overview");
}

export async function fetchCompareContracts(
  symbolA = "GOLDM",
  symbolB = "GOLDTEN",
  liquidityFilter = false
): Promise<CompareContractsResponse> {
  const params = new URLSearchParams({
    symbol_a: symbolA,
    symbol_b: symbolB,
    liquidity_filter: String(liquidityFilter),
  });
  return fetchJson<CompareContractsResponse>(`/api/contracts/compare?${params.toString()}`);
}

export async function fetchFuturesCurve(
  snapshotDate?: string
): Promise<FuturesCurveResponse> {
  const params = new URLSearchParams();
  if (snapshotDate) {
    params.set("snapshot_date", snapshotDate);
  }
  const query = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<FuturesCurveResponse>(`/api/futures/curve${query}`);
}

export async function fetchOpportunities(
  scenario = "base",
  symbolFilter = "ALL",
  limit = 50
): Promise<OpportunitiesResponse> {
  const params = new URLSearchParams({
    cost_scenario: scenario,
    symbol_filter: symbolFilter,
    limit: String(limit),
  });
  return fetchJson<OpportunitiesResponse>(`/api/opportunities?${params.toString()}`);
}

export async function fetchBacktest(
  scenario = "base",
  strategy = "All Strategies",
  fold = "All Folds"
): Promise<BacktestResponse> {
  const params = new URLSearchParams({
    cost_scenario: scenario,
    strategy_name: strategy,
    fold_id: fold,
  });
  return fetchJson<BacktestResponse>(`/api/backtest?${params.toString()}`);
}

export async function fetchMethodology(): Promise<MethodologyResponse> {
  return fetchJson<MethodologyResponse>("/api/methodology");
}
