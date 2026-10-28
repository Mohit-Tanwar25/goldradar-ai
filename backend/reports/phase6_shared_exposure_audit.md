# Gold Contract Radar — Phase 6 Final Shared Exposure Audit and Correction Report

**Project:** Gold Contract Radar — MCX Commodity Derivatives Intelligence  
**Phase:** Phase 6 — Walk-Forward Backtesting & Execution Feasibility Analysis  
**Audit Scope:** Shared-Contract Overlap, Portfolio Exposure Limits & Deterministic Allocation Policy  
**Date:** 2026-10-25  
**Auditor / Agent:** Antigravity IDE  

---

## 1. Executive Summary

During the final logic audit of Phase 6, an independent inspection revealed that while `active_pair_positions` successfully prevented concurrent trades on the exact same contract *pair*, it **failed to prevent shared-contract overlap across different pairs and across strategies**. Specifically:
- **Trade A** (e.g. `GOLD` vs `GOLDM`) and **Trade B** (e.g. `GOLD` vs `GOLDGUINEA`) share the identical underlying contract `GOLD_05JUN2026`.
- In calendar spreads, two adjacent spread positions (e.g. Month 1 vs Month 2 and Month 2 vs Month 3) could simultaneously buy and sell Month 2 at the exact same Open, producing an artificial, opposing "wash" position with double frictional transaction costs.
- In multi-strategy execution, Strategy A and Strategy B could simultaneously take positions in the exact same contract.

