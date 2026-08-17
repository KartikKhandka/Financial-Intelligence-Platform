import os
import pandas as pd
from src.etl.normaliser import normalize_ticker
from src.analytics.cagr import calculate_cagr
from src.analytics.ratios import calc_icr_label
from src.screener.engine import ScreenerEngine
from src.etl.loader import FILE_MANIFEST

def test_rule1_core_excel_headers():
    for filename, table_name, header_row, is_supplementary in FILE_MANIFEST:
        if not is_supplementary:
            assert header_row == 1, f"Core file {filename} must use header=1"

def test_rule2_normalize_company_id():
    assert normalize_ticker("  reliance ") == "RELIANCE"
    assert normalize_ticker("tcs.ns") == "TCS"
    assert normalize_ticker("infosys.bo") == "INFOSYS"
    assert normalize_ticker("  hdfc bank  ") == "HDFC BANK"

def test_rule4_screener_financials_de():
    engine_file = "src/screener/engine.py"
    if os.path.exists(engine_file):
        with open(engine_file, "r") as f:
            content = f.read()
        assert "df[\"broad_sector\"] == \"Financials\"" in content or "df['broad_sector'] == 'Financials'" in content, "Financials sector not skipped for D/E filter"

def test_rule5_cagr_turnaround():
    val, flag = calculate_cagr(-10, 50, 5)
    assert flag == "TURNAROUND"
    assert val is None

    val2, flag2 = calculate_cagr(-10, -5, 5)
    assert flag2 == "TURNAROUND"
    assert val2 is None

def test_rule6_interest_expense():
    assert calc_icr_label(None) == "Debt Free"

def test_rule7_simulated_labels():
    pages_to_check = ["src/dashboard/pages/06_sectors.py", "src/dashboard/pages/07_capital.py"]
    for page in pages_to_check:
        if os.path.exists(page):
            with open(page, "r") as f:
                content = f.read()
            if "market_cap" in content.lower():
                assert "SIMULATED" in content.upper(), f"SIMULATED label missing in {page}"