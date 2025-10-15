"""
Script para analizar la mejora del NER Inteligente vs Diccionario.
Ejecutar DESPUÉS de sincronizar con IntelligentNERService.
"""

import sys
from app.services.sql_database_service import SQLDatabaseService
from app.services.database_service import DatabaseService
from collections import Counter

print("\n" + "="*80)
print("📊 ANÁLISIS DE MEJORA: NER INTELIGENTE vs DICCIONARIO")
print("="*80 + "\n")

# Inicializar servicios
sql_db = SQLDatabaseService()
chroma_db = DatabaseService()

# Estadísticas generales
stats = sql_db.get_statistics()
print(f"📈 MÉTRICAS GENERALES")
print("-" * 80)
print(f"   Total Teachers: {stats['total_teachers']}")
print(f"   Total Courses: {stats['total_courses']}")
print(f"   Total Skills Únicas: {stats['total_skills']}")

# Análisis detallado de teachers
teachers = sql_db.get_all_teachers()
skills_per_teacher = [len(t.skills) for t in teachers]

if skills_per_teacher:
    avg_skills = sum(skills_per_teacher) / len(skills_per_teacher)
    max_skills = max(skills_per_teacher)
    min_skills = min(skills_per_teacher)
    
    print(f"\n📊 DISTRIBUCIÓN DE SKILLS POR TEACHER")
    print("-" * 80)
    print(f"   Promedio: {avg_skills:.1f} skills/teacher")
    print(f"   Máximo: {max_skills} skills")
    print(f"   Mínimo: {min_skills} skills")
    print(f"   Teachers sin skills: {skills_per_teacher.count(0)}")
    
    # Distribución por rangos
    ranges = {
        "0 skills": sum(1 for s in skills_per_teacher if s == 0),
        "1-3 skills": sum(1 for s in skills_per_teacher if 1 <= s <= 3),
        "4-7 skills": sum(1 for s in skills_per_teacher if 4 <= s <= 7),
        "8-12 skills": sum(1 for s in skills_per_teacher if 8 <= s <= 12),
        "13+ skills": sum(1 for s in skills_per_teacher if s >= 13)
    }
    
    print(f"\n   Distribución:")
    for range_name, count in ranges.items():
        percentage = (count / len(teachers) * 100) if teachers else 0
        print(f"      • {range_name}: {count} teachers ({percentage:.1f}%)")

# Top 20 skills más detectadas
print(f"\n\n🏆 TOP 20 SKILLS MÁS DETECTADAS")
print("-" * 80)
all_skills = []
for teacher in teachers:
    all_skills.extend([s.name for s in teacher.skills])

skill_counts = Counter(all_skills)
for i, (skill, count) in enumerate(skill_counts.most_common(20), 1):
    percentage = (count / len(teachers) * 100) if teachers else 0
    print(f"   {i:2d}. {skill:30s} - {count:3d} teachers ({percentage:.1f}%)")

# Análisis de multi-word terms (indicador de NER inteligente)
print(f"\n\n🔍 ANÁLISIS DE TÉRMINOS MULTI-PALABRA")
print("-" * 80)
multi_word_skills = [skill for skill in skill_counts.keys() if ' ' in skill]
single_word_skills = [skill for skill in skill_counts.keys() if ' ' not in skill]

print(f"   Skills multi-palabra detectadas: {len(multi_word_skills)}")
print(f"   Skills de una palabra: {len(single_word_skills)}")

if multi_word_skills:
    print(f"\n   Ejemplos de términos multi-palabra (Top 10):")
    multi_word_counts = [(skill, skill_counts[skill]) for skill in multi_word_skills]
    multi_word_counts.sort(key=lambda x: x[1], reverse=True)
    for skill, count in multi_word_counts[:10]:
        print(f"      • {skill}: {count} teachers")

