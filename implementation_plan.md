# Implementation Plan: Decision Recommendation Engine Integration

This plan outlines the enhancements to calculate, rank, and display community risk scores, recommended actions, and resource allocation suggestions. It fixes current unit and integration test issues and integrates recommendations into the main dashboard page.

## User Review Required

> [!IMPORTANT]
> **Risk Score Formula & Traffic Input**:
> 1. The formula is: `Risk Score = 0.4 * complaints + 0.3 * traffic + 0.3 * AQI`.
> 2. We will support both categorical `traffic` ("Low", "Medium", "High") mapped to `(10, 50, 100)` and raw numerical `traffic` values (e.g., `0.0` to `100.0` or custom floats) parsed directly from the uploaded CSV.
> 3. The `csv_processor.py` validator will be updated to accept numeric inputs for the `traffic` column, ensuring they aren't incorrectly mapped to the default `"Low"`.

> [!NOTE]
> **Main Dashboard Integration**:
> We will enhance the primary `1_Dashboard.py` page to directly display the Decision Recommendation Engine results, including the priority ranking Plotly charts and the AI-generated recommended actions and resource allocation suggestions.

---

## Proposed Changes

### Backend Ingestion & Processing

#### [MODIFY] [csv_processor.py](file:///c:/Users/romag/AG/Problem1/community-decision-intelligence/backend/database/csv_processor.py)
- Update the parser to validate the `traffic` column as either numeric (float/int) or categorical (`"Low"`, `"Medium"`, `"High"` case-insensitively).
- If it is numeric, we store it as the parsed float string (e.g., `"75.0"`). If categorical, we store the standard capitalized category name.

#### [MODIFY] [recommendations.py](file:///c:/Users/romag/AG/Problem1/community-decision-intelligence/backend/app/routers/recommendations.py)
- Update `calculate_traffic_score` to check if the string contains a float/int value.
- If it is numeric, return the float value directly. Otherwise, fall back to the `Low = 10.0`, `Medium = 50.0`, `High = 100.0` mapping.

### Frontend Dashboard Updates

#### [MODIFY] [1_Dashboard.py](file:///c:/Users/romag/AG/Problem1/community-decision-intelligence/frontend/pages/1_Dashboard.py)
- Fetch recommendations from the `/recommendations` API endpoint.
- Re-calculate the "Critical Area Hotspot" metric using the official `Risk Score` formula.
- Add a new visual section: **"🛡️ Decision recommendations & Priority Ranking"**.
- Add a Plotly horizontal bar chart of the official **Vulnerability Risk Scores** for priority ranking.
- Add an interactive expandable list showing each ward's **Recommended Actions** and **Resource Allocation Suggestions** side-by-side.

### Testing & Verification Fixes

#### [MODIFY] [test_upload_integration.py](file:///c:/Users/romag/AG/Problem1/community-decision-intelligence/backend/test_upload_integration.py)
- Use `StaticPool` from `sqlalchemy.pool` to ensure the SQLite in-memory database persists tables across FastAPI's async thread pools during test execution.
- Import `database.models` explicitly before running migrations to ensure tables are registered.

#### [MODIFY] [test_db.py](file:///c:/Users/romag/AG/Problem1/community-decision-intelligence/backend/database/test_db.py)
- Update to use `StaticPool` for robust local test execution.

---

## Verification Plan

### Automated Tests
- Run database layer tests:
  ```powershell
  python -m unittest backend/database/test_db.py
  ```
- Run upload integration tests:
  ```powershell
  $env:PYTHONPATH="backend"
  python -m unittest backend/test_upload_integration.py
  ```

### Manual Verification
- Ingest a test CSV with mixed traffic values (e.g. some numeric `85`, some categorical `High`).
- Navigate to the Streamlit **Dashboard** (`1_Dashboard.py`) and verify that:
  1. The "Critical Area Hotspot" KPI matches the highest calculated risk score.
  2. The horizontal priority chart matches the computed risk ranking.
  3. Action plans and resource allocations are displayed clearly for each neighborhood.
- Verify that the **AI Recommendations** page (`4_AI_Recommendations.py`) displays matching risk scores.
