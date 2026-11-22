"""Pydantic schemas for visual learning, object detection, and scene context."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DetectedObject(BaseModel):
    """Structured information for an individual detected object."""
    id: int = Field(..., description="Unique integer ID within the image")
    label: str = Field(..., description="English vocabulary name")
    vietnamese: Optional[str] = Field(None, description="Vietnamese translation")
    confidence: float = Field(..., description="Detection confidence score between 0 and 1")
    confidence_percent: int = Field(..., description="Confidence score formatted as percentage (0-100)")
    box: List[int] = Field(default_factory=list, description="Pixel bounding box [x1, y1, x2, y2]")
    box_normalized: List[float] = Field(default_factory=list, description="Normalized coordinates [x1/w, y1/h, x2/w, y2/h]")
    crop_url: Optional[str] = Field(None, description="Relative URL to cropped thumbnail image")
    cefr_level: Optional[str] = Field("A1", description="Estimated CEFR difficulty level (A1, A2, B1, B2, C1, C2)")
    source: str = Field("yolo", description="Detection source: 'yolo' or 'gemini'")


class SceneContext(BaseModel):
    """High-level environmental and spatial scene understanding."""
    scene: str = Field("General", description="Identified scene environment (e.g. Study Desk, Kitchen, Classroom)")
    scene_vietnamese: Optional[str] = Field(None, description="Vietnamese name for scene environment")
    description: Optional[str] = Field(None, description="Brief 1-sentence English description of the scene")
    spatial_relationships: List[str] = Field(default_factory=list, description="List of spatial relation sentences between objects")


class AnalyzeResponse(BaseModel):
    """Full API response contract for POST /api/v1/analyze."""
    file_name: str
    detected_label: List[str]
    detected_objects: List[DetectedObject]
    scene_context: Optional[SceneContext] = None
    annotated_img_url: Optional[str] = None
    lesson_context: str
    quiz: Optional[Dict[str, Any]] = None
    scan_mode: str = "auto"
    success: bool = True
