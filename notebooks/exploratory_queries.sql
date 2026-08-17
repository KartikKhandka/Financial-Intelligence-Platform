-- Exploratory Queries for Nifty 100 Financial Data
-- Sprint 1, Day 7

-- 1. Top 5 Companies by Market Cap in 2024
SELECT c.company_name, m.market_cap_crore
FROM companies c
JOIN market_cap m ON c.company_id = m.company_id
WHERE m.year = 2024
ORDER BY m.market_cap_crore DESC
LIMIT 5;

-- 2. Companies with the highest Return on Equity (ROE) based on Analysis
SELECT c.company_name, a.roe
FROM companies c
JOIN analysis a ON c.company_id = a.company_id
ORDER BY a.roe DESC
LIMIT 10;

-- 3. Average P/E Ratio by Broad Sector in 2024
SELECT s.broad_sector, AVG(m.pe_ratio) AS avg_pe_ratio
FROM sectors s
JOIN market_cap m ON s.company_id = m.company_id
WHERE m.year = 2024 AND m.pe_ratio IS NOT NULL
GROUP BY s.broad_sector
ORDER BY avg_pe_ratio DESC;

-- 4. Total Debt exposure by Sector in 2024
SELECT s.broad_sector, SUM(f.total_debt_cr) AS total_debt_crore
FROM sectors s
JOIN financial_ratios f ON s.company_id = f.company_id
WHERE f.year = 2024
GROUP BY s.broad_sector
ORDER BY total_debt_crore DESC;

-- 5. Top 5 Companies by Net Profit Margin in 2024
SELECT c.company_name, f.net_profit_margin_pct
FROM companies c
JOIN financial_ratios f ON c.company_id = f.company_id
WHERE f.year = 2024
ORDER BY f.net_profit_margin_pct DESC
LIMIT 5;

-- 6. Cash Flow from Operations vs. Net Profit in 2024 for Top 5 Market Cap Companies
SELECT c.company_name, f.cash_from_operations_cr, p.net_profit
FROM companies c
JOIN financial_ratios f ON c.company_id = f.company_id
JOIN profitandloss p ON c.company_id = p.company_id AND f.year = p.year
JOIN market_cap m ON c.company_id = m.company_id AND f.year = m.year
WHERE f.year = 2024
ORDER BY m.market_cap_crore DESC
LIMIT 5;

-- 7. Companies with the highest Dividend Yield in 2024
SELECT c.company_name, m.dividend_yield_pct
FROM companies c
JOIN market_cap m ON c.company_id = m.company_id
WHERE m.year = 2024 AND m.dividend_yield_pct IS NOT NULL
ORDER BY m.dividend_yield_pct DESC
LIMIT 5;

-- 8. Peer Group performance comparisons (Average Market Cap by Peer Group)
SELECT p.peer_group_name, AVG(m.market_cap_crore) AS avg_market_cap
FROM peer_groups p
JOIN market_cap m ON p.company_id = m.company_id
WHERE m.year = 2024
GROUP BY p.peer_group_name
ORDER BY avg_market_cap DESC;

-- 9. Stock Price Volatility: High vs Low difference in the last available date
SELECT c.company_name, s.date, (s.high_price - s.low_price) AS daily_range
FROM companies c
JOIN stock_prices s ON c.company_id = s.company_id
WHERE s.date = (SELECT MAX(date) FROM stock_prices)
ORDER BY daily_range DESC
LIMIT 5;

-- 10. Overview of Companies with less than 5 years of P&L data
SELECT company_id, COUNT(DISTINCT year) AS years_count
FROM profitandloss
GROUP BY company_id
HAVING years_count < 5
ORDER BY years_count ASC;
