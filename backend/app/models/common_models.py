"""
Modelos comunes reutilizables en todo el sistema.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata de un documento procesado (CV o Sílabo)."""
    
    document_id: str = Field(
        ...,
        description="ID único del documento (ej: Google Drive file ID)",
        example="1abc123def456"
    )
    filename: str = Field(
        ...,
        description="Nombre del archivo",
        example="Juan_Perez_CV.pdf"
    )
    document_type: str = Field(
        ...,
        description="Tipo de documento: 'cv' o 'syllabus'",
        example="cv"
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp de cuando fue procesado"
    )
    cycle: Optional[str] = Field(
        default=None,
        description="Ciclo académico (solo para sílabos)",
        example="Ciclo 01"
    )
    course: Optional[str] = Field(
        default=None,
        description="Nombre del curso (solo para sílabos)",
        example="Programación Orientada a Objetos"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "1abc123def456",
                "filename": "Juan_Perez_CV.pdf",
                "document_type": "cv",
                "processed_at": "2025-10-14T10:30:00"
            }
        }


class EmbeddingInfo(BaseModel):
    """Información sobre un embedding generado."""
    
    dimension: int = Field(
        ...,
        description="Dimensión del vector de embedding",
        example=384,
        ge=1
    )
    model_name: str = Field(
        ...,
        description="Nombre del modelo usado para generar el embedding",
        example="paraphrase-multilingual-MiniLM-L12-v2"
    )
    normalized: bool = Field(
        ...,
        description="Indica si el embedding está normalizado (norma = 1.0)",
        example=True
    )
    norm: Optional[float] = Field(
        default=None,
        description="Norma euclidiana del vector",
        example=1.0,
        ge=0.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "dimension": 384,
                "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
                "normalized": True,
                "norm": 1.0
            }
        }


class ErrorResponse(BaseModel):
    """Response estándar para errores de la API."""
    
    status: str = Field(
        default="error",
        description="Estado de la operación",
        example="error"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Código de error identificador",
        example="SYNC_001"
    )
    message: str = Field(
        ...,
        description="Mensaje de error descriptivo",
        example="No se pudo conectar a Google Drive"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalles adicionales del error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "SYNC_001",
                "message": "No se pudo conectar a Google Drive",
                "details": {"folder_id": "invalid_id"},
                "timestamp": "2025-10-14T10:30:00"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response del endpoint de health check."""
    
    status: str = Field(
        ...,
        description="Estado del sistema: 'healthy' o 'unhealthy'",
        example="healthy"
    )
    version: str = Field(
        ...,
        description="Versión de la API",
        example="0.1.0"
    )
    services: Dict[str, str] = Field(
        ...,
        description="Estado de servicios externos",
        example={
            "database": "operational",
            "nlp_model": "loaded",
            "drive_api": "connected"
        }
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la verificación"
    )
