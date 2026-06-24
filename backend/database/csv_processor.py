import csv
import io
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Set
from sqlalchemy.orm import Session
from .models import CommunityData
from .schemas import UploadSummary

def parse_datetime(date_str: str) -> datetime:
    """Attempt to parse datetime from various standard formats."""
    date_str = date_str.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y %H:%M"
    ):
        try:
            # Parse and make it timezone-naive for uniform DB comparison
            dt = datetime.strptime(date_str, fmt)
            return dt
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date string: {date_str}")

def validate_and_process_csv(db: Session, file_content: bytes, filename: str) -> UploadSummary:
    """
    Parses a CSV byte stream, validates columns, filters duplicates,
    and inserts valid records into AlloyDB.
    """
    # 1. Read the CSV stream
    try:
        csv_file = io.StringIO(file_content.decode("utf-8"))
        reader = csv.DictReader(csv_file)
    except Exception as e:
        return UploadSummary(
            filename=filename,
            total_rows=0,
            inserted_rows=0,
            ignored_duplicates=0,
            errors=[f"Failed to read file encoding: {str(e)}"]
        )

    if not reader.fieldnames:
        return UploadSummary(
            filename=filename,
            total_rows=0,
            inserted_rows=0,
            ignored_duplicates=0,
            errors=["CSV file is empty or missing headers."]
        )

    # Normalize headers to lowercase to tolerate variations
    headers = [h.strip().lower() for h in reader.fieldnames]
    required_cols = {"area", "complaints", "traffic", "aqi"}
    
    # Check if required columns are present
    missing_cols = required_cols - set(headers)
    if missing_cols:
        return UploadSummary(
            filename=filename,
            total_rows=0,
            inserted_rows=0,
            ignored_duplicates=0,
            errors=[f"Missing required columns: {', '.join(missing_cols)}"]
        )

    # Map headers to actual CSV headers (retaining original casing for dict keys)
    header_map = {h.strip().lower(): h for h in reader.fieldnames}
    area_col = header_map["area"]
    complaints_col = header_map["complaints"]
    traffic_col = header_map["traffic"]
    aqi_col = header_map["aqi"]
    timestamp_col = header_map.get("timestamp") # Optional

    total_rows = 0
    inserted_rows = 0
    ignored_duplicates = 0
    errors: List[str] = []

    # Fetch existing records from database to build an in-memory duplicate checking cache.
    # We define a duplicate as having the exact same area and timestamp (down to the second).
    try:
        existing_records = db.query(CommunityData.area, CommunityData.timestamp).all()
        # Create a lookup set of (area, timestamp_naive)
        # Normalize area to lowercase for case-insensitive duplicate check
        existing_cache: Set[Tuple[str, datetime]] = set()
        for area_val, ts_val in existing_records:
            if ts_val:
                # SQLAlchemy datetime objects are naive when fetched if saved without timezone
                existing_cache.add((area_val.strip().lower(), ts_val))
    except Exception as e:
        return UploadSummary(
            filename=filename,
            total_rows=0,
            inserted_rows=0,
            ignored_duplicates=0,
            errors=[f"Database connection error during duplicate checking: {str(e)}"]
        )

    records_to_insert: List[CommunityData] = []
    
    for row_idx, row in enumerate(reader, start=1):
        total_rows += 1
        
        # Extract area
        area = row.get(area_col, "").strip()
        if not area:
            errors.append(f"Row {row_idx}: Area is empty.")
            continue
            
        # Parse complaints
        try:
            complaints_str = row.get(complaints_col, "0").strip()
            complaints = int(complaints_str) if complaints_str else 0
            if complaints < 0:
                errors.append(f"Row {row_idx}: Complaints cannot be negative")
                continue
        except ValueError as e:
            errors.append(f"Row {row_idx}: Invalid complaints value '{row.get(complaints_col)}'. Must be non-negative integer.")
            continue

        # Parse traffic
        traffic = row.get(traffic_col, "").strip()
        is_numeric_traffic = False
        try:
            float(traffic)
            is_numeric_traffic = True
        except ValueError:
            pass

        if not is_numeric_traffic:
            val_lower = traffic.lower()
            if val_lower == "high":
                traffic = "High"
            elif val_lower == "medium":
                traffic = "Medium"
            else:
                traffic = "Low"

        # Parse AQI
        try:
            aqi_str = row.get(aqi_col, "0").strip()
            aqi = int(aqi_str) if aqi_str else 0
            if aqi < 0:
                raise ValueError("AQI cannot be negative")
        except ValueError as e:
            errors.append(f"Row {row_idx}: Invalid AQI value '{row.get(aqi_col)}'. Must be non-negative integer.")
            continue

        # Parse Timestamp
        try:
            if timestamp_col and row.get(timestamp_col):
                timestamp = parse_datetime(row.get(timestamp_col))
            else:
                timestamp = datetime.now() # Default to current local/naive time
            # Strip microseconds to match typical CSV precision
            timestamp = timestamp.replace(microsecond=0)
        except ValueError as e:
            errors.append(f"Row {row_idx}: {str(e)}")
            continue

        # Check for duplicates
        lookup_key = (area.lower(), timestamp)
        if lookup_key in existing_cache:
            ignored_duplicates += 1
            continue

        # Add to insertion transaction list and update cache to avoid duplicates within the same CSV upload
        db_record = CommunityData(
            area=area,
            complaints=complaints,
            traffic=traffic,
            aqi=aqi,
            timestamp=timestamp
        )
        records_to_insert.append(db_record)
        existing_cache.add(lookup_key)

    # Perform bulk insert if we have valid records
    if records_to_insert:
        try:
            db.bulk_save_objects(records_to_insert)
            db.commit()
            inserted_rows = len(records_to_insert)
        except Exception as e:
            db.rollback()
            errors.append(f"Failed to commit database transaction: {str(e)}")
            inserted_rows = 0

    return UploadSummary(
        filename=filename,
        total_rows=total_rows,
        inserted_rows=inserted_rows,
        ignored_duplicates=ignored_duplicates,
        errors=errors
    )
