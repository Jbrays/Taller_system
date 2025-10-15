from fastapi import APIRouter, HTTPException
from ..models.recommendation_models import RecommendationRequest, RecommendationResponse, TeacherRecommendation, ComponentScores
from ..services.database_service import DatabaseService
from ..services.sql_database_service import SQLDatabaseService
from ..services.advanced_matching_service import AdvancedMatchingService

router = APIRouter()

db_service = DatabaseService()  # ChromaDB (vectorial)
sql_db_service = SQLDatabaseService()  # SQLite (relacional)
matching_service = AdvancedMatchingService()

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

@router.post("/recommendations/generate-hybrid", tags=["Recommendations"])
async def generate_hybrid_recommendations(request: RecommendationRequest):
    """
    NUEVO: Genera recomendaciones usando arquitectura híbrida SQL + ChromaDB.
    
    Flujo:
    1. Busca el curso en SQL por nombre
    2. Obtiene teachers que tengan al menos 1 skill requerida (filtro SQL)
    3. Para cada candidato filtrado, calcula similitud semántica con ChromaDB
    4. Combina scores: 40% SQL (skill match) + 60% ChromaDB (semantic similarity)
    5. Retorna top 10 ordenados por score final
    """
    print(f"\n🔀 HYBRID MATCHING: {request.cycle_name} - {request.course_name}")
    
    try:
        # === PASO 1: Buscar sílabo en ChromaDB para obtener embedding ===
        syllabus_results = db_service.syllabus_collection.get(
            include=["metadatas", "embeddings"]
        )
        
        if not syllabus_results or not syllabus_results.get('metadatas'):
            raise HTTPException(
                status_code=404,
                detail="No hay sílabos sincronizados en ChromaDB"
            )
        
        # Buscar el sílabo que coincida
        target_syllabus = None
        target_embedding = None
        target_embedding_id = None
        
        for i, metadata in enumerate(syllabus_results['metadatas']):
            cycle_match = (request.cycle_name.lower() in metadata.get('cycle', '').lower() or 
                          metadata.get('cycle', '').lower() in request.cycle_name.lower())
            course_match = (request.course_name.lower() in metadata.get('course', '').lower() or 
                           metadata.get('course', '').lower() in request.course_name.lower())
            
            if cycle_match and course_match:
                target_syllabus = metadata
                target_embedding = syllabus_results['embeddings'][i]
                target_embedding_id = syllabus_results['ids'][i]
                break
        
        if not target_syllabus:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró sílabo para {request.cycle_name} - {request.course_name}"
            )
        
        print(f"✅ Sílabo encontrado: {target_syllabus.get('name')} (ID: {target_embedding_id})")
        
        # === PASO 2: Buscar curso en SQL para obtener required_skills ===
        sql_courses = sql_db_service.get_all_courses()
        target_course_sql = None
        
        for course in sql_courses:
            if course.embedding_id == target_embedding_id:
                target_course_sql = course
                break
        
        if not target_course_sql:
            print("⚠️  Curso no encontrado en SQL, usando solo ChromaDB")
            # Fallback al endpoint antiguo
            return await generate_recommendations(request)
        
        required_skill_names = [skill.name for skill in target_course_sql.required_skills]
        print(f"📋 Required skills (SQL): {required_skill_names}")
        
        if not required_skill_names:
            print("⚠️  No hay required skills en SQL, usando solo ChromaDB")
            return await generate_recommendations(request)
        
        # === PASO 3: Filtrar teachers con SQL (al menos 1 skill match) ===
        sql_candidates = sql_db_service.find_teachers_by_skills(required_skill_names, min_matches=1)
        print(f"🔍 SQL filtró {len(sql_candidates)} teachers con skills coincidentes")
        
        if not sql_candidates:
            return {
                "cycle_name": request.cycle_name,
                "course_name": request.course_name,
                "syllabus_info": {
                    "name": target_syllabus.get("name", "N/A"),
                    "cycle": target_syllabus.get("cycle", "N/A"),
                    "required_skills": required_skill_names
                },
                "recommendations": [],
                "total_analyzed": 0,
                "message": "No se encontraron docentes con las skills requeridas"
            }
        
        # === PASO 4: Para cada candidato SQL, obtener similitud semántica de ChromaDB ===
        hybrid_recommendations = []
        
        for teacher, sql_matches_count in sql_candidates:
            # Calcular SQL score (porcentaje de skills que coinciden)
            sql_score_detail = sql_db_service.calculate_sql_match_score(
                teacher.id, 
                target_course_sql.id
            )
            sql_score = sql_score_detail['score']
            
            # Obtener embedding del teacher desde ChromaDB
            teacher_data = db_service.cv_collection.get(
                ids=[teacher.embedding_id],
                include=["embeddings", "metadatas"]
            )
            
            if not teacher_data or not teacher_data.get('embeddings'):
                print(f"  ⚠️  Teacher {teacher.name} no tiene embedding en ChromaDB")
                continue
            
            teacher_embedding = teacher_data['embeddings'][0]
            teacher_metadata = teacher_data['metadatas'][0]
            
            # Calcular similitud semántica (distancia L2 → similarity)
            from numpy import dot
            from numpy.linalg import norm
            
            # Cosine similarity (más preciso para vectores normalizados)
            semantic_similarity = dot(target_embedding, teacher_embedding) / (
                norm(target_embedding) * norm(teacher_embedding)
            )
            semantic_similarity = max(0.0, min(1.0, semantic_similarity))
            
            # === PASO 5: Combinar scores ===
            # Pesos: 40% SQL (skill match) + 60% semántico (SBERT)
            final_score = (0.4 * sql_score) + (0.6 * semantic_similarity)
            
            # Reconstruir entidades para explanation
            if 'entities' in teacher_metadata:
                cv_entities = teacher_metadata['entities']
            else:
                cv_entities = {
                    'technical_skills': teacher_metadata.get('entities_technical_skills', '').split(', ') if teacher_metadata.get('entities_technical_skills') else [],
                    'experience_years': int(teacher_metadata.get('entities_experience_years', 0)) if teacher_metadata.get('entities_experience_years', '').isdigit() else 0
                }
            
            recommendation = {
                "teacher_name": teacher.name,
                "cv_filename": teacher_metadata.get("filename", "N/A"),
                "score": final_score,
                "component_scores": {
                    "sql_score": sql_score,
                    "semantic_similarity": semantic_similarity,
                    "matched_skills_count": sql_matches_count,
                    "total_required_skills": len(required_skill_names)
                },
                "explanation": {
                    "matched_skills": sql_score_detail['matched_skills'],
                    "missing_skills": sql_score_detail['missing_skills'],
                    "teacher_skills": [s.name for s in teacher.skills],
                    "experience_years": teacher.experience_years
                }
            }
            
            hybrid_recommendations.append(recommendation)
            
            # Guardar en historial
            sql_db_service.save_matching_result(
                teacher_id=teacher.id,
                course_id=target_course_sql.id,
                sql_score=sql_score,
                semantic_score=semantic_similarity,
                final_score=final_score,
                matched_skills_count=sql_matches_count
            )
        
        # === PASO 6: Ordenar por final_score y retornar top 10 ===
        final_recommendations = sorted(
            hybrid_recommendations, 
            key=lambda x: x['score'], 
            reverse=True
        )[:10]
        
        print(f"✅ Generadas {len(final_recommendations)} recomendaciones híbridas")
        
        return {
            "cycle_name": request.cycle_name,
            "course_name": request.course_name,
            "matching_method": "hybrid_sql_chromadb",
            "syllabus_info": {
                "name": target_syllabus.get("name", "N/A"),
                "cycle": target_syllabus.get("cycle", "N/A"),
                "required_skills": required_skill_names
            },
            "recommendations": final_recommendations,
            "total_analyzed": len(hybrid_recommendations),
            "weights": {
                "sql_skill_match": "40%",
                "semantic_similarity": "60%"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en hybrid matching: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en matching híbrido: {str(e)}")


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
                'methodologies': syllabus_metadata.get('entities_methodologies', '').split(', ') if syllabus_metadata.get('entities_methodologias') else [],
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

@router.get("/recommendations/stats", tags=["Recommendations"])
async def get_system_statistics():
    """
    Obtiene estadísticas del sistema de matching (SQL + ChromaDB).
    """
    try:
        sql_stats = sql_db_service.get_statistics()
        
        # Stats de ChromaDB
        cv_count = db_service.cv_collection.count()
        syllabus_count = db_service.syllabus_collection.count()
        
        return {
            "sql_database": sql_stats,
            "chromadb": {
                "total_cvs": cv_count,
                "total_syllabi": syllabus_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")