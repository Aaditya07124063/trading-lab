# Cross-validation evidence

Extracts (4 instruments only) of NSE equity bhavcopies, downloaded 2026-09-30 from
`https://nsearchives.nseindia.com/content/historical/EQUITIES/<YYYY>/<MON>/cm<DDMONYYYY>bhav.csv.zip`
(public NSE archive, no login). Used only to verify vendor (Yahoo) anomalies.
`cm28JUL2005bhav.csv.zip` returned HTTP 404 on 2026-09-30 while 27JUL and 29JUL returned 200.
NSE prices are raw (unadjusted); Yahoo daily prices are split/bonus-adjusted.
