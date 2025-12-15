"""
Glucose analysis endpoints (image upload to extract meter readings).
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
import mimetypes
from app.services.gemini_service import GeminiService


api_router = APIRouter(prefix="/api/ai", tags=["ai"])

_gemini_service_instance = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    return _gemini_service_instance


@api_router.post("/analyze-glucose")
async def ai_analyze_glucose(image: UploadFile = File(...)):
    """
    Analyze a glucose meter image and return the parsed reading with brief analysis.
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
        result = gemini_service.analyze_glucose_image(
            image_data=data,
            mime_type=content_type
        )

        return {
            "success": True,
            "reading": {"value": result["value"], "unit": result["unit"]},
            "analysis": result.get("analysis"),
            "raw_response": result.get("raw_response")
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