# Buscar skills académicas/complejas
print(f"\n\n🎓 DETECCIÓN DE SKILLS ACADÉMICAS/TÉCNICAS COMPLEJAS")
print("-" * 80)
academic_keywords = ['learning', 'analytics', 'intelligence', 'artificial', 'machine', 
                     'augmented', 'virtual', 'cmmi', 'arquitectura', 'ingeniería']

academic_skills = [skill for skill in skill_counts.keys() 
                   if any(keyword in skill.lower() for keyword in academic_keywords)]

if academic_skills:
    print(f"   Skills académicas/complejas detectadas: {len(academic_skills)}")
    print(f"\n   Ejemplos:")
    academic_counts = [(skill, skill_counts[skill]) for skill in academic_skills]
    academic_counts.sort(key=lambda x: x[1], reverse=True)
    for skill, count in academic_counts[:15]:
        print(f"      • {skill}: {count} teachers")
else:
    print(f"   ⚠️  No se detectaron skills académicas complejas")

# Caso de estudio: SAGASTEGUI
print(f"\n\n👨‍🏫 CASO DE ESTUDIO: SAGASTEGUI CHIGNE")
print("-" * 80)
sagastegui = next((t for t in teachers if 'SAGASTEGUI' in t.name.upper()), None)

if sagastegui:
    sagastegui_skills = [s.name for s in sagastegui.skills]
    print(f"   Nombre: {sagastegui.name}")
    print(f"   Skills detectadas: {len(sagastegui_skills)}")
    print(f"   Lista de skills:")
    for skill in sorted(sagastegui_skills):
        print(f"      • {skill}")
    
    # Verificar si detectó skills esperadas
    expected_skills = ['machine learning', 'learning analytics', 'data analytics', 
                       'artificial intelligence', 'augmented reality', 'cmmi']
    detected_expected = [skill for skill in sagastegui_skills 
                         if any(exp in skill.lower() for exp in expected_skills)]
    
    print(f"\n   Skills esperadas detectadas: {len(detected_expected)}/{len(expected_skills)}")
    if detected_expected:
        print(f"   ✅ Detectadas correctamente:")
        for skill in detected_expected:
            print(f"      • {skill}")
    
    missing = [exp for exp in expected_skills 
               if not any(exp in skill.lower() for skill in sagastegui_skills)]
    if missing:
        print(f"\n   ❌ Skills esperadas NO detectadas:")
        for skill in missing:
            print(f"      • {skill}")
else:
    print(f"   ⚠️  Teacher SAGASTEGUI no encontrado en la base de datos")

# Comparación con resultados anteriores (manual)
print(f"\n\n📊 COMPARACIÓN CON NER ANTERIOR (Diccionario)")
print("-" * 80)
print(f"   ANTES (Diccionario):")
print(f"      • Promedio: 3.0 skills/teacher")
print(f"      • Top skill: 'go' (100% - falso positivo)")
print(f"      • SAGASTEGUI: 2 skills (git, go)")
print(f"      • Multi-palabra: 0")
print(f"")
print(f"   AHORA (Inteligente):")
print(f"      • Promedio: {avg_skills:.1f} skills/teacher")
print(f"      • Top skill: {skill_counts.most_common(1)[0][0]} ({skill_counts.most_common(1)[0][1]/len(teachers)*100:.1f}%)")
if sagastegui:
    print(f"      • SAGASTEGUI: {len(sagastegui_skills)} skills")
print(f"      • Multi-palabra: {len(multi_word_skills)} skills")

# Calcular mejora porcentual
if avg_skills > 3.0:
    improvement = ((avg_skills - 3.0) / 3.0) * 100
    print(f"\n   🎯 MEJORA: +{improvement:.1f}% en detección de skills")
else:
    print(f"\n   ⚠️  No se observó mejora en la detección")

print("\n" + "="*80)
print("✅ ANÁLISIS COMPLETADO")
print("="*80 + "\n")

sql_db.close()
