#!/usr/bin/env python3
"""
Análisis de calidad NER basado en los datos reales de ChromaDB
"""

import sqlite3
import os
from collections import Counter

db_path = os.path.join(os.getcwd(), 'backend', 'chroma_db', 'chroma.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("🔍 ANÁLISIS DE CALIDAD DE NER - Datos Reales")
print("="*80)

# Obtener todos los metadatos de entidades
cursor.execute("""
    SELECT id, key, string_value, int_value
    FROM embedding_metadata
    WHERE key LIKE 'entities_%' OR key = 'name' OR key = 'cycle' OR key = 'course'
    ORDER BY id, key
""")

rows = cursor.fetchall()

# Organizar por documento
docs = {}
for id, key, str_val, int_val in rows:
    if id not in docs:
        docs[id] = {}
    
    value = str_val if str_val is not None else int_val
    docs[id][key] = value

print(f"\n📊 Total de documentos con metadata: {len(docs)}")

# Separar CVs de Sílabos
cvs = [doc for doc in docs.values() if 'course' not in doc]
syllabi = [doc for doc in docs.values() if 'course' in doc]

print(f"   📄 CVs: {len(cvs)}")
print(f"   📘 Sílabos: {len(syllabi)}")

# Analizar CVs
print("\n" + "="*80)
print("📄 ANÁLISIS DE CVs")
print("="*80)

all_cv_skills = []
all_cv_exp = []
all_cv_education = []
all_cv_certs = []
all_cv_languages = []

cv_with_skills = 0
cv_with_exp = 0
cv_with_education = 0

for i, cv in enumerate(cvs[:5], 1):  # Primeros 5 para muestra detallada
    name = cv.get('name', 'Sin nombre')
    print(f"\n{i}. {name}")
    print("-" * 80)
    
    skills = cv.get('entities_technical_skills', '')
    exp = cv.get('entities_experience_years', 0)
    education = cv.get('entities_education', '')
    certs = cv.get('entities_certifications', '')
    languages = cv.get('entities_languages', '')
    
    skills_list = [s.strip() for s in str(skills).split(',') if s.strip()]
    education_list = [e.strip() for e in str(education).split(',') if e.strip()]
    certs_list = [c.strip() for c in str(certs).split(',') if c.strip()]
    languages_list = [l.strip() for l in str(languages).split(',') if l.strip()]
    
    print(f"   🛠️  Skills ({len(skills_list)}): {skills_list[:10]}")
    print(f"   💼 Experiencia: {exp} años")
    print(f"   🎓 Educación ({len(education_list)}): {education_list[:5]}")
    print(f"   📜 Certificaciones ({len(certs_list)}): {certs_list[:3]}")
    print(f"   🗣️  Idiomas ({len(languages_list)}): {languages_list}")

# Estadísticas agregadas de todos los CVs
print(f"\n{'='*80}")
print("📊 ESTADÍSTICAS AGREGADAS - TODOS LOS CVs")
print(f"{'='*80}")

for cv in cvs:
    skills = cv.get('entities_technical_skills', '')
    exp = cv.get('entities_experience_years', 0)
    education = cv.get('entities_education', '')
    certs = cv.get('entities_certifications', '')
    languages = cv.get('entities_languages', '')
    
    if skills:
        cv_with_skills += 1
        all_cv_skills.extend([s.strip() for s in str(skills).split(',') if s.strip()])
    
    if exp and int(exp) > 0:
        cv_with_exp += 1
        all_cv_exp.append(int(exp))
    
    if education:
        cv_with_education += 1
        all_cv_education.extend([e.strip() for e in str(education).split(',') if e.strip()])
    
    if certs:
        all_cv_certs.extend([c.strip() for c in str(certs).split(',') if c.strip()])
    
    if languages:
        all_cv_languages.extend([l.strip() for l in str(languages).split(',') if l.strip()])

print(f"\n✅ Cobertura de extracción NER:")
print(f"   CVs con skills: {cv_with_skills}/{len(cvs)} ({cv_with_skills/len(cvs)*100 if cvs else 0:.1f}%)")
print(f"   CVs con experiencia: {cv_with_exp}/{len(cvs)} ({cv_with_exp/len(cvs)*100 if cvs else 0:.1f}%)")
print(f"   CVs con educación: {cv_with_education}/{len(cvs)} ({cv_with_education/len(cvs)*100 if cvs else 0:.1f}%)")

if all_cv_skills:
    skill_counts = Counter(all_cv_skills)
    print(f"\n🛠️  Top 15 Skills en CVs:")
    for skill, count in skill_counts.most_common(15):
        print(f"   {skill:30s} → {count:2d} veces")
else:
    print(f"\n   ❌ NO se encontraron skills técnicas")

if all_cv_exp:
    avg_exp = sum(all_cv_exp) / len(all_cv_exp)
    print(f"\n💼 Experiencia:")
    print(f"   Promedio: {avg_exp:.1f} años")
    print(f"   Rango: {min(all_cv_exp)} - {max(all_cv_exp)} años")
    print(f"   Distribución: {Counter(all_cv_exp)}")
else:
    print(f"\n   ❌ NO se encontraron años de experiencia")

if all_cv_languages:
    lang_counts = Counter(all_cv_languages)
    print(f"\n🗣️  Idiomas mencionados:")
    for lang, count in lang_counts.most_common():
        print(f"   {lang:20s} → {count:2d} CVs")

# Analizar Sílabos
print(f"\n{'='*80}")
print("📘 ANÁLISIS DE SÍLABOS")
print(f"{'='*80}")

all_required_skills = []
all_topics = []
syllabus_with_skills = 0

for i, syllabus in enumerate(syllabi[:5], 1):
    cycle = syllabus.get('cycle', 'N/A')
    course = syllabus.get('course', 'N/A')
    print(f"\n{i}. {cycle} - {course}")
    print("-" * 80)
    
    req_skills = syllabus.get('entities_required_skills', '')
    topics = syllabus.get('entities_course_topics', '')
    
    req_skills_list = [s.strip() for s in str(req_skills).split(',') if s.strip()]
    topics_list = [t.strip() for t in str(topics).split(',') if t.strip()]
    
    print(f"   🎯 Skills Requeridas ({len(req_skills_list)}): {req_skills_list[:10]}")
    print(f"   📚 Topics ({len(topics_list)}): {topics_list[:10]}")

# Estadísticas agregadas de sílabos
for syllabus in syllabi:
    req_skills = syllabus.get('entities_required_skills', '')
    topics = syllabus.get('entities_course_topics', '')
    
    if req_skills:
        syllabus_with_skills += 1
        all_required_skills.extend([s.strip() for s in str(req_skills).split(',') if s.strip()])
    
    if topics:
        all_topics.extend([t.strip() for t in str(topics).split(',') if t.strip()])

print(f"\n{'='*80}")
print("📊 ESTADÍSTICAS AGREGADAS - TODOS LOS SÍLABOS")
print(f"{'='*80}")

print(f"\n✅ Cobertura de extracción NER:")
print(f"   Sílabos con skills requeridas: {syllabus_with_skills}/{len(syllabi)} ({syllabus_with_skills/len(syllabi)*100 if syllabi else 0:.1f}%)")

if all_required_skills:
    req_skill_counts = Counter(all_required_skills)
    print(f"\n🎯 Top 15 Skills Requeridas en Sílabos:")
    for skill, count in req_skill_counts.most_common(15):
        print(f"   {skill:30s} → {count:2d} cursos")
else:
    print(f"\n   ❌ NO se encontraron skills requeridas")

if all_topics:
    topic_counts = Counter(all_topics)
    print(f"\n📚 Top 15 Topics más comunes:")
    for topic, count in topic_counts.most_common(15):
        print(f"   {topic:40s} → {count:2d} cursos")

# Análisis de overlap
print(f"\n{'='*80}")
print("🎯 ANÁLISIS DE MATCHING POTENCIAL")
print(f"{'='*80}")

cv_skills_set = set([s.lower() for s in all_cv_skills])
required_skills_set = set([s.lower() for s in all_required_skills])
overlap = cv_skills_set.intersection(required_skills_set)

print(f"\n🔍 Overlap entre Skills de CVs y Sílabos:")
print(f"   Skills únicas en CVs: {len(cv_skills_set)}")
print(f"   Skills únicas requeridas en Sílabos: {len(required_skills_set)}")
print(f"   Skills en común: {len(overlap)}")

if overlap:
    print(f"   \n✅ Skills compartidas: {sorted(list(overlap))}")
else:
    print(f"   \n⚠️  NO hay overlap entre skills de CVs y Sílabos")

if len(required_skills_set) > 0:
    coverage = len(overlap) / len(required_skills_set) * 100
    print(f"\n   📊 Cobertura: {coverage:.1f}% de skills requeridas están en CVs")

# Diagnóstico final
print(f"\n{'='*80}")
print("🏥 DIAGNÓSTICO DE CALIDAD")
print(f"{'='*80}")

issues = []
warnings = []
successes = []

# Verificar CVs
if cv_with_skills == 0:
    issues.append("❌ CRÍTICO: Ningún CV tiene skills técnicas extraídas")
elif cv_with_skills < len(cvs) * 0.5:
    warnings.append(f"⚠️  Solo {cv_with_skills}/{len(cvs)} CVs tienen skills (< 50%)")
else:
    successes.append(f"✅ {cv_with_skills}/{len(cvs)} CVs tienen skills extraídas")

if cv_with_exp == 0:
    issues.append("❌ CRÍTICO: Ningún CV tiene años de experiencia extraídos")
elif cv_with_exp < len(cvs) * 0.5:
    warnings.append(f"⚠️  Solo {cv_with_exp}/{len(cvs)} CVs tienen experiencia (< 50%)")
else:
    successes.append(f"✅ {cv_with_exp}/{len(cvs)} CVs tienen experiencia extraída")

# Verificar Sílabos
if syllabus_with_skills == 0:
    issues.append("❌ CRÍTICO: Ningún sílabo tiene skills requeridas extraídas")
elif syllabus_with_skills < len(syllabi) * 0.5:
    warnings.append(f"⚠️  Solo {syllabus_with_skills}/{len(syllabi)} sílabos tienen skills (< 50%)")
else:
    successes.append(f"✅ {syllabus_with_skills}/{len(syllabi)} sílabos tienen skills extraídas")

# Verificar overlap
if len(overlap) == 0 and len(cv_skills_set) > 0 and len(required_skills_set) > 0:
    issues.append("🔴 CRÍTICO: Cero overlap entre skills - matching NER será inútil")
elif len(overlap) < 3:
    warnings.append(f"⚠️  Muy poco overlap ({len(overlap)} skills) - matching NER será débil")
else:
    successes.append(f"✅ Hay {len(overlap)} skills en común - matching NER funcional")

print(f"\n✅ ÉXITOS:")
for success in successes:
    print(f"   {success}")

print(f"\n⚠️  ADVERTENCIAS:")
if warnings:
    for warning in warnings:
        print(f"   {warning}")
else:
    print(f"   Ninguna")

print(f"\n❌ PROBLEMAS CRÍTICOS:")
if issues:
    for issue in issues:
        print(f"   {issue}")
else:
    print(f"   Ninguno")

# Recomendaciones
print(f"\n{'='*80}")
print("💡 RECOMENDACIONES")
print(f"{'='*80}")

if len(overlap) < 5:
    print("""
1. 🔴 PRIORIDAD ALTA: Bajo overlap entre CVs y Sílabos
   → El matching dependerá PRINCIPALMENTE de SBERT (similitud semántica)
   → NER aporta poco al score (solo 60% que casi no se usa)
   
   ACCIONES:
   - Ajustar pesos: SBERT 70%, NER 30%
   - O mejorar diccionario de skills en ner_service.py
   - Agregar sinónimos y variantes (ej: 'js', 'javascript', 'JavaScript')
""")

if cv_with_skills < len(cvs) * 0.7:
    print("""
2. ⚠️  Extracción de skills de CVs es baja
   → Revisar patrones en ner_service.py
   → Los CVs pueden usar términos no contemplados
   → Considerar técnicas de keyword extraction automática
""")

if len(all_cv_skills) > 0:
    print(f"""
3. ✅ Se están extrayendo algunas skills ({len(all_cv_skills)} total)
   → Top skills: {', '.join([s for s, _ in Counter(all_cv_skills).most_common(5)])}
   → Verificar si son relevantes para los cursos
""")

conn.close()

print(f"\n{'='*80}")
print("✅ Análisis completado")
print(f"{'='*80}")
