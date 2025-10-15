"""
Modelos de datos (Pydantic schemas) para el sistema de emparejamiento.

Este módulo centraliza todos los modelos de validación de datos
para requests y responses de la API.
"""

from .sync_models import SyncRequest, SyncResponse
from .recommendation_models import RecommendationRequest, RecommendationResponse, TeacherRecommendation
from .common_models import DocumentMetadata, EmbeddingInfo, ErrorResponse

__all__ = [
    # Sync models
    "SyncRequest",
    "SyncResponse",
    
    # Recommendation models
    "RecommendationRequest",
    "RecommendationResponse",
    "TeacherRecommendation",
    
    # Common models
    "DocumentMetadata",
    "EmbeddingInfo",
    "ErrorResponse",
]
