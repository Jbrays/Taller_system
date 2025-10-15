"""
Modelos para el sistema de recomendaciones de docentes.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class RecommendationRequest(BaseModel):
    """Request para generar recomendaciones de docentes para un curso."""
    
    cycle_name: str = Field(
        ...,
        description="Nombre del ciclo académico",
        example="Ciclo 01"
    )
    course_name: str = Field(
        ...,
        description="Nombre del curso",
        example="Programación Orientada a Objetos"
    )
    cv_folder_id: str = Field(
        ...,
        description="ID de la carpeta de Google Drive con CVs",
        example="1abc123def456ghi789jkl"
    )
    syllabus_folder_id: str = Field(
        ...,
        description="ID de la carpeta de Google Drive con sílabos",
        example="1xyz987wvu654tsr321qpo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cycle_name": "Ciclo 01",
                "course_name": "Programación Orientada a Objetos",
                "cv_folder_id": "1abc123def456ghi789jkl",
                "syllabus_folder_id": "1xyz987wvu654tsr321qpo"
            }
        }


class ComponentScores(BaseModel):
    """Scores detallados de cada componente del algoritmo de matching."""
    
    semantic_similarity: float = Field(
        ...,
        description="Similitud semántica (SBERT)",
        ge=0.0,
        le=100.0
    )
    skill_match: float = Field(
        ...,
        description="Compatibilidad de habilidades técnicas",
        ge=0.0,
        le=100.0
    )
    experience_match: float = Field(
        ...,
        description="Compatibilidad de experiencia",
        ge=0.0,
        le=100.0
    )
    education_match: float = Field(
        ...,
        description="Compatibilidad educativa",
        ge=0.0,
        le=100.0
    )


class TeacherRecommendation(BaseModel):
    """Recomendación individual de un docente para un curso."""
    
    teacher_name: str = Field(
        ...,
        description="Nombre del docente",
        example="Dr. Juan Pérez"
    )
    final_score: float = Field(
        ...,
        description="Score final ponderado (0-100)",
        ge=0.0,
        le=100.0,
        example=85.5
    )
    component_scores: ComponentScores = Field(
        ...,
        description="Desglose de scores por componente"
    )
    explanation: str = Field(
        ...,
        description="Explicación contextual de la recomendación",
        example="Excelente coincidencia en habilidades técnicas (Python, Java) y experiencia en POO"
    )
    rank: Optional[int] = Field(
        default=None,
        description="Posición en el ranking (1 = mejor)",
        ge=1
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "teacher_name": "Dr. Juan Pérez",
                "final_score": 85.5,
                "component_scores": {
                    "semantic_similarity": 88.2,
                    "skill_match": 92.0,
                    "experience_match": 78.5,
                    "education_match": 80.0
                },
                "explanation": "Excelente coincidencia en habilidades técnicas",
                "rank": 1
            }
        }


class RecommendationResponse(BaseModel):
    """Response con las recomendaciones de docentes para un curso."""
    
    course_name: str = Field(
        ...,
        description="Nombre del curso analizado",
        example="Programación Orientada a Objetos"
    )
    cycle_name: str = Field(
        ...,
        description="Nombre del ciclo académico",
        example="Ciclo 01"
    )
    recommendations: List[TeacherRecommendation] = Field(
        ...,
        description="Lista de recomendaciones ordenadas por score (mayor a menor)"
    )
    total_candidates: int = Field(
        ...,
        description="Número total de docentes evaluados",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_name": "Programación Orientada a Objetos",
                "cycle_name": "Ciclo 01",
                "recommendations": [
                    {
                        "teacher_name": "Dr. Juan Pérez",
                        "final_score": 85.5,
                        "rank": 1
                    }
                ],
                "total_candidates": 15
            }
        }
