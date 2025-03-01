# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import your FastAPI app
from unittest.mock import patch, MagicMock
from app.routers.cves import get_db, CVE  # Import get_db and the SQLAlchemy model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.models import CVEDB
# --- In-Memory SQLite Database for Testing ---

# Use an in-memory SQLite database for testing. This is fast and isolated.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}  # Required for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create a test version of the CVE model.  This is important to avoid
# potential conflicts with the main application's models, especially
# if you later add more complex relationships or constraints.
class TestCVE(Base):
    __tablename__ = "cves"  # Use the same table name
    cve_id = Column(String, primary_key=True)
    published = Column(DateTime)
    last_modified = Column(DateTime)
    description = Column(String)
    base_score_v3 = Column(Numeric)
    base_score_v2 = Column(Numeric)
    raw_data = Column(JSON)

# Override the database dependency for testing.
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture to set up the test client and database
@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine) # Create tables
    app.dependency_overrides[get_db] = override_get_db  # Override the dependency
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine) # Drop tables after tests


# --- Test Cases ---

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "CVE Data API"}

def test_get_cves_empty(client):
    # No data in the test database initially, so it should return an empty list.
    response = client.get("/cves/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_cves_with_data(client):
    # Add some test data *directly to the test database* using SQLAlchemy.
    db = TestingSessionLocal()  # Get a session
    test_cve = TestCVE(
        cve_id="CVE-2023-9999",
        published=datetime(2023, 1, 15, 12, 0, 0),
        last_modified=datetime(2023, 1, 20, 18, 30, 0),
        description="A test vulnerability.",
        base_score_v3=7.5,
        base_score_v2=6.8,
        raw_data={}
    )
    db.add(test_cve)
    db.commit()
    db.close() # Close session after adding

    response = client.get("/cves/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cve_id"] == "CVE-2023-9999"
    assert data[0]["description"] == "A test vulnerability."
    assert data[0]["base_score_v3"] == 7.5
    assert data[0]["base_score_v2"] == 6.8
    # You can add more assertions to check other fields

def test_get_cve_by_id(client):
    # Add test data (similar to above)
    db = TestingSessionLocal()
    test_cve = TestCVE(
        cve_id="CVE-2024-1111",
        published=datetime(2024, 2, 1),
        last_modified=datetime(2024, 2, 10),
        description="Another test CVE.",
        base_score_v3=9.1,
        base_score_v2=None,  # Test a None value
        raw_data={}
    )
    db.add(test_cve)
    db.commit()
    db.close()

    response = client.get("/cves/CVE-2024-1111")
    assert response.status_code == 200
    data = response.json()
    assert data["cve_id"] == "CVE-2024-1111"
    assert data["base_score_v3"] == 9.1
    assert data["base_score_v2"] is None  # Check for None

def test_get_cve_not_found(client):
    response = client.get("/cves/CVE-DOES-NOT-EXIST")
    assert response.status_code == 404
    assert response.json() == {"detail": "CVE not found"}

def test_get_cves_filter_by_year(client):
    db = TestingSessionLocal()
    db.add(TestCVE(cve_id="CVE-2023-1", published=datetime(2023, 1, 1), description="Test 2023"))
    db.add(TestCVE(cve_id="CVE-2022-1", published=datetime(2022, 1, 1), description="Test 2022"))
    db.commit()
    db.close()

    response = client.get("/cves/?year=2023")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cve_id"] == "CVE-2023-1"

def test_get_cves_filter_by_score(client):
    db = TestingSessionLocal()
    db.add(TestCVE(cve_id="CVE-HIGH", base_score_v3=8.0))
    db.add(TestCVE(cve_id="CVE-LOW", base_score_v3=3.0))
    db.commit()
    db.close()

    response = client.get("/cves/?base_score_v3=5.0")  # Get CVEs with score >= 5.0
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cve_id"] == "CVE-HIGH"

def test_get_cves_filter_last_modified(client):
    db = TestingSessionLocal()
    db.add(TestCVE(cve_id="CVE-RECENT", last_modified=datetime.utcnow() - timedelta(days=5)))
    db.add(TestCVE(cve_id="CVE-OLD", last_modified=datetime.utcnow() - timedelta(days=30)))
    db.commit()
    db.close()

    response = client.get("/cves/?last_modified_days=10") #Last modified with in 10 days
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cve_id"] == "CVE-RECENT"