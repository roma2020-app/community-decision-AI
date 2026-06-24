import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from .connection import Base
from . import crud

class TestDatabaseLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup in-memory SQLite for testing SQLAlchemy configurations
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        # Clean up database tables between tests
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

    def test_community_data_crud(self):
        # 1. Create
        record = crud.create_community_data(
            db=self.db,
            area="Downtown",
            complaints=12,
            traffic="High",
            aqi=45
        )
        self.assertIsNotNone(record.id)
        self.assertEqual(record.area, "Downtown")
        self.assertEqual(record.complaints, 12)
        self.assertEqual(record.traffic, "High")
        self.assertEqual(record.aqi, 45)

        # 2. Read by ID
        fetched = crud.get_community_data_by_id(self.db, record.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.area, "Downtown")

        # 3. Read by Area
        results = crud.get_community_data_by_area(self.db, "Downtown")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, record.id)

        # 4. Read all
        all_records = crud.get_all_community_data(self.db)
        self.assertEqual(len(all_records), 1)

        # 5. Update
        updated = crud.update_community_data(self.db, record.id, {"complaints": 15, "traffic": "Medium"})
        self.assertIsNotNone(updated)
        self.assertEqual(updated.complaints, 15)
        self.assertEqual(updated.traffic, "Medium")

        # 6. Delete
        success = crud.delete_community_data(self.db, record.id)
        self.assertTrue(success)
        self.assertIsNone(crud.get_community_data_by_id(self.db, record.id))

    def test_community_insights_crud(self):
        # 1. Create
        insight = crud.create_community_insight(
            db=self.db,
            area="West End",
            insight="High PM2.5 levels detected near school zone.",
            priority_score=8.5,
            recommendation="Redirect heavy duty truck traffic during school hours."
        )
        self.assertIsNotNone(insight.id)
        self.assertEqual(insight.area, "West End")
        self.assertEqual(insight.priority_score, 8.5)

        # 2. Read by ID
        fetched = crud.get_community_insight_by_id(self.db, insight.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.insight, "High PM2.5 levels detected near school zone.")

        # 3. Read by Area
        results = crud.get_insights_by_area(self.db, "West End")
        self.assertEqual(len(results), 1)

        # 4. Read all
        all_insights = crud.get_all_insights(self.db)
        self.assertEqual(len(all_insights), 1)

        # 5. Update
        updated = crud.update_community_insight(self.db, insight.id, {"priority_score": 9.2})
        self.assertIsNotNone(updated)
        self.assertEqual(updated.priority_score, 9.2)

        # 6. Delete
        success = crud.delete_community_insight(self.db, insight.id)
        self.assertTrue(success)
        self.assertIsNone(crud.get_community_insight_by_id(self.db, insight.id))

if __name__ == "__main__":
    unittest.main()
