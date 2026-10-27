export type ContractSymbol = "GOLDM" | "GOLDTEN" | "GOLDGUINEA" | "GOLDPETAL";

export interface OverviewResponse {
  metadata: {
    latest_date: string;
    latest_date_display: string;
    total_sessions: number;
    total_records: number;
    coverage_years: string;
    exchange: string;
    verification_status: string;
  };
  kpis: {
    normalized_gold_price: number;
    benchmark_symbol: string;
    active_contracts_count: number;
    active_contract_symbols: string[];
    historical_sessions: number;
    historical_records: number;
    market_structure: string;
    median_roll_yield_pct: number;
    net_strategy_pnl: number;
    gross_strategy_pnl: number;
    total_costs: number;
  };
  active_contracts: Array<{
    symbol: ContractSymbol;
    name: string;
    trading_unit: string;
    purity: number | string;
    quotation_unit: string;
    delivery_logic: string;
    lot_size_grams: number;
    latest_quoted_price: number | null;
    latest_fine_price: number | null;
    days_to_expiry: number | null;
    expiry_date: string | null;
    volume_lots: number;
    open_interest_lots: number;
  }>;
  price_history: Array<{
    date: string;
    GOLDM?: number | null;
    GOLDTEN?: number | null;
    GOLDGUINEA?: number | null;
    GOLDPETAL?: number | null;
  }>;
  recent_opportunities: Array<{
    candidate_id: string;
    date: string;
    symbol_leg_a: string;
    symbol_leg_b: string;
    contract_key_leg_a: string;
    contract_key_leg_b: string;
    fine_price_spread_per_gram: number;
    candidate_type: string;
  }>;
  dataset_health: {
    status: string;
    verified_count: number;
    collision_free: boolean;
  };
}

export interface ContractSpecDetail {
  symbol: string;
  name: string;
  trading_unit: string;
  purity: number | string;
  quotation_unit: string;
  delivery_logic: string;
  lot_size_grams: number;
  latest_fine_price: number | null;
}

export interface CompareContractsResponse {
  symbol_a: string;
  symbol_b: string;
  contract_a: ContractSpecDetail;
  contract_b: ContractSpecDetail;
  statistics: {
    pair: string;
    total_observations: number;
    mean_spread: number;
    median_spread: number;
    std_spread: number;
    min_spread: number;
    max_spread: number;
    latest_spread: number;
    latest_relative_pct: number;
  };
  timeseries: Array<{
    date: string;
    spread: number;
    relative_pct: number;
    rolling_mean: number | null;
    upper_band: number | null;
    lower_band: number | null;
  }>;
  distribution: Array<{
    bin_center: number;
    bin_start: number;
    bin_end: number;
    count: number;
  }>;
}

export interface FuturesCurveResponse {
  selected_date: string;
  available_dates: string[];
  market_structure: string;
  median_annualized_roll_yield_pct: number;
  curve_points: Array<{
    contract_key: string;
    symbol: string;
    name: string;
    expiry_date: string;
    days_to_expiry: number;
    close_fine_per_gram: number;
    expiry_rank: number;
  }>;
  roll_yield_history: Array<{
    date: string;
    symbol: string;
    nearer_expiry: string;
    deferred_expiry: string;
    days_between: number;
    fine_calendar_spread: number;
    annualized_spread_pct: number;
    regime: string;
  }>;
}

export interface OpportunitiesResponse {
  scenario: string;
  funnel: Array<{
    stage: string;
    count: number;
    description: string;
  }>;
  cost_scenarios_breakdown: Array<{
    scenario: string;
    label: string;
    brokerage_per_crore: number;
    slippage_bps: number;
    ctt_pct: number;
    stamp_duty_pct: number;
    exchange_fee_pct: number;
    sebi_turnover_pct: number;
    gst_pct: number;
  }>;
  opportunities: Array<{
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
    passes_liquidity: boolean;
  }>;
  total_count: number;
}

export interface BacktestResponse {
  scenario: string;
  selected_strategy: string;
  selected_fold: string;
  available_strategies: string[];
  available_folds: string[];
  kpis: {
    trade_attempts: number;
    completed_trades: number;
    rejected_trades: number;
    unresolved_trades?: number;
    completion_rate_pct: number;
    winning_trades: number;
    losing_trades: number;
    win_rate_pct: number;
    gross_pnl_inr: number;
    total_costs_inr: number;
    net_pnl_inr: number;
    mean_net_pnl_per_trade_inr: number;
    median_net_pnl_per_trade_inr?: number;
    mean_net_pnl_per_gram?: number;
    profit_factor: number | null;
    realized_max_drawdown_inr: number;
    mean_holding_days: number;
    pnl_reconciled: boolean;
    max_reconciliation_diff: number;
  };
  equity_curve: Array<{
    date: string;
    trade_id: string;
    net_pnl: number;
    cum_net_pnl: number;
    running_peak: number;
    drawdown: number;
  }>;
  strategies: Array<{
    strategy_name: string;
    total_trade_attempts: number;
    completed_trades: number;
    rejected_trades: number;
    win_rate_pct: number;
    gross_pnl_inr: number;
    total_costs_inr: number;
    net_pnl_inr: number;
    profit_factor: number | null;
    realized_max_drawdown_inr: number;
    mean_holding_days: number;
  }>;
  walk_forward_folds: Array<{
    fold_id: string;
    strategy_name: string;
    train_start_date: string;
    train_end_date: string;
    test_start_date: string;
    test_end_date: string;
    completed_trades: number;
    win_rate_pct: number;
    net_pnl_inr: number;
    profit_factor: number | null;
    realized_max_drawdown_inr: number;
  }>;
  trade_ledger: Array<{
    trade_id: string;
    signal_date: string;
    entry_date: string;
    exit_date: string;
    strategy_name: string;
    symbol_leg_a: string;
    symbol_leg_b: string;
    signal_direction: string;
    gross_pnl_inr: number | null;
    total_modeled_cost_inr: number | null;
    net_pnl_inr: number | null;
    trade_completion_status: string;
    rejection_or_exclusion_reason: string | null;
  }>;
}

export interface DatasetItem {
  filename: string;
  description: string;
  exists: boolean;
  size_bytes: number;
  rows: number;
  status: string;
}

export interface MethodologyResponse {
  active_universe: {
    contracts: Array<{
      symbol: string;
      name: string;
      trading_unit: string;
      quotation_unit: string;
      purity_fineness: number | string;
      purity_factor: number;
      lot_size_grams: number;
      delivery_logic: string;
      tick_size_inr: number;
    }>;
    excluded_products: Array<{
      symbol: string;
      notional_value: string;
      reason: string;
    }>;
  };
  normalization_formula: {
    title: string;
    formula: string;
    explanation: string;
  };
  liquidity_rules: Record<string, any>;
  cost_assumptions: Record<string, any>;
  backtest_methodology: Record<string, any>;
  datasets: DatasetItem[];
  disclaimer: string;
}
