# Bluestock Financial Intelligence Platform

A comprehensive, enterprise-grade financial analytics and visualization platform built to analyze Nifty 100 constituents. This platform provides deep insights into capital allocation, peer benchmarking, financial trends, and automated report generation through an interactive, sleek dashboard.

## 🚀 Key Features

*   **Advanced Stock Screener:** Filter companies across 10+ fundamental metrics (ROE, D/E, FCF, CAGR, etc.) with pre-built screens (Quality, Value, Growth, Dividend, Turnaround).
*   **Capital Allocation Mapping:** Dynamic bubble charts plotting Return on Capital Employed (ROCE) against Free Cash Flow, visually categorized by allocation patterns (Cash Cows, Debt Burdened, High Growth, etc.).
*   **Peer Group Benchmarking:** Compare financial health, valuation ratios, and margins against industry peers and benchmarks in real-time.
*   **Interactive Visualizations:** Sleek, dark-themed Plotly charts with custom color palettes and responsive layouts.
*   **Automated PDF Reporting:** Generate comprehensive tearsheets, portfolio summaries, radar charts, and sector reports automatically.
*   **FastAPI Backend:** A robust backend API for programmatic access to financial data, valuation metrics, and peer group information.

## 🛠️ Tech Stack & Skills

This platform is built using modern data engineering and web development tools:

*   **Frontend & Dashboard:** Streamlit
*   **Data Visualization:** Plotly Express & Plotly Graph Objects
*   **Data Manipulation & Analysis:** Pandas, NumPy
*   **Database:** SQLite (Relational Data Storage)
*   **Backend API:** FastAPI
*   **Automated Reporting:** FPDF/ReportLab (PDF Generation)
*   **Styling:** Custom CSS injected into Streamlit for a premium, dark-mode aesthetic (glassmorphism, custom typography).

## 📁 Project Structure

*   `src/dashboard/`: Streamlit application pages and UI utilities (Screener, Capital Allocation, Peers, etc.).
*   `src/api/`: FastAPI backend implementation and routing.
*   `src/analytics/`: Core mathematical and financial logic (Clustering, CAGR calculations, composite scoring).
*   `src/reports/`: PDF generation scripts and batch processing tools.
*   `src/etl/`: Extract, Transform, Load pipelines (Normalizers, Validators) for ingesting financial data.

## ⚙️ Setup & Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit Dashboard:
   ```bash
   python -m streamlit run src/dashboard/app.py
   ```
4. (Optional) Run the FastAPI backend:
   ```bash
   uvicorn src.api.main:app --reload
   ```

## 🎨 Design Philosophy

The platform prioritizes a highly professional, "Bloomberg-terminal" aesthetic. It features a curated, dark-themed color palette, native typography (Inter/Outfit), and bespoke CSS overrides to eliminate clutter, creating a seamless and powerful user experience.
