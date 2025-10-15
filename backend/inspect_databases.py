"""
Script para inspeccionar el estado actual de las bases de datos SQL y ChromaDB.
"""

import sys
from app.services.sql_database_service import SQLDatabaseService
from app.services.database_service import DatabaseService

print("\n" + "="*80)
print("🔍 INSPECCIÓN DE BASES DE DATOS - SISTEMA HÍBRIDO")
print("="*80 + "\n")

# Inicializar servicios
sql_db = SQLDatabaseService()
chroma_db = DatabaseService()

print("📊 1. ESTADÍSTICAS SQL DATABASE")
print("-" * 80)
stats = sql_db.get_statistics()
print(f"   Teachers: {stats['total_teachers']}")
print(f"   Courses: {stats['total_courses']}")
print(f"   Skills: {stats['total_skills']}")
print(f"   Matches realizados: {stats['total_matches_performed']}")

if stats['total_teachers'] > 0:
    print(f"\n   📋 Top 10 Skills Más Requeridas en Cursos:")
    for item in stats['top_required_skills'][:10]:
        print(f"      • {item['skill']}: {item['courses']} cursos")
    
    print(f"\n   👨‍🏫 Top 10 Skills de Docentes:")
    for item in stats['top_teacher_skills'][:10]:
        print(f"      • {item['skill']}: {item['teachers']} docentes")

print(f"\n\n💾 2. ESTADÍSTICAS CHROMADB")
print("-" * 80)
cv_count = chroma_db.cv_collection.count()
syllabus_count = chroma_db.syllabus_collection.count()
print(f"   CVs: {cv_count}")
print(f"   Sílabos: {syllabus_count}")

# Mostrar algunos ejemplos de teachers
print(f"\n\n👥 3. EJEMPLOS DE TEACHERS (primeros 5)")
print("-" * 80)
teachers = sql_db.get_all_teachers()[:5]
for i, teacher in enumerate(teachers, 1):
    skills_list = [s.name for s in teacher.skills]
    print(f"\n   {i}. {teacher.name}")
    print(f"      Experiencia: {teacher.experience_years} años")
    print(f"      Skills ({len(skills_list)}): {', '.join(skills_list) if skills_list else 'No se detectaron skills'}")
    print(f"      Embedding ID: {teacher.embedding_id}")
    
    # Verificar si existe en ChromaDB
    try:
        chroma_data = chroma_db.cv_collection.get(
            ids=[teacher.embedding_id],
            include=["metadatas"]
        )
        if chroma_data and chroma_data.get('metadatas'):
            metadata = chroma_data['metadatas'][0]
            # Intentar obtener skills del metadata de ChromaDB
            if 'entities' in metadata:
                chroma_skills = metadata['entities'].get('technical_skills', [])
            else:
                chroma_skills_str = metadata.get('entities_technical_skills', '')
                chroma_skills = chroma_skills_str.split(', ') if chroma_skills_str else []
            print(f"      ✅ En ChromaDB con {len(chroma_skills)} skills detectadas por NER")
        else:
            print(f"      ❌ NO ENCONTRADO en ChromaDB")
    except Exception as e:
        print(f"      ⚠️  Error al verificar ChromaDB: {e}")

# Mostrar algunos ejemplos de courses
print(f"\n\n📚 4. EJEMPLOS DE COURSES (primeros 5)")
print("-" * 80)
courses = sql_db.get_all_courses()[:5]
for i, course in enumerate(courses, 1):
    required_skills = [s.name for s in course.required_skills]
    print(f"\n   {i}. {course.name}")
    print(f"      Ciclo: {course.cycle}")
    print(f"      Required Skills ({len(required_skills)}): {', '.join(required_skills) if required_skills else 'No se detectaron skills'}")
    print(f"      Embedding ID: {course.embedding_id}")

# Análisis de calidad NER
print(f"\n\n🎯 5. ANÁLISIS DE CALIDAD NER")
print("-" * 80)

teachers_with_skills = sum(1 for t in sql_db.get_all_teachers() if len(t.skills) > 0)
teachers_without_skills = stats['total_teachers'] - teachers_with_skills

courses_with_skills = sum(1 for c in sql_db.get_all_courses() if len(c.required_skills) > 0)
courses_without_skills = stats['total_courses'] - courses_with_skills

print(f"\n   Teachers:")
print(f"      Con skills detectadas: {teachers_with_skills} ({teachers_with_skills/stats['total_teachers']*100:.1f}%)" if stats['total_teachers'] > 0 else "      Sin datos")
print(f"      Sin skills detectadas: {teachers_without_skills} ({teachers_without_skills/stats['total_teachers']*100:.1f}%)" if stats['total_teachers'] > 0 else "")

print(f"\n   Courses:")
print(f"      Con skills detectadas: {courses_with_skills} ({courses_with_skills/stats['total_courses']*100:.1f}%)" if stats['total_courses'] > 0 else "      Sin datos")
print(f"      Sin skills detectadas: {courses_without_skills} ({courses_without_skills/stats['total_courses']*100:.1f}%)" if stats['total_courses'] > 0 else "")

# Promedio de skills por teacher/course
if stats['total_teachers'] > 0:
    avg_skills_teacher = sum(len(t.skills) for t in sql_db.get_all_teachers()) / stats['total_teachers']
    print(f"\n   Promedio de skills por teacher: {avg_skills_teacher:.1f}")

if stats['total_courses'] > 0:
    avg_skills_course = sum(len(c.required_skills) for c in sql_db.get_all_courses()) / stats['total_courses']
    print(f"   Promedio de required_skills por course: {avg_skills_course:.1f}")

# Verificar sincronización
print(f"\n\n🔄 6. VERIFICACIÓN DE SINCRONIZACIÓN SQL ↔ ChromaDB")
print("-" * 80)

synced_teachers = 0
not_synced_teachers = []

for teacher in sql_db.get_all_teachers():
    try:
        chroma_data = chroma_db.cv_collection.get(
            ids=[teacher.embedding_id],
            include=["metadatas"]
        )
        if chroma_data and chroma_data.get('metadatas'):
            synced_teachers += 1
        else:
            not_synced_teachers.append(teacher.name)
    except:
        not_synced_teachers.append(teacher.name)

print(f"   Teachers sincronizados: {synced_teachers}/{stats['total_teachers']}")
if not_synced_teachers:
    print(f"   Teachers NO sincronizados: {', '.join(not_synced_teachers[:5])}")

print("\n" + "="*80)
print("✅ INSPECCIÓN COMPLETADA")
print("="*80 + "\n")

if stats['total_teachers'] == 0:
    print("⚠️  Las bases de datos están vacías. Ejecuta sync primero:")
    print("   1. Desde el frontend: Click en 'Sincronizar'")
    print("   2. O con cURL en terminal")
    print("")

sql_db.close()
