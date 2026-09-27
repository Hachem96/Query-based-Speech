"""
Inference API endpoints
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.InferenceQuery import (
    inference_query,
    search_all_videos,
    VideoNotFoundError,
)
from backend.api.limiter import limiter


logger = logging.getLogger(__name__)
router = APIRouter()


class InferenceRequest(BaseModel):
    videoName: str = Field(..., min_length=1, max_length=200)
    query: str = Field(..., min_length=1, max_length=500)


class InferenceResponse(BaseModel):
    success: bool
    videoName: str
    query: str
    result: Dict[str, Any]


class VideoSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class VideoSearchResponse(BaseModel):
    success: bool
    query: str
    videoIds: List[int]


@router.post("/", response_model=InferenceResponse)
@limiter.limit("10/minute")
async def run_inference(request: Request, body: InferenceRequest):
    """
    Run inference on a video with a query.

    Args:
        videoName: name of the video to run inference on
        query: query string for inference

    Returns:
        Dictionary containing inference results.
    """

    try:
        result = inference_query(
            body.query,
            body.videoName
        )

        return InferenceResponse(
            success=True,
            videoName=body.videoName,
            query=body.query,
            result=result,
        )

    except VideoNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    except Exception:
        logger.exception(
            "Inference failed for videoName=%r",
            body.videoName
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error running inference",
        )


@router.post(
    "/search",
    response_model=VideoSearchResponse
)
@limiter.limit("10/minute")
async def search_videos(
    request: Request,
    body: VideoSearchRequest
):
    """
    Search all videos using semantic similarity.

    Args:
        query: text query

    Returns:
        IDs of the top-k most similar videos.
    """

    try:
        video_ids = search_all_videos(body.query)

        return VideoSearchResponse(
            success=True,
            query=body.query,
            videoIds=video_ids,
        )

    except Exception:
        logger.exception(
            "Video search failed for query=%r",
            body.query
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching videos",
        )