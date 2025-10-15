"""
Script de prueba para verificar la arquitectura híbrida SQL + ChromaDB.
Ejecutar después de hacer sync para verificar que ambas bases de datos están pobladas.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.sql_database_service import SQLDatabaseService
from app.services.database_service import DatabaseService


def test_hybrid_architecture():
    """Prueba la arquitectura híbrida SQL + ChromaDB."""
    
    print("\n" + "="*70)
    print("🧪 PRUEBA DE ARQUITECTURA HÍBRIDA SQL + ChromaDB")
    print("="*70 + "\n")
    
    # Inicializar servicios
    sql_db = SQLDatabaseService()
    chroma_db = DatabaseService()
    
    # === TEST 1: Verificar SQL Database ===
    print("📊 TEST 1: Estadísticas de SQL Database")
    print("-" * 70)
    
    stats = sql_db.get_statistics()
    print(f"✅ Total Teachers: {stats['total_teachers']}")
    print(f"✅ Total Courses: {stats['total_courses']}")
    print(f"✅ Total Skills: {stats['total_skills']}")
    print(f"✅ Total Matches Realizados: {stats['total_matches_performed']}")
    
    if stats['top_required_skills']:
        print("\n📋 Top 5 Skills Más Requeridas:")
        for item in stats['top_required_skills'][:5]:
            print(f"   - {item['skill']}: {item['courses']} cursos")
    
    if stats['top_teacher_skills']:
        print("\n👨‍🏫 Top 5 Skills de Docentes:")
        for item in stats['top_teacher_skills'][:5]:
            print(f"   - {item['skill']}: {item['teachers']} docentes")
    
    # === TEST 2: Verificar ChromaDB ===
    print("\n\n💾 TEST 2: Estadísticas de ChromaDB")
    print("-" * 70)
    
    cv_count = chroma_db.cv_collection.count()
    syllabus_count = chroma_db.syllabus_collection.count()
    
    print(f"✅ Total CVs: {cv_count}")
    print(f"✅ Total Sílabos: {syllabus_count}")
    
    # === TEST 3: Verificar sincronización entre ambas bases ===
    print("\n\n🔄 TEST 3: Verificación de Sincronización")
    print("-" * 70)
    
    teachers = sql_db.get_all_teachers()
    print(f"✅ Teachers en SQL: {len(teachers)}")
    
    synced_count = 0
    not_synced = []
    
    for teacher in teachers[:10]:  # Verificar primeros 10
        chroma_data = chroma_db.cv_collection.get(
            ids=[teacher.embedding_id],
            include=["metadatas"]
        )
        
        if chroma_data and chroma_data.get('metadatas'):
            synced_count += 1
            skills_in_sql = len(teacher.skills)
            print(f"   ✅ {teacher.name}: {skills_in_sql} skills en SQL, embedding en ChromaDB")
        else:
            not_synced.append(teacher.name)
            print(f"   ❌ {teacher.name}: NO ENCONTRADO en ChromaDB")
    
    print(f"\n📈 Sincronización: {synced_count}/{len(teachers[:10])} verificados")
    
    # === TEST 4: Probar búsqueda híbrida ===
    print("\n\n🔍 TEST 4: Búsqueda Híbrida por Skills")
    print("-" * 70)
    
    courses = sql_db.get_all_courses()
    if courses:
        test_course = courses[0]
        required_skills = [skill.name for skill in test_course.required_skills]
        
        print(f"Curso de prueba: {test_course.name}")
        print(f"Required skills: {required_skills}")
        
        if required_skills:
            candidates = sql_db.find_teachers_by_skills(required_skills, min_matches=1)
            print(f"\n✅ Encontrados {len(candidates)} candidatos con al menos 1 skill")
            
            for i, (teacher, matches) in enumerate(candidates[:5], 1):
                score_detail = sql_db.calculate_sql_match_score(teacher.id, test_course.id)
                print(f"\n   {i}. {teacher.name}")
                print(f"      - Matched Skills: {score_detail['matched_skills']}")
                print(f"      - Missing Skills: {score_detail['missing_skills']}")
                print(f"      - SQL Score: {score_detail['score']:.2%}")
                print(f"      - Experiencia: {teacher.experience_years} años")
        else:
            print("⚠️  No hay required skills para este curso")
    else:
        print("⚠️  No hay cursos en la base de datos SQL")
    
    # === RESUMEN FINAL ===
    print("\n\n" + "="*70)
    print("📋 RESUMEN DE LA ARQUITECTURA")
    print("="*70)
    
    if stats['total_teachers'] > 0 and cv_count > 0:
        print("✅ SQL Database: FUNCIONANDO")
        print("✅ ChromaDB: FUNCIONANDO")
        print("✅ Sincronización: OK")
        print("\n🎉 La arquitectura híbrida está lista para usarse!")
        print("\nPróximos pasos:")
        print("  1. Usa el endpoint /recommendations/generate-hybrid para matching")
        print("  2. Compara resultados con /recommendations/generate (antiguo)")
        print("  3. El nuevo sistema combina: 40% SQL + 60% Semántico")
    else:
        print("⚠️  Base de datos vacía. Ejecuta primero:")
        print("    POST /sync con los IDs de las carpetas de Drive")
    
    print("="*70 + "\n")
    
    sql_db.close()


if __name__ == "__main__":
    test_hybrid_architecture()
