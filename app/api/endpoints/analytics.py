"""
Analytics and Dashboard API endpoints.
Provides weekly glucose data for patient dashboards.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db import get_db
from app.models import GlucoseReading

# Router for analytics endpoints
api_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@api_router.get("/glucose/weekly")
async def get_weekly_glucose(
    user_id: str = Query(..., description="Firebase user ID to get glucose data for"),
    days: int = Query(7, ge=1, le=30, description="Number of days to retrieve (default: 7, max: 30)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get weekly glucose data for a patient dashboard.
    
    Returns day-wise glucose values suitable for Flutter bar charts.
    
    **Response Format:**
    ```json
    {
        "user_id": "firebase_uid",
        "period_days": 7,
        "start_date": "2025-01-01",
        "end_date": "2025-01-07",
        "daily_data": [
            {
                "date": "2025-01-01",
                "day_name": "Monday",
                "average_value": 5.2,
                "unit": "mmol/L",
                "reading_count": 3,
                "readings": [
                    {"value": 5.2, "unit": "mmol/L", "taken_at": "2025-01-01T08:00:00"}
                ]
            },
            ...
        ]
    }
    ```
    
    **Usage:**
    - Default (last 7 days): `GET /api/analytics/glucose/weekly?user_id=YOUR_UID`
    - Custom period: `GET /api/analytics/glucose/weekly?user_id=YOUR_UID&days=14`
    """
    try:
        # Calculate date range (last N days from today)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query glucose readings for this user within the date range
        stmt = select(GlucoseReading).where(
            and_(
                GlucoseReading.user_id == user_id,
                GlucoseReading.taken_at >= start_date,
                GlucoseReading.taken_at <= end_date
            )
        ).order_by(GlucoseReading.taken_at.asc())
        
        result = await db.execute(stmt)
        readings = result.scalars().all()
        
        if not readings:
            # Return empty structure if no data
            return {
                "user_id": user_id,
                "period_days": days,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "daily_data": [],
                "message": "No glucose readings found for this period"
            }
        
        # Group readings by day
        daily_groups = {}
        unit = readings[0].unit  # Assume all readings use the same unit
        
        for reading in readings:
            # Get date (YYYY-MM-DD) as key
            date_key = reading.taken_at.date().isoformat()
            
            if date_key not in daily_groups:
                daily_groups[date_key] = []
            
            daily_groups[date_key].append({
                "value": reading.value,
                "unit": reading.unit,
                "taken_at": reading.taken_at.isoformat()
            })
        
        # Build daily data with averages
        daily_data = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Sort by date
        sorted_dates = sorted(daily_groups.keys())
        
        for date_str in sorted_dates:
            readings_for_day = daily_groups[date_str]
            values = [r["value"] for r in readings_for_day]
            average_value = sum(values) / len(values) if values else 0.0
            
            # Get day name
            date_obj = datetime.fromisoformat(date_str).date()
            day_name = day_names[date_obj.weekday()]
            
            daily_data.append({
                "date": date_str,
                "day_name": day_name,
                "average_value": round(average_value, 2),  # Round to 2 decimal places
                "unit": unit,
                "reading_count": len(readings_for_day),
                "readings": readings_for_day
            })
        
        return {
            "user_id": user_id,
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "daily_data": daily_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving glucose data: {str(e)}"
        )


@api_router.get("/glucose/summary")
async def get_glucose_summary(
    user_id: str = Query(..., description="Firebase user ID"),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for glucose readings.
    
    Returns overall stats like average, min, max, total readings.
    
    **Response Format:**
    ```json
    {
        "user_id": "firebase_uid",
        "period_days": 7,
        "total_readings": 15,
        "average_value": 5.3,
        "min_value": 4.8,
        "max_value": 6.1,
        "unit": "mmol/L"
    }
    ```
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query all readings for this period
        stmt = select(GlucoseReading).where(
            and_(
                GlucoseReading.user_id == user_id,
                GlucoseReading.taken_at >= start_date,
                GlucoseReading.taken_at <= end_date
            )
        )
        
        result = await db.execute(stmt)
        readings = result.scalars().all()
        
        if not readings:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_readings": 0,
                "message": "No glucose readings found for this period"
            }
        
        values = [r.value for r in readings]
        unit = readings[0].unit
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_readings": len(readings),
            "average_value": round(sum(values) / len(values), 2),
            "min_value": round(min(values), 2),
            "max_value": round(max(values), 2),
            "unit": unit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving glucose summary: {str(e)}"
        )

