import os
import sqlite3

import pandas as pd
import streamlit as st

from src import config
def get_connection():
    from src import config
    db_abs_path = os.path.abspath(config.DB_PATH)
    return sqlite3.connect(db_abs_path)

@st.cache_data(ttl=600)
def get_companies():

    conn = get_connection()
    query = "SELECT * FROM companies"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):

    conn = get_connection()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []

    if ticker:
        query += " AND company_id = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):

    conn = get_connection()
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker):

    conn = get_connection()
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):

    conn = get_connection()
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():

    conn = get_connection()
    query = "SELECT * FROM sectors"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name):

    conn = get_connection()
    query = "SELECT * FROM peer_groups WHERE peer_group_name = ?"
    df = pd.read_sql_query(query, conn, params=[group_name])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker):

    conn = get_connection()
    query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_prosandcons(ticker):

    conn = get_connection()
    query = "SELECT * FROM prosandcons WHERE company_id = ?"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_market_caps(year=None):

    conn = get_connection()
    query = "SELECT * FROM market_cap WHERE 1=1"
    params = []
    if year:
        query += " AND year = ?"
        params.append(year)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_master_dataframe():
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_ratios().sort_values("year").groupby("company_id").tail(1)
    market_caps = get_market_caps().sort_values("year").groupby("company_id").tail(1)

    df = pd.merge(
        companies[["company_id", "company_name"]],
        sectors[["company_id", "broad_sector"]],
        on="company_id",
        how="left",
    )
    df = pd.merge(df, ratios, on="company_id", how="left")

    if "year" in market_caps.columns:
        market_caps = market_caps.drop(columns=["year"])
    df = pd.merge(df, market_caps, on="company_id", how="left")
    
    return df