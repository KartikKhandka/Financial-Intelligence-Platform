from pydantic import BaseModel

class CompanyListResponse(BaseModel):
    company_id: str
    company_name: str
    broad_sector: str | None = None
    sub_sector: str | None = None
    roe_pct: float | None = None
    roce_pct: float | None = None

class CompanyProfileResponse(BaseModel):
    company_id: str
    company_name: str
    company_logo: str | None = None
    about_company: str | None = None
    website: str | None = None
    nse_profile: str | None = None
    bse_profile: str | None = None
    face_value: float | None = None
    book_value: float | None = None
    roce_percentage: float | None = None
    roe_percentage: float | None = None
    broad_sector: str | None = None
    sub_sector: str | None = None
    market_cap_category: str | None = None

    latest_pe: float | None = None
    latest_pb: float | None = None
    latest_market_cap: float | None = None