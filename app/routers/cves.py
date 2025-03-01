# app/routers/cves.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import create_engine, Column, String, Numeric, DateTime, JSON, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, validator, Field

# --- Pydantic Models (Moved from main.py) ---
class CVSSv3Data(BaseModel):
    baseScore: Optional[float] = None

class CVSSv2Data(BaseModel):
    baseScore: Optional[float] = None

class CVSSMetricV3(BaseModel):
    cvssData: Optional[CVSSv3Data] = None

class CVSSMetricV2(BaseModel):
    cvssData: Optional[CVSSv2Data] = None
class DescriptionData(BaseModel):
    lang: str
    value: str

class CVEItem(BaseModel):
    id: str
    published: Optional[str] = None
    lastModified: Optional[str] = None
    descriptions: List[DescriptionData] = Field(default_factory=list)
    metrics: Dict = Field(default_factory=dict)


class Vulnerability(BaseModel):
    cve: CVEItem

class CVEResponse(BaseModel):
    resultsPerPage: int
    startIndex: int
    totalResults: int
    vulnerabilities: List[Vulnerability]

class CVEResponseSingle(BaseModel):
    vulnerabilities: List[Vulnerability]

class CVEDB(BaseModel):
    cve_id: str
    published: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    description: Optional[str] = None
    base_score_v3: Optional[float] = None
    base_score_v2: Optional[float] = None
    raw_data: Dict

    class Config:
        from_attributes = True

# --- Database Setup (SQLAlchemy) ---
load_dotenv()
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(database_url)
Base = declarative_base()

class CVE(Base):  # SQLAlchemy Model (matches your db_schemas.py)
    __tablename__ = "cves"
    cve_id = Column(String, primary_key=True)
    published = Column(DateTime)
    last_modified = Column(DateTime)
    description = Column(String)
    base_score_v3 = Column(Numeric)
    base_score_v2 = Column(Numeric)
    raw_data = Column(JSON)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Dependency for Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- APIRouter ---
router = APIRouter()

@router.get("/cves/", response_model=List[CVEDB])
async def get_cves(
    cve_id: Optional[str] = Query(None, description="Filter by CVE ID"),
    year: Optional[int] = Query(None, description="Filter by CVE year"),
    base_score_v3: Optional[float] = Query(None, description="Filter by CVSS v3 base score"),
    last_modified_days: Optional[int] = Query(None, description="Filter by last modified in N days"),
    db: Session = Depends(get_db)  # Use Depends for the database session
):
    query = db.query(CVE)

    if cve_id:
        query = query.filter(CVE.cve_id == cve_id)
    if year:
        query = query.filter(text("EXTRACT(YEAR FROM published) = :year").bindparams(year=year)) # Use text for year extraction
    if base_score_v3:
        query = query.filter(CVE.base_score_v3 >= base_score_v3) # Filter greater or equal
    if last_modified_days:
        date_threshold = datetime.utcnow() - timedelta(days=last_modified_days)
        query = query.filter(CVE.last_modified >= date_threshold)

    cves = query.all()
    return [CVEDB.model_validate(cve) for cve in cves]  # Convert to Pydantic models

@router.get("/cves/{cve_id}", response_model=CVEDB)
async def get_cve(cve_id: str, db: Session = Depends(get_db)):
    cve = db.query(CVE).filter(CVE.cve_id == cve_id).first()
    if cve is None:
        raise HTTPException(status_code=404, detail="CVE not found")
    return CVEDB.model_validate(cve)