# Test fixtures — genuine official API responses captured 2026-11-09T11:24Z

- `eurostat_namq_10_gdp_DE_last6.json`: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?freq=Q&unit=CLV20_MNAC&s_adj=SCA&na_item=B1GQ&geo=DE&lastTimePeriod=6&lang=EN (3426 bytes)
- `eurostat_prc_hicp_minr_FR_last4.json`: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?freq=M&unit=RCH_A&coicop18=TOTAL&geo=FR&lastTimePeriod=4&lang=EN (4617 bytes)
- `ecb_FM_DFR_last4.csv`: https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV?format=csvdata&detail=full&lastNObservations=4 (1636 bytes)
- `fred_GDPC1_2024.csv`: https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2024-01-01 (254 bytes)

Sources: Eurostat (reuse with acknowledgement), European Central Bank Data Portal,
FRED, Federal Reserve Bank of St. Louis (GDPC1: U.S. Bureau of Economic Analysis).
Used only by unit tests; the app never displays fixture data.
