import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src import config
import os

import pandas as pd
from src.reports.portfolio_summary import generate_portfolio_summary
from src.reports.sector_report import generate_sector_reports
from src.reports.tearsheet import generate_tearsheet
from src.reports.radar_charts import generate_all_radar_charts

def main():

    pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
    companies = pl["company_id"].unique()

    skipped = []
    generated = 0

    tearsheet_dir = config.REPORTS_DIR / "tearsheets"
    tearsheet_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting batch tearsheet generation for {len(companies)} companies...")
    for cid in companies:
        comp_pl = pl[pl["company_id"] == cid]
        if len(comp_pl) < 3:
            skipped.append({"company_id": cid, "years_data": len(comp_pl)})
            continue

        success = generate_tearsheet(cid)
        if success:
            generated += 1
        else:
            skipped.append({"company_id": cid, "years_data": len(comp_pl)})

    if skipped:
        skipped_path = config.OUTPUT_DIR / "skipped_tearsheets.csv"
        pd.DataFrame(skipped).to_csv(skipped_path, index=False)
        print(
            f"Skipped {len(skipped)} companies, saved to {skipped_path}"
        )

    print(f"Successfully generated {generated} tearsheets.")

    print("Generating sector reports...")
    generate_sector_reports()

    print("Generating portfolio summary...")
    generate_portfolio_summary()

    print("Generating radar charts...")
    generate_all_radar_charts()

    files = os.listdir(config.REPORTS_DIR / "tearsheets")
    pdf_count = len([f for f in files if f.endswith(".pdf")])
    print(
        f"Verification: Found {pdf_count} PDFs in {config.REPORTS_DIR}/tearsheets (Expected: {len(companies) - len(skipped)})"
    )

if __name__ == "__main__":
    main()