import io
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import FastAPI app, base models, database dependency override hook
from app.main import app
from database import Base, get_db

class TestCSVUploadIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure local database for test isolation
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Override FastAPI dependency
        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        # Refresh tables
        self.db = self.SessionLocal()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_upload_invalid_file_extension(self):
        # Try uploading a .txt file instead of .csv
        files = {"file": ("test.txt", b"area,complaints,traffic,aqi\nDowntown,10,Low,45", "text/plain")}
        response = self.client.post("/api/v1/datasets/upload", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only CSV files are supported", response.json()["detail"])

    def test_upload_missing_columns(self):
        # Missing 'aqi' column
        csv_data = "area,complaints,traffic\nDowntown,10,Low\n"
        files = {"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")}
        response = self.client.post("/api/v1/datasets/upload", files=files)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Missing required columns", response.json()["detail"])

    def test_upload_successful_with_duplicates_and_errors(self):
        # Contains:
        # Row 1: Valid row
        # Row 2: Duplicate of Row 1 (same area and timestamp)
        # Row 3: Invalid row (negative complaints)
        # Row 4: Valid row (new area)
        csv_data = (
            "area,complaints,traffic,aqi,timestamp\n"
            "Downtown,10,Low,45,2026-06-23 12:00:00\n"
            "Downtown,10,Low,45,2026-06-23 12:00:00\n"
            "Northside,-5,Medium,80,2026-06-23 12:00:00\n"
            "West End,2,High,110,2026-06-23 13:00:00\n"
        )
        files = {"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")}
        response = self.client.post("/api/v1/datasets/upload", files=files)
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        self.assertEqual(data["filename"], "test.csv")
        self.assertEqual(data["total_rows"], 4)
        self.assertEqual(data["inserted_rows"], 2) # Row 1 and Row 4
        self.assertEqual(data["ignored_duplicates"], 1) # Row 2
        self.assertEqual(len(data["errors"]), 1) # Row 3
        self.assertIn("Complaints cannot be negative", data["errors"][0])

        # Verify database inserts
        from database.models import CommunityData
        records = self.db.query(CommunityData).all()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].area, "Downtown")
        self.assertEqual(records[1].area, "West End")

    def test_recommendations_endpoint(self):
        # 1. Upload a CSV dataset containing numeric and categorical traffic
        csv_data = (
            "area,complaints,traffic,aqi\n"
            "Ward A,10,High,50\n"
            "Ward B,5,60.0,40\n"
        )
        files = {"file": ("test_recs.csv", csv_data.encode("utf-8"), "text/csv")}
        upload_resp = self.client.post("/api/v1/datasets/upload", files=files)
        self.assertEqual(upload_resp.status_code, 201)

        # 2. Query the recommendations endpoint
        response = self.client.get("/api/v1/recommendations")
        self.assertEqual(response.status_code, 200)
        
        recs = response.json()
        self.assertEqual(len(recs), 2)
        
        # Ward A calculation: 0.4 * 10 (complaints) + 0.3 * 100 (traffic: High) + 0.3 * 50 (aqi) = 4 + 30 + 15 = 49.0
        # Ward B calculation: 0.4 * 5 (complaints) + 0.3 * 60 (traffic: 60) + 0.3 * 40 (aqi) = 2 + 18 + 12 = 32.0
        # Ward A (49.0) should be ranked higher than Ward B (32.0).
        self.assertEqual(recs[0]["area"], "Ward A")
        self.assertEqual(recs[0]["risk_score"], 49.0)
        self.assertEqual(recs[0]["rank"], 1)
        self.assertEqual(recs[0]["traffic"], "High")
        
        self.assertEqual(recs[1]["area"], "Ward B")
        self.assertEqual(recs[1]["risk_score"], 32.0)
        self.assertEqual(recs[1]["rank"], 2)
        self.assertEqual(recs[1]["traffic"], "60.0")

if __name__ == "__main__":
    unittest.main()
