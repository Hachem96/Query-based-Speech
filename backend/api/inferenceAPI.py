"""
Inference API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from backend.InferenceQuery import inference_query  # Import your inference function

router = APIRouter()

class InferenceRequest(BaseModel):
    videoName: str
    query: str

class InferenceResponse(BaseModel):
    success: bool
    videoName: str
    query: str
    result: Dict[str, Any]

@router.post("/", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """
    Run inference on a video with a query
    
    Args:
        videoId: ID of the video to run inference on
        query: Query string for inference
        
    Returns:
        Dictionary containing inference results
    """
    
    try:
        # Call your existing inference function
        result = inference_query(
            request.query,
            request.videoName
        )
        print("Inference result:", result)
        return InferenceResponse(
            success=True,
            videoName=request.videoName,
            query=request.query,
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running inference: {str(e)}"
        )