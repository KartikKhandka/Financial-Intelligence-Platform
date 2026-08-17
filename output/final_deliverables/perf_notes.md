# Performance Notes

## API Screener Load Test
- 10 concurrent requests completed in **2.19 seconds**.
- Maximum response time for a single thread: **2.18 seconds**.
- Target (all 10 complete within 10 seconds): **PASS**

## Dashboard Performance
- Streamlit and FastAPI started simultaneously without port conflicts (Ports 8501 and 8000).
- Company Profile screen data loads primarily depend on the `/companies/{ticker}` API endpoint.
- Database query execution is heavily optimized via SQLite indexing on `company_id` and `year`.
- Estimated load time per ticker profile is well under the 3-second threshold.
