# Cost-schedule sources (retrieved 2026-09-30)

NSE equity **intraday** (MIS), per executed order. Fractions of turnover.

| Component | Rate | Side | Sources |
|---|---|---|---|
| STT | 0.025% | sell | zerodha.com/charges; upstox.com/brokerage-charges (both quote "0.025% on the sell side") |
| NSE transaction charge + IPFT | Rs 307/crore = 0.00307% | each side | NSE circular NSE/FA/73061 (27 Feb 2026, effective 1 Mar 2026): 306.99 + 0.01 IPFT; previously 297 + 10 IPFT (same total). PDF in this folder. Zerodha shows 0.00307%; Upstox shows 0.00297% (+IPFT separately) |
| SEBI turnover fee | Rs 10/crore = 0.0001% | each side | both brokers |
| Stamp duty | 0.003% (Rs 300/crore) | buy | both brokers |
| GST | 18% on brokerage + exchange + SEBI | - | Zerodha ("brokerage + SEBI charges + transaction charges"); Upstox base lists brokerage + transaction + IPFT |
| Brokerage (Zerodha) | min(Rs 20, 0.03%) | per order | zerodha.com/charges |
| Brokerage (Upstox) | min(Rs 20, 0.1%) | per order | upstox.com/brokerage-charges |

Notes
- These are the CURRENT (2026-09-30) schedules applied to the whole sample. Historical
  NSE charges before 1 Oct 2024 were slab-based (NSE/FA/64232, 27 Sep 2024); differences
  are of order 0.0001-0.0003% per side and are dominated by the slippage grid.
- No broker account, login or API was used.
