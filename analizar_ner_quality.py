"""
Script de análisis para verificar la calidad de extracción de NER.
Muestra qué entidades está extrayendo el sistema y evalúa su relevancia.
"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import chromadb
import json
from collections import Counter

print("="*80)
print("🔍 ANÁLISIS DE CALIDAD DE NER - Sistema de Emparejamiento")
print("="*80)

# Conectar directamente a ChromaDB
db_path = os.path.join(os.getcwd(), 'backend', 'chroma_db')
client = chromadb.PersistentClient(path=db_path)
cv_collection = client.get_collection(name="cvs")
syllabus_collection = client.get_collection(name="syllabi")

# Obtener todos los CVs de la base de datos
print("\n📄 Cargando CVs desde ChromaDB...")
cv_data = cv_collection.get(include=["metadatas"])
cv_metadatas = cv_data['metadatas']
print(f"✅ {len(cv_metadatas)} CVs cargados")

# Obtener todos los sílabos
print("\n📘 Cargando Sílabos desde ChromaDB...")
syllabus_data = syllabus_collection.get(include=["metadatas"])
syllabus_metadatas = syllabus_data['metadatas']
print(f"✅ {len(syllabus_metadatas)} Sílabos cargados")

print("\n" + "="*80)
print("📊 ANÁLISIS DE CVs")
print("="*80)

# Analizar CVs
all_skills_cv = []
all_experience = []
all_education = []
all_certs = []

for i, metadata in enumerate(cv_metadatas[:5], 1):  # Primeros 5 para muestra
    print(f"\n{i}. CV: {metadata.get('name', 'Sin nombre')}")
    print("-" * 80)
    
    # Extraer entidades (están aplanadas en metadata)
    skills_str = metadata.get('entities_technical_skills', '')
    exp_years = metadata.get('entities_experience_years', '0')
    education_str = metadata.get('entities_education', '')
    certs_str = metadata.get('entities_certifications', '')
    
    # Parsear strings a listas
    skills = [s.strip() for s in skills_str.split(',') if s.strip()] if skills_str else []
    education = [e.strip() for e in education_str.split(',') if e.strip()] if education_str else []
    certs = [c.strip() for c in certs_str.split(',') if c.strip()] if certs_str else []
    
    print(f"   🛠️  Habilidades Técnicas ({len(skills)}): {skills[:10]}")
    print(f"   💼 Años de Experiencia: {exp_years}")
    print(f"   🎓 Educación ({len(education)}): {education[:5]}")
    print(f"   📜 Certificaciones ({len(certs)}): {certs[:5]}")
    
    # Verificar si hay raw_text para análisis manual
    raw_text = metadata.get('raw_text', '')
    if raw_text:
        print(f"   📝 Texto original (primeros 200 chars):")
        print(f"      {raw_text[:200]}...")
    
    all_skills_cv.extend(skills)
    try:
        all_experience.append(int(exp_years))
    except:
        pass
    all_education.extend(education)
    all_certs.extend(certs)

# Estadísticas agregadas de CVs
print("\n" + "="*80)
print("📈 ESTADÍSTICAS AGREGADAS - CVs")
print("="*80)

if all_skills_cv:
    skill_counts = Counter(all_skills_cv)
    print(f"\n🛠️  Top 15 Habilidades Más Comunes:")
    for skill, count in skill_counts.most_common(15):
        print(f"   {skill:30s} → {count:2d} CVs")
else:
    print("   ⚠️  No se encontraron habilidades técnicas")

if all_experience:
    avg_exp = sum(all_experience) / len(all_experience)
    print(f"\n💼 Experiencia:")
    print(f"   Promedio: {avg_exp:.1f} años")
    print(f"   Mínimo: {min(all_experience)} años")
    print(f"   Máximo: {max(all_experience)} años")
else:
    print("   ⚠️  No se encontraron años de experiencia")

if all_education:
    edu_counts = Counter(all_education)
    print(f"\n🎓 Top 10 Instituciones Educativas:")
    for edu, count in edu_counts.most_common(10):
        print(f"   {edu:40s} → {count:2d} CVs")
else:
    print("   ⚠️  No se encontraron instituciones educativas")

if all_certs:
    cert_counts = Counter(all_certs)
    print(f"\n📜 Top 10 Certificaciones:")
    for cert, count in cert_counts.most_common(10):
        print(f"   {cert:40s} → {count:2d} CVs")
else:
    print("   ⚠️  No se encontraron certificaciones")

print("\n" + "="*80)
print("📊 ANÁLISIS DE SÍLABOS")
print("="*80)

# Analizar Sílabos
all_required_skills = []
all_topics = []
all_prereqs = []

for i, metadata in enumerate(syllabus_metadatas[:5], 1):  # Primeros 5 para muestra
    cycle = metadata.get('cycle', 'N/A')
    course = metadata.get('course', 'N/A')
    print(f"\n{i}. Sílabo: {cycle} - {course}")
    print("-" * 80)
    
    # Extraer entidades
    req_skills_str = metadata.get('entities_required_skills', '')
    topics_str = metadata.get('entities_course_topics', '')
    prereqs_str = metadata.get('entities_prerequisites', '')
    
    req_skills = [s.strip() for s in req_skills_str.split(',') if s.strip()] if req_skills_str else []
    topics = [t.strip() for t in topics_str.split(',') if t.strip()] if topics_str else []
    prereqs = [p.strip() for p in prereqs_str.split(',') if p.strip()] if prereqs_str else []
    
    print(f"   🎯 Skills Requeridas ({len(req_skills)}): {req_skills[:10]}")
    print(f"   📚 Topics del Curso ({len(topics)}): {topics[:10]}")
    print(f"   📋 Prerequisitos ({len(prereqs)}): {prereqs[:5]}")
    
    # Verificar texto original
    raw_text = metadata.get('raw_text', '')
    if raw_text:
        print(f"   📝 Texto original (primeros 200 chars):")
        print(f"      {raw_text[:200]}...")
    
    all_required_skills.extend(req_skills)
    all_topics.extend(topics)
    all_prereqs.extend(prereqs)

# Estadísticas agregadas de Sílabos
print("\n" + "="*80)
print("📈 ESTADÍSTICAS AGREGADAS - Sílabos")
print("="*80)

if all_required_skills:
    skill_counts = Counter(all_required_skills)
    print(f"\n🎯 Top 15 Skills Más Requeridas:")
    for skill, count in skill_counts.most_common(15):
        print(f"   {skill:30s} → {count:2d} cursos")
else:
    print("   ⚠️  No se encontraron skills requeridas")

if all_topics:
    topic_counts = Counter(all_topics)
    print(f"\n📚 Top 15 Topics Más Comunes:")
    for topic, count in topic_counts.most_common(15):
        print(f"   {topic:40s} → {count:2d} cursos")
else:
    print("   ⚠️  No se encontraron topics de curso")

print("\n" + "="*80)
print("🎯 ANÁLISIS DE MATCHING POTENCIAL")
print("="*80)

# Análisis de overlap entre CV skills y required skills
cv_skills_set = set(all_skills_cv)
required_skills_set = set(all_required_skills)
overlap = cv_skills_set.intersection(required_skills_set)

print(f"\n🔍 Overlap entre Skills de CVs y Skills Requeridas:")
print(f"   Skills únicas en CVs: {len(cv_skills_set)}")
print(f"   Skills únicas requeridas: {len(required_skills_set)}")
print(f"   Skills en común: {len(overlap)}")
if overlap:
    print(f"   Skills compartidas: {sorted(list(overlap))[:15]}")

if len(required_skills_set) > 0:
    coverage = len(overlap) / len(required_skills_set) * 100
    print(f"\n   📊 Cobertura: {coverage:.1f}% de skills requeridas están en CVs")
else:
    print(f"\n   ⚠️  No hay skills requeridas para calcular cobertura")

print("\n" + "="*80)
print("⚠️  PROBLEMAS POTENCIALES DETECTADOS")
print("="*80)

issues = []

if not all_skills_cv:
    issues.append("❌ NO se están extrayendo habilidades técnicas de los CVs")
elif len(all_skills_cv) < len(cv_metadatas):
    issues.append(f"⚠️  Solo {len(all_skills_cv)} skills para {len(cv_metadatas)} CVs (promedio muy bajo)")

if not all_required_skills:
    issues.append("❌ NO se están extrayendo skills requeridas de los sílabos")

if not all_experience or all(exp == 0 for exp in all_experience):
    issues.append("❌ NO se están extrayendo años de experiencia correctamente")

if len(overlap) == 0 and len(cv_skills_set) > 0 and len(required_skills_set) > 0:
    issues.append("🔴 CRÍTICO: Cero overlap entre skills de CVs y sílabos - matching será pobre")

if not all_education:
    issues.append("⚠️  No se está extrayendo información educativa")

if issues:
    for issue in issues:
        print(f"\n   {issue}")
else:
    print("\n   ✅ No se detectaron problemas mayores")

print("\n" + "="*80)
print("💡 RECOMENDACIONES")
print("="*80)

print("""
1. Si hay skills con overlap bajo:
   - Verificar patrones en ner_service.py
   - Agregar sinónimos (ej: 'js' → 'javascript')
   - Considerar normalización (lowercase, stemming)

2. Si no hay años de experiencia:
   - Revisar patrones regex en _extract_experience_years()
   - Verificar que CVs mencionen experiencia explícitamente

3. Si no hay overlap entre CVs y sílabos:
   - Verificar que ambos usan mismo vocabulario
   - Considerar usar SBERT principalmente (ya captura sinónimos)
   
4. Para mejorar matching:
   - Ajustar pesos: más SBERT si NER es débil
   - Expandir diccionario de technical_skills
   - Usar embeddings de skills individuales
""")

print("\n" + "="*80)
print("✅ Análisis completado")
print("="*80)
