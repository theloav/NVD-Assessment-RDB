# app/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

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

    @validator('published', 'lastModified', pre=True, allow_reuse=True)
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        return value

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