### Key Audit Findings & Correction
1. **Defect Confirmed**: In the prior implementation, 95 out of 120 traded contracts experienced concurrent overlapping trades (reaching up to 7 concurrent trades and 23 gross lots on single contracts like `GOLDPETAL_31OCT2025` and `GOLDGUINEA_31OCT2025`). In addition, 2,728 opposing position instances and 2,462 multi-strategy conflict instances occurred.
2. **Defect Corrected**: A deterministic chronological portfolio allocation policy was designed and implemented in [src/run_walk_forward_backtest.py](file:///d:/Akshitakumawat/hackkk/src/run_walk_forward_backtest.py), backed by configurable controls in [config/backtest_config.json](file:///d:/Akshitakumawat/hackkk/config/backtest_config.json).
3. **Current Exposure Status**: All 114 distinct contracts traded across all 10 folds now have **zero (0) concurrent overlaps, zero (0) opposing positions, and zero (0) multi-strategy conflicts**.
4. **All Regression Tests Passing**: 14 new synthetic and integration tests (Tests 25 to 38) were added to [tests/test_walk_forward_backtest.py](file:///d:/Akshitakumawat/hackkk/tests/test_walk_forward_backtest.py). The entire repository test suite (84 tests) passes with 100% success.
5. **Upstream Datasets Verified**: All Phase 1–5 datasets match their canonical SHA-256 integrity hashes byte-for-byte.

---

## 2. Portfolio Exposure Controls Defined

To ensure auditability, research-backtest exposure controls were added to [config/backtest_config.json](file:///d:/Akshitakumawat/hackkk/config/backtest_config.json):

```json
"portfolio_exposure_limits": {
  "allow_shared_contract_overlap": false,
  "max_concurrent_positions_per_contract": 1,
  "max_gross_lots_per_contract": 10,
  "max_net_lots_per_contract": 10,
  "max_underlying_grams_per_contract": 1000,
  "allow_multi_strategy_contract_sharing": false,
  "allow_opposing_contract_positions": false,
  "position_release_timing": "next_session_after_exit",
  "tie_breaker_priority": "signal_strength_descending"
}
```

### Rationale and Specification:
- **`allow_shared_contract_overlap: false`**: Enforces strict contract-level exclusion. A contract cannot be occupied by multiple trades simultaneously, even if the paired leg differs.
- **`max_concurrent_positions_per_contract: 1`**: Cap on concurrent open legs per `contract_key = (symbol, expiry_date)`.
- **`max_gross_lots_per_contract: 10` & `max_net_lots_per_contract: 10`**: Absolute aggregate and directional limits on lots per contract.
- **`max_underlying_grams_per_contract: 1000`**: Underlying commodity mass ceiling (equivalent to 1 kg = 1 large GOLD contract or 10 GOLDM contracts).
- **`allow_multi_strategy_contract_sharing: false`**: Prohibits Strategy A and Strategy B from claiming the same contract concurrently.
- **`allow_opposing_contract_positions: false`**: Prohibits simultaneous Long and Short positions in the same contract.
- **`position_release_timing: "next_session_after_exit"`**: Because exit execution occurs at Date $E$ Open, the contract remains legally occupied during Date $E$. Exposure is released for new entry signals only on Date $E+1$ (`entry_date > exit_date`).
- **`tie_breaker_priority: "signal_strength_descending"`**: When multiple signals trigger on the same Date $t$ Close, candidates are sorted deterministically by:
  $$\text{Strength} = \frac{|\text{Signal Metric Value}|}{\text{Training Threshold}} \quad (\text{Descending})$$
  Ties broken by `candidate_id` ASC. This policy uses **strictly information available at Date $t$ Close** with zero future lookahead.

---

## 3. Implementation Details

In [src/run_walk_forward_backtest.py](file:///d:/Akshitakumawat/hackkk/src/run_walk_forward_backtest.py):
1. **Contract-Level Tracking**: Replaced pair-level dictionary `active_pair_positions` with `active_contract_positions = defaultdict(list)`, mapping each `contract_key` to its active position lifecycle.
2. **Deterministic Pre-Sorting**: Sorted test window candidates deterministically by `(date ASC, -strength, candidate_id ASC)`.
3. **Chronological Pruning**: At each candidate evaluation on `entry_date`, pruned positions where `exit_date < entry_date`.
4. **Pre-Entry Limit Checks**: Evaluated both legs `key_a` and `key_b` against concurrency, multi-strategy, opposing direction, gross lot, net lot, and underlying gram limits.
5. **Audit Ledger Preservation**: Rejected candidates are appended to Output A with explicit machine-readable rejection reasons:
   - `rejected_existing_contract_position`
   - `rejected_multi_strategy_contract_conflict`
   - `rejected_opposing_contract_position`
   - `rejected_gross_exposure_limit`
   - `rejected_net_exposure_limit`
   - `rejected_contract_gram_limit`
6. **Leg Registration**: Upon fill and modeled exit determination, registered both `key_a` and `key_b` into `active_contract_positions` until `exit_date`.

---

## 4. Before-and-After Comparison

### A. Overlap and Conflict Statistics

| Metric | Before Fix (Pair-Level Only) | After Fix (Contract-Level Portfolio Policy) | Status |
| :--- | :---: | :---: | :---: |
| Distinct Traded Contracts | 120 | 114 | Verified |
| Contracts with Overlapping Trades ($>1$) | **95 / 120 (79.2%)** | **0 / 114 (0.0%)** | **ELIMINATED** |
| Max Concurrent Trades on Single Contract | **7** | **1** | **RESOLVED** |
| Max Concurrent Gross Lots on Contract | **23 lots** | **10 lots (Max single-trade lot)** | **ENFORCED** |
| Simultaneous Opposing Positions | **2,728 instances** | **0 instances** | **ELIMINATED** |
| Multi-Strategy Concurrent Sharing | **2,462 instances** | **0 instances** | **ELIMINATED** |

---

### B. Strategy Performance Metrics (Base Cost Scenario)

| Performance Metric | Strategy A (Before) | Strategy A (After) | Strategy B (Before) | Strategy B (After) |
| :--- | :---: | :---: | :---: | :---: |
| **Total Trade Attempts** | 1,869 | 1,869 | 8,610 | 8,610 |
| **Completed Trades** | 111 | **87** | 633 | **180** |
| **Unresolved Trades** | 0 | **0** | 1 | **1** |
| **Rejected Trade Attempts** | 1,758 | **1,782** | 7,976 | **8,429** |
| **Rejection: Existing Position** | 1,673 (pair) | **1,697 (contract)** | 7,746 (pair) | **8,259 (contract)** |
| **Winning Trades** | 56 | **43** | 204 | **61** |
| **Losing Trades** | 55 | **44** | 429 | **119** |
| **Win Rate (%)** | 50.45% | **49.43%** | 32.23% | **33.89%** |
| **Gross P&L (₹)** | +₹81,894.00 | **+₹58,232.00** | -₹986,220.00 | **-₹225,083.00** |
| **Modeled Costs (₹)** | ₹23,348.04 | **₹18,337.40** | ₹465,972.05 | **₹104,315.50** |
| **Net P&L (₹)** | +₹58,545.96 | **+₹39,894.60** | -₹1,452,192.05 | **-₹329,398.50** |
| **Profit Factor** | 1.341 | **1.368** | 0.449 | **0.653** |
| **Realized Max Drawdown (₹)**| ₹53,744.46 | **₹53,744.46** | ₹1,452,192.05 | **₹494,524.96** |
| **Mean Holding Days** | 8.87 | **9.09** | 8.16 | **8.24** |

> **Key Observation**: Eliminating overlapping positions on the same contract reduced simultaneous exposure while preserving the fundamental character of both strategies: Strategy A remained moderately profitable after all transaction costs (Net P&L ₹+39,894.60, PF 1.368), while Strategy B losses and drawdown were significantly curtailed by preventing compounding losses on concurrent calendar spreads.

---

### C. Output D Diagnostics Reconciliation

From [data/processed/mcx_gold_execution_diagnostics.csv](file:///d:/Akshitakumawat/hackkk/data/processed/mcx_gold_execution_diagnostics.csv):

| Diagnostic Metric | Count | Category | Description |
| :--- | :---: | :--- | :--- |
| `total_candidates_screened` | 27,802 | Eligibility & Screening | Total candidates evaluated in backtest |
| `candidates_in_test_windows` | 27,802 | Eligibility & Screening | Candidates occurring within test window boundaries |
| `signals_triggered` | 10,479 | Signal Triggers | Candidate observations exceeding training threshold |
| `trades_filled` | 268 | Execution Feasibility | Trade attempts filled at t+1 Open on both legs |
| `trades_completed` | 267 | Execution Feasibility | Trades cleanly exited at Open |
| `trades_unresolved` | 1 | Execution Feasibility | Trades marked unresolved due to unexecutable boundary exit |
| `rejected_existing_contract_position` | **9,956** | Execution Rejections | Rejections because contract already in active position |
| `rejected_insufficient_training_history`| 61 | Execution Rejections | Rejections because training samples < 20 in fold |
| `rejected_tender_window_at_entry` | 42 | Execution Rejections | Rejections because DTE <= 5 at entry |
| `rejected_fold_boundary_censored` | 152 | Execution Rejections | Planned entry falls on/after test window end |
| `exits_due_to_max_holding` | 185 | Exit Mechanics | Exits triggered by 10-day max holding period |
| `exits_due_to_tender_safety` | 47 | Exit Mechanics | Exits triggered by tender notice safety window (DTE <= 5) |
| `exits_due_to_fold_boundary` | 36 | Exit Mechanics | Exits triggered by test window boundary close |

**Verification of Account Balance**:
$$\text{Signals Triggered} = 10,479 = 268 \text{ (Filled)} + 9,956 \text{ (Existing Contract)} + 61 \text{ (History)} + 42 \text{ (Tender)} + 152 \text{ (Censored)}$$
$$268 \text{ (Filled)} = 267 \text{ (Completed)} + 1 \text{ (Unresolved)}$$
Exact 100% reconciliation across all categories.

---

## 5. Regression Test Results

Fourteen new regression tests were added to [tests/test_walk_forward_backtest.py](file:///d:/Akshitakumawat/hackkk/tests/test_walk_forward_backtest.py):

| Test ID | Test Name | Purpose | Result |
| :--- | :--- | :--- | :---: |
| `test_25` | `test_25_two_different_pairs_sharing_same_contract` | Synthetic test: Shared contract across 2 pairs rejected | **PASSED** |
| `test_26` | `test_26_multiple_strategies_sharing_same_contract` | Synthetic test: Multi-strategy sharing rejected | **PASSED** |
| `test_27` | `test_27_gross_exposure_limit_exceeded` | Synthetic test: Gross lot ceiling breach rejected | **PASSED** |
| `test_28` | `test_28_net_exposure_limit_exceeded` | Synthetic test: Net lot ceiling breach rejected | **PASSED** |
| `test_29` | `test_29_opposite_positions_and_gross_vs_net_exposure` | Synthetic test: Opposing positions rejected | **PASSED** |
| `test_30` | `test_30_exit_and_subsequent_reentry_release_timing` | Synthetic test: Contract released strictly on session $E+1$ | **PASSED** |
| `test_31` | `test_31_position_occupancy_across_all_trading_sessions` | Integration test: 0 overlapping sessions across all contracts | **PASSED** |
| `test_32` | `test_32_simultaneous_signals_deterministic_prioritization`| Synthetic test: Priority given to highest relative deviation | **PASSED** |
| `test_33` | `test_33_fold_boundary_exits_and_unresolved_positions` | Integration test: Unresolved boundary exit has NaN P&L | **PASSED** |
| `test_34` | `test_34_separate_cost_scenarios_not_counted_as_independent_live_exposure` | Integration test: 3 cost scenarios share identical trades | **PASSED** |
| `test_35` | `test_35_rejected_attempts_preserved_in_audit_ledger` | Integration test: All rejected attempts preserved with reasons | **PASSED** |
| `test_36` | `test_36_identical_inputs_produce_deterministic_outputs` | Synthetic test: 100% deterministic candidate selection | **PASSED** |
| `test_37` | `test_37_no_look_ahead_leakage_in_trade_selection` | Integration test: Trade selection uses date $t$ info only | **PASSED** |
| `test_38` | `test_38_correct_pnl_and_cost_reconciliation_after_changes` | Integration test: Gross P&L - Costs = Net P&L (100% reconciled) | **PASSED** |

### Complete Repository Test Suite Execution:
```bash
python -m unittest discover tests
----------------------------------------------------------------------
Ran 84 tests in 111.752s

OK
```
All 84 tests passed without failure or regression.

---

## 6. Upstream Dataset Integrity Verification (SHA-256)

All Phase 1–5 datasets were verified to ensure zero upstream mutation:

| File Path | Canonical SHA-256 Hash | Current Calculated Hash | Status |
| :--- | :---: | :---: | :---: |
| `data/processed/mcx_gold_master.csv` | `ac57299101fef7092ae956dc35fa9e9f15d9e8a195a340621ddd245f3f510088` | `ac57299101fef7092ae956dc35fa9e9f15d9e8a195a340621ddd245f3f510088` | **MATCH (100%)** |
| `data/processed/mcx_gold_normalized.csv` | `26c57ce9ad54f271875e816ce865ef0121adadbe517136289494a8bae48c2020` | `26c57ce9ad54f271875e816ce865ef0121adadbe517136289494a8bae48c2020` | **MATCH (100%)** |
| `data/processed/mcx_gold_relative_price_radar.csv` | `38f13aeddb2454f928ae5a043319b525c01d198283be0e050f292d8efa2386c4` | `38f13aeddb2454f928ae5a043319b525c01d198283be0e050f292d8efa2386c4` | **MATCH (100%)** |
| `data/processed/mcx_gold_term_structure.csv` | `d81102755b7f1b85766ea699a99dc1c6f998eaf50b034c2924d1bf133fac6201` | `d81102755b7f1b85766ea699a99dc1c6f998eaf50b034c2924d1bf133fac6201` | **MATCH (100%)** |
| `data/processed/mcx_gold_term_structure_snapshots.csv` | `f064bf4e75ff6791b1839f4b8152cabf51d99478ecf310b6696a0aefb3120037` | `f064bf4e75ff6791b1839f4b8152cabf51d99478ecf310b6696a0aefb3120037` | **MATCH (100%)** |
| `data/processed/mcx_gold_liquidity_filtered_candidates.csv` | `b2385ab75c9f0a2d6a65f6da580725b8979f6834e433042df5f9c51d4efac135` | `b2385ab75c9f0a2d6a65f6da580725b8979f6834e433042df5f9c51d4efac135` | **MATCH (100%)** |
| `data/processed/mcx_gold_transaction_cost_scenarios.csv` | `1f58b74593db05e5a521f289870ac0368a06f14963e0676ed20d90f4e5c9158a` | `1f58b74593db05e5a521f289870ac0368a06f14963e0676ed20d90f4e5c9158a` | **MATCH (100%)** |
| `data/processed/mcx_gold_eligible_candidates.csv` | `774b872b9aae45d06129c970f70f852e2efdb0f1ba6358381af19cb34b6fa22f` | `774b872b9aae45d06129c970f70f852e2efdb0f1ba6358381af19cb34b6fa22f` | **MATCH (100%)** |

All raw data and Phase 1–5 files remain byte-for-byte immutable.

---

## 7. Remaining Limitations

1. **Proxy Reference Prices**: Fills are executed at the next session's Open price. In actual MCX trading, simultaneous two-leg market or limit execution at Open is subject to execution lag and queue positioning.
2. **Realized-P&L vs MTM Equity**: Drawdowns are calculated from the cumulative realized P&L curve booked at trade exit dates. Daily unrealized mark-to-market equity fluctuations are unmodeled because daily intermediate settling prices are not tracked inside active holding periods.
3. **Capital Employed / Margin**: Bhavcopy files do not report initial and maintenance margin requirements. Consequently, Sharpe ratios, Sortino ratios, and percentage ROIs are not calculated to avoid fabricating unverified denominator assumptions.

---

## 8. Final Approval Status

| Sign-Off Criterion | Status | Evidence |
| :--- | :---: | :--- |
| Shared-Contract Overlap Audited & Eliminated | **PASSED** | 0 / 114 overlapping contracts; 0 opposing positions |
| Portfolio Exposure Limits Configured & Enforced | **PASSED** | `portfolio_exposure_limits` block in `backtest_config.json` |
| Chronological & Leakage-Free Allocation | **PASSED** | Priority by Date $t$ Close deviation; entries on Date $t+1$ Open |
| Reconciled P&L and Cost Math | **PASSED** | Gross P&L - Modeled Costs = Net P&L for 100% of trades |
| 14 New Regression Tests Passing | **PASSED** | Tests 25 to 38 in `test_walk_forward_backtest.py` pass |
| Full Repository Test Suite Passing | **PASSED** | 84 tests pass in 111.75s (`python -m unittest discover tests`) |
| Upstream Datasets Byte-Identical | **PASSED** | 8 Phase 1–5 SHA-256 hashes match canonical records |
| Scope Discipline Preserved | **PASSED** | Phase 7 and Phase 8 remain strictly unstarted |

**Recommendation:** **Phase 6 Walk-Forward Backtesting & Execution Feasibility Analysis is fully verified, robust, and APPROVED.**
