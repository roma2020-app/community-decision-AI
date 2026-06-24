from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, schemas, csv_processor, crud, CommunityData, CommunityInsight

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"]
)

@router.post("/upload", response_model=schemas.UploadSummary, status_code=status.HTTP_201_CREATED)
async def upload_csv_dataset(
    file: UploadFile = File(...),
    reset: bool = True,
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file containing community metrics, validate columns and data types,
    filter duplicate records, and save new records to AlloyDB/PostgreSQL.
    Optionally resets existing data before upload.
    """
    # 1. Verify file extension
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files are supported."
        )

    # 2. Reset existing data if requested
    if reset:
        try:
            db.query(CommunityData).delete()
            db.query(CommunityInsight).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reset existing database records: {str(e)}"
            )

    # 3. Read file content
    try:
        content = await file.read()
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # 3. Process and validate CSV
    summary = csv_processor.validate_and_process_csv(
        db=db,
        file_content=content,
        filename=file.filename
    )

    # 4. Check if fatal processing errors occurred (like missing columns)
    # If there are parsing errors on rows, they are returned in summary.errors list.
    # But if the file is completely unparseable or missing columns, total_rows will be 0.
    if summary.total_rows == 0 and summary.errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV processing failed: {summary.errors[0]}"
        )

    return summary


@router.get("/records", response_model=List[schemas.CommunityData], status_code=status.HTTP_200_OK)
def get_all_records(db: Session = Depends(get_db)):
    """
    Fetch all community records stored in AlloyDB.
    """
    try:
        return crud.get_all_community_data(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch records: {str(e)}"
        )

