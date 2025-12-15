"""
Food analysis endpoints (image upload to analyze meals for diabetes patients).
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
import mimetypes
from typing import Optional
from app.services.gemini_service import GeminiService


api_router = APIRouter(prefix="/api/ai", tags=["ai"])

_gemini_service_instance = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    return _gemini_service_instance


@api_router.post("/analyze-food")
async def ai_analyze_food(
    image: UploadFile = File(...),
    health_context: Optional[str] = Query(None, description="Optional health context (e.g., latest glucose reading)")
):
    """
    Analyze a food image and return meal name, estimated calories, and diabetes-friendly recommendation.
    
    Optional query parameter:
    - health_context: Provide health context like "Latest glucose: 125 mg/dL" for personalized advice
    """
    try:
        # Allow missing/unknown content types by inferring from filename; still require an image/* guess
        content_type = image.content_type
        if not content_type or content_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(image.filename or "")
            content_type = guessed or "image/jpeg"
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        data = await image.read()
        if not data:
            raise HTTPException(status_code=400, detail="Image file is empty")

        gemini_service = get_gemini_service()
        result = gemini_service.analyze_food_image(
            image_data=data,
            mime_type=content_type,
            health_context=health_context
        )

        return {
            "success": True,
            "meal": {
                "meal_name": result.get("meal_name"),
                "calories": result.get("calories")
            },
            "recommendation": result.get("recommendation"),
            "raw_response": result.get("raw_response")
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Food analysis failed: {str(e)}")


@api_router.post("/analyze-image")
async def ai_analyze_image(
    image: UploadFile = File(...),
    health_context: Optional[str] = Query(None, description="Optional health context for food analysis")
):
    """
    Smart image analysis:
    - If the image is a glucose meter, returns glucose reading and analysis.
    - If the image is food, returns meal info, calories, and diabetes-friendly recommendation.
    """
    try:
        # Allow missing/unknown content types by inferring from filename; still require an image/* guess
        content_type = image.content_type
        if not content_type or content_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(image.filename or "")
            content_type = guessed or "image/jpeg"
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        data = await image.read()
        if not data:
            raise HTTPException(status_code=400, detail="Image file is empty")

        gemini_service = get_gemini_service()
        result = gemini_service.analyze_image_auto(
            image_data=data,
            mime_type=content_type,
            health_context=health_context
        )

        return {
            "success": True,
            **result
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

