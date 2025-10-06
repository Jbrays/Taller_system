from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.database_service import DatabaseService
from ..services.advanced_matching_service import AdvancedMatchingService

router = APIRouter()

db_service = DatabaseService()
matching_service = AdvancedMatchingService()

class RecommendationRequest(BaseModel):
    cycle_name: str
    course_name: str
    cv_folder_id: str
    syllabus_folder_id: str

@router.post("/recommendations/reset-database", tags=["Recommendations"])
async def reset_database():
    """
    Resetea la base de datos ChromaDB en caso de corrupción.
    """
    try:
        db_service._reinitialize_database()
        return {"status": "success", "message": "Base de datos reinicializada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al resetear base de datos: {str(e)}")

@router.post("/recommendations/generate", tags=["Recommendations"])
async def generate_recommendations(request: RecommendationRequest):
    """
    Genera recomendaciones de docentes para un curso específico basado en el nombre del ciclo y curso.
    """
    print(f"Generando recomendaciones para: {request.cycle_name} - {request.course_name}")
    
    try:
        # 1. Buscar el sílabo en la base de datos usando cycle_name y course_name
        syllabus_results = db_service.syllabus_collection.get(
            include=["metadatas", "embeddings"]
        )
        
        if not syllabus_results or not syllabus_results.get('metadatas'):
            raise HTTPException(
                status_code=404, 
                detail="No se encontraron sílabos en la base de datos. Ejecute la sincronización primero."
            )
        
        # Debug: Mostrar todos los sílabos disponibles
        print(f"Total de sílabos en la base de datos: {len(syllabus_results['metadatas'])}")
        for i, metadata in enumerate(syllabus_results['metadatas']):
            print(f"🔍 DEBUG Sílabo {i} - Metadata completa: {metadata}")
            print(f"Sílabo {i}: cycle='{metadata.get('cycle', '')}', course='{metadata.get('course', '')}', name='{metadata.get('name', '')}', filename='{metadata.get('filename', '')}'")
        
        print(f"Buscando: cycle_name='{request.cycle_name}', course_name='{request.course_name}'")
        
        # Buscar el sílabo que coincida con el ciclo y curso
        target_syllabus = None
        target_syllabus_id = None
        target_embedding = None
        
        for i, metadata in enumerate(syllabus_results['metadatas']):
            syllabus_cycle = metadata.get('cycle', '')
            syllabus_course = metadata.get('course', '')
            
            print(f"Comparando con sílabo {i}: cycle='{syllabus_cycle}', course='{syllabus_course}'")
            
            # Comparación flexible de nombres
            cycle_match = (request.cycle_name.lower() in syllabus_cycle.lower() or 
                          syllabus_cycle.lower() in request.cycle_name.lower())
            course_match = (request.course_name.lower() in syllabus_course.lower() or 
                           syllabus_course.lower() in request.course_name.lower())
            
            print(f"  - cycle_match: {cycle_match}")
            print(f"  - course_match: {course_match}")
            
            if cycle_match and course_match:
                target_syllabus = metadata
                target_syllabus_id = syllabus_results['ids'][i]
                target_embedding = syllabus_results['embeddings'][i]
                break
        
        if not target_syllabus:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró un sílabo para {request.cycle_name} - {request.course_name}. Verifique que el archivo existe y ha sido sincronizado."
            )
        
        print(f"Sílabo encontrado: {target_syllabus.get('name', 'N/A')} (ID: {target_syllabus_id})")
        
        # 2. Buscar CVs similares semánticamente
        cv_results, semantic_distances = db_service.search_similar("cvs", target_embedding, n_results=20)
        if cv_results is None:
            raise HTTPException(status_code=500, detail="Error al realizar la búsqueda vectorial.")
        
        # 3. Aplicar matching avanzado a cada candidato
        syllabus_entities = target_syllabus.get('entities', {})
        advanced_recommendations = []
        
        for cv_metadata, semantic_distance in zip(cv_results, semantic_distances):
            # Debugging detallado de la distancia semántica
            print(f"\n🔍 DEBUG CV - {cv_metadata.get('name', 'Unknown')}")
            print(f"   Semantic distance (raw): {semantic_distance}")
            print(f"   Distance range interpretation (for normalized vectors):")
            print(f"     - 0.0 = identical vectors")
            print(f"     - 1.0 = moderate difference") 
            print(f"     - 1.414 ≈ maximum for normalized vectors (orthogonal)")
            print(f"     - 2.0 = maximum possible distance for normalized vectors")
            
            # Convertir distancia L2 a similitud para vectores normalizados
            # Para vectores normalizados: distancia máxima = 2.0 (vectores opuestos)
            # Fórmula: similarity = 1 - (distance / 2.0)
            
            if semantic_distance > 2.5:
                # Distancias anómalamente altas - problema con embeddings
                semantic_similarity = 0.0
                print(f"   ⚠️  WARNING: Very high distance - may indicate non-normalized vectors")
            else:
                # Fórmula estándar para vectores normalizados
                semantic_similarity = max(0.0, 1.0 - (semantic_distance / 2.0))
                print(f"   ✅ Normal distance for normalized vectors")
                
            print(f"   Semantic similarity (calculated): {semantic_similarity:.6f}")
            print(f"   Metadata keys: {list(cv_metadata.keys())}")
            
            # Obtener entidades del CV - reconstruir desde metadatos aplanados
            if 'entities' in cv_metadata:
                cv_entities = cv_metadata['entities']
                print(f"   Found 'entities' key directly")
            else:
                print(f"   Reconstructing entities from flattened metadata...")
                cv_entities = {
                    'name': cv_metadata.get('name', 'Unknown'),  # Agregar nombre del profesor
                    'technical_skills': cv_metadata.get('entities_technical_skills', '').split(', ') if cv_metadata.get('entities_technical_skills') else [],
                    'experience_years': int(cv_metadata.get('entities_experience_years', 0)) if cv_metadata.get('entities_experience_years', '').isdigit() else 0,
                    'education': cv_metadata.get('entities_education', '').split(', ') if cv_metadata.get('entities_education') else [],
                    'organizations': cv_metadata.get('entities_organizations', '').split(', ') if cv_metadata.get('entities_organizations') else [],
                    'certifications': cv_metadata.get('entities_certifications', '').split(', ') if cv_metadata.get('entities_certifications') else [],
                    'languages': cv_metadata.get('entities_languages', '').split(', ') if cv_metadata.get('entities_languages') else []
                }
                # Limpiar entradas vacías
                cv_entities['technical_skills'] = [skill.strip() for skill in cv_entities['technical_skills'] if skill.strip()]
                cv_entities['education'] = [edu.strip() for edu in cv_entities['education'] if edu.strip()]
                cv_entities['organizations'] = [org.strip() for org in cv_entities['organizations'] if org.strip()]
                cv_entities['certifications'] = [cert.strip() for cert in cv_entities['certifications'] if cert.strip()]
                cv_entities['languages'] = [lang.strip() for lang in cv_entities['languages'] if lang.strip()]
            
            print(f"   Final CV entities: {cv_entities}")
            
            # Obtener entidades del sílabo - también necesitan reconstrucción
            if 'entities' in target_syllabus:
                syllabus_entities = target_syllabus['entities']
            else:
                syllabus_entities = {
                    'required_skills': target_syllabus.get('entities_required_skills', '').split(', ') if target_syllabus.get('entities_required_skills') else [],
                    'tools_required': target_syllabus.get('entities_tools_required', '').split(', ') if target_syllabus.get('entities_tools_required') else [],
                    'course_topics': target_syllabus.get('entities_course_topics', '').split(', ') if target_syllabus.get('entities_course_topics') else [],
                    'methodologies': target_syllabus.get('entities_methodologies', '').split(', ') if target_syllabus.get('entities_methodologies') else [],
                    'prerequisites': target_syllabus.get('entities_prerequisites', '').split(', ') if target_syllabus.get('entities_prerequisites') else []
                }
                # Limpiar entradas vacías
                for key in syllabus_entities:
                    if isinstance(syllabus_entities[key], list):
                        syllabus_entities[key] = [item.strip() for item in syllabus_entities[key] if item.strip()]
            
            print(f"   Syllabus entities: {syllabus_entities}")
            
            # Calcular matching avanzado
            advanced_match = matching_service.calculate_advanced_match(
                cv_entities, syllabus_entities, semantic_similarity
            )
            
            recommendation = {
                "teacher_name": cv_metadata.get("name", "N/A"),
                "cv_filename": cv_metadata.get("filename", "N/A"),
                "score": advanced_match['final_score'],
                "component_scores": advanced_match['component_scores'],
                "explanation": advanced_match['explanation']
            }
            
            advanced_recommendations.append(recommendation)
        
        # 4. Ordenar por score final y tomar top 10
        final_recommendations = matching_service.rank_candidates(advanced_recommendations)[:10]
        
        return {
            "cycle_name": request.cycle_name,
            "course_name": request.course_name,
            "syllabus_info": {
                "name": target_syllabus.get("name", "N/A"),
                "cycle": target_syllabus.get("cycle", "N/A"),
                "required_skills": syllabus_entities.get('required_skills', []),
                "course_topics": syllabus_entities.get('course_topics', [])
            },
            "recommendations": final_recommendations,
            "total_analyzed": len(advanced_recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar recomendaciones: {str(e)}")

@router.get("/recommendations/{syllabus_id}", tags=["Recommendations"])
async def get_recommendations(syllabus_id: str):
    """
    Genera un ranking avanzado de docentes para un sílabo usando NER + SBERT.
    """
    print(f"Generando recomendaciones avanzadas para el sílabo ID: {syllabus_id}")

    # 1. Obtener el sílabo completo (embedding + metadata con entidades)
    try:
        syllabus_data = db_service.syllabus_collection.get(
            ids=[syllabus_id], 
            include=["embeddings", "metadatas"]
        )
        if not syllabus_data or not syllabus_data.get('embeddings'):
            raise HTTPException(
                status_code=404, 
                detail="El sílabo no ha sido procesado o no se encontró. Ejecute la sincronización."
            )
        
        syllabus_embedding = syllabus_data['embeddings'][0]
        syllabus_metadata = syllabus_data['metadatas'][0]
        
        # Reconstruir entidades del sílabo
        if 'entities' in syllabus_metadata:
            syllabus_entities = syllabus_metadata['entities']
        else:
            syllabus_entities = {
                'required_skills': syllabus_metadata.get('entities_required_skills', '').split(', ') if syllabus_metadata.get('entities_required_skills') else [],
                'tools_required': syllabus_metadata.get('entities_tools_required', '').split(', ') if syllabus_metadata.get('entities_tools_required') else [],
                'course_topics': syllabus_metadata.get('entities_course_topics', '').split(', ') if syllabus_metadata.get('entities_course_topics') else [],
                'methodologies': syllabus_metadata.get('entities_methodologies', '').split(', ') if syllabus_metadata.get('entities_methodologies') else [],
                'prerequisites': syllabus_metadata.get('entities_prerequisites', '').split(', ') if syllabus_metadata.get('entities_prerequisites') else []
            }
            # Limpiar entradas vacías
            for key in syllabus_entities:
                if isinstance(syllabus_entities[key], list):
                    syllabus_entities[key] = [item.strip() for item in syllabus_entities[key] if item.strip()]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos del sílabo: {e}")

    # 2. Buscar CVs similares semánticamente
    cv_results, semantic_distances = db_service.search_similar("cvs", syllabus_embedding, n_results=20)
    if cv_results is None:
        raise HTTPException(status_code=500, detail="Error al realizar la búsqueda vectorial.")

    # 3. Aplicar matching avanzado a cada candidato
    advanced_recommendations = []
    
    for cv_metadata, semantic_distance in zip(cv_results, semantic_distances):
        # Convertir distancia L2 a similitud (0-1)
        semantic_similarity = max(0, 1 - (semantic_distance / 2))
        
        # Obtener entidades del CV - reconstruir desde metadatos aplanados
        if 'entities' in cv_metadata:
            cv_entities = cv_metadata['entities']
        else:
            cv_entities = {
                'name': cv_metadata.get('name', 'Unknown'),  # Agregar nombre del profesor
                'technical_skills': cv_metadata.get('entities_technical_skills', '').split(', ') if cv_metadata.get('entities_technical_skills') else [],
                'experience_years': int(cv_metadata.get('entities_experience_years', 0)) if cv_metadata.get('entities_experience_years', '').isdigit() else 0,
                'education': cv_metadata.get('entities_education', '').split(', ') if cv_metadata.get('entities_education') else [],
                'organizations': cv_metadata.get('entities_organizations', '').split(', ') if cv_metadata.get('entities_organizations') else [],
                'certifications': cv_metadata.get('entities_certifications', '').split(', ') if cv_metadata.get('entities_certifications') else [],
                'languages': cv_metadata.get('entities_languages', '').split(', ') if cv_metadata.get('entities_languages') else []
            }
            # Limpiar entradas vacías
            cv_entities['technical_skills'] = [skill.strip() for skill in cv_entities['technical_skills'] if skill.strip()]
            cv_entities['education'] = [edu.strip() for edu in cv_entities['education'] if edu.strip()]
            cv_entities['organizations'] = [org.strip() for org in cv_entities['organizations'] if org.strip()]
            cv_entities['certifications'] = [cert.strip() for cert in cv_entities['certifications'] if cert.strip()]
            cv_entities['languages'] = [lang.strip() for lang in cv_entities['languages'] if lang.strip()]
        
        # Calcular matching avanzado
        advanced_match = matching_service.calculate_advanced_match(
            cv_entities, syllabus_entities, semantic_similarity
        )
        
        recommendation = {
            "teacher_name": cv_metadata.get("name", "N/A"),
            "final_score": advanced_match['final_score'],
            "component_scores": advanced_match['component_scores'],
            "explanation": advanced_match['explanation']
        }
        
        advanced_recommendations.append(recommendation)

    # 4. Ordenar por score final y tomar top 10
    final_recommendations = matching_service.rank_candidates(advanced_recommendations)[:10]

    return {
        "syllabus_id": syllabus_id,
        "syllabus_info": {
            "name": syllabus_metadata.get("name", "N/A"),
            "required_skills": syllabus_entities.get('required_skills', []),
            "course_topics": syllabus_entities.get('course_topics', [])
        },
        "recommendations": final_recommendations,
        "total_analyzed": len(advanced_recommendations)
    }