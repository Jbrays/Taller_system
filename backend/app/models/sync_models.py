"""
Modelos para las operaciones de sincronización con Google Drive.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SyncRequest(BaseModel):
    """Request para iniciar sincronización de documentos desde Google Drive."""
    
    cv_folder_id: str = Field(
        ...,
        description="ID de la carpeta de Google Drive que contiene los CVs",
        example="1abc123def456ghi789jkl"
    )
    syllabus_folder_id: str = Field(
        ...,
        description="ID de la carpeta de Google Drive que contiene los sílabos",
        example="1xyz987wvu654tsr321qpo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cv_folder_id": "1abc123def456ghi789jkl",
                "syllabus_folder_id": "1xyz987wvu654tsr321qpo"
            }
        }


class SyncResponse(BaseModel):
    """Response de una operación de sincronización."""
    
    status: str = Field(
        ...,
        description="Estado de la sincronización: 'success' o 'error'",
        example="success"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del resultado",
        example="Sincronización completada exitosamente"
    )
    cvs_processed: int = Field(
        default=0,
        description="Número de CVs procesados correctamente",
        ge=0
    )
    syllabi_processed: int = Field(
        default=0,
        description="Número de sílabos procesados correctamente",
        ge=0
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="Lista de errores encontrados durante el procesamiento"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Sincronización completada exitosamente",
                "cvs_processed": 15,
                "syllabi_processed": 8,
                "errors": []
            }
        }
