#!/usr/bin/env python3
"""
Script simple para inspeccionar directamente ChromaDB sin dependencias complejas.
"""

import sqlite3
import json
import os
from collections import Counter

print("="*80)
print("🔍 INSPECCIÓN DIRECTA DE ChromaDB - Análisis de NER")
print("="*80)

# Ruta a la base de datos SQLite de ChromaDB
db_path = os.path.join(os.getcwd(), 'backend', 'chroma_db', 'chroma.sqlite3')

if not os.path.exists(db_path):
    print(f"\n❌ ERROR: No se encontró la base de datos en: {db_path}")
    print("   Verifica que hayas sincronizado datos primero.")
    exit(1)

print(f"\n✅ Base de datos encontrada: {db_path}")

# Conectar a SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver tablas disponibles
print("\n📊 Tablas en ChromaDB:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"   - {table[0]}")

# Intentar leer metadatos de las colecciones
print("\n" + "="*80)
print("🔍 Estructura de la Base de Datos")
print("="*80)

try:
    # Ver colecciones
    cursor.execute("SELECT * FROM collections")
    collections = cursor.fetchall()
    print(f"\n📁 Colecciones disponibles ({len(collections)}):")
    for col in collections:
        print(f"   ID: {col[0]}, Name: {col[1]}, UUID: {col[2]}")
    
    # Ver embeddings
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]
    print(f"\n💾 Total de embeddings almacenados: {embedding_count}")
    
    # Leer algunos metadatos de ejemplo
    cursor.execute("""
        SELECT e.id, e.collection_uuid, e.embedding_id, c.name, e.document, e.metadata
        FROM embeddings e
        JOIN collections c ON e.collection_uuid = c.uuid
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    print("\n" + "="*80)
    print("📄 MUESTRA DE DOCUMENTOS ALMACENADOS")
    print("="*80)
    
    for i, row in enumerate(rows, 1):
        collection_name = row[3]
        document = row[4] if row[4] else "N/A"
        metadata_str = row[5] if row[5] else "{}"
        
        print(f"\n{i}. Colección: {collection_name}")
        print(f"   Embedding ID: {row[2]}")
        
        # Intentar parsear metadata JSON
        try:
            metadata = json.loads(metadata_str) if metadata_str and metadata_str != "{}" else {}
            
            print(f"   📝 Nombre: {metadata.get('name', 'N/A')}")
            
            # Buscar entidades en metadata
            entities_keys = [k for k in metadata.keys() if k.startswith('entities_')]
            
            if entities_keys:
                print(f"   🧠 Entidades NER encontradas ({len(entities_keys)}):")
                for key in entities_keys[:5]:  # Mostrar primeras 5
                    value = metadata.get(key, '')
                    key_display = key.replace('entities_', '')
                    if isinstance(value, str) and len(value) > 60:
                        value = value[:60] + "..."
                    print(f"      • {key_display}: {value}")
            else:
                print(f"   ⚠️  No se encontraron entidades NER en metadata")
                print(f"   📋 Keys en metadata: {list(metadata.keys())[:10]}")
            
            # Mostrar texto original si existe
            raw_text = metadata.get('raw_text', '')
            if raw_text:
                print(f"   📖 Texto original (100 chars): {raw_text[:100]}...")
                
        except json.JSONDecodeError:
            print(f"   ⚠️  Metadata no es JSON válido")
        except Exception as e:
            print(f"   ⚠️  Error al procesar metadata: {e}")
        
        print("-" * 80)

except sqlite3.Error as e:
    print(f"\n❌ Error de SQL: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")

# Análisis agregado
print("\n" + "="*80)
print("📊 ANÁLISIS AGREGADO")
print("="*80)

try:
    # Contar documentos por colección
    cursor.execute("""
        SELECT c.name, COUNT(e.id)
        FROM collections c
        LEFT JOIN embeddings e ON c.uuid = e.collection_uuid
        GROUP BY c.name
    """)
    
    counts = cursor.fetchall()
    print(f"\n📈 Documentos por colección:")
    for name, count in counts:
        print(f"   {name:20s} → {count:3d} documentos")
    
    # Verificar presencia de entidades NER
    cursor.execute("""
        SELECT c.name, e.metadata
        FROM embeddings e
        JOIN collections c ON e.collection_uuid = c.uuid
    """)
    
    all_rows = cursor.fetchall()
    
    cv_with_skills = 0
    cv_with_exp = 0
    syllabus_with_skills = 0
    all_skills = []
    all_exp = []
    
    for name, metadata_str in all_rows:
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
            
            if name == "cvs":
                skills = metadata.get('entities_technical_skills', '')
                if skills:
                    cv_with_skills += 1
                    all_skills.extend([s.strip() for s in skills.split(',') if s.strip()])
                
                exp = metadata.get('entities_experience_years', '0')
                if exp and exp != '0':
                    cv_with_exp += 1
                    try:
                        all_exp.append(int(exp))
                    except:
                        pass
            
            elif name == "syllabi":
                req_skills = metadata.get('entities_required_skills', '')
                if req_skills:
                    syllabus_with_skills += 1
        except:
            pass
    
    print(f"\n🔍 Calidad de extracción NER:")
    print(f"   CVs con skills: {cv_with_skills}/{len([r for r in all_rows if r[0] == 'cvs'])}")
    print(f"   CVs con experiencia: {cv_with_exp}/{len([r for r in all_rows if r[0] == 'cvs'])}")
    print(f"   Sílabos con skills requeridas: {syllabus_with_skills}/{len([r for r in all_rows if r[0] == 'syllabi'])}")
    
    if all_skills:
        skill_counts = Counter(all_skills)
        print(f"\n🛠️  Top 10 Skills más comunes:")
        for skill, count in skill_counts.most_common(10):
            print(f"      {skill:30s} → {count:2d}x")
    else:
        print(f"\n   ⚠️  No se encontraron skills en los metadatos")
    
    if all_exp:
        avg_exp = sum(all_exp) / len(all_exp)
        print(f"\n💼 Experiencia:")
        print(f"      Promedio: {avg_exp:.1f} años")
        print(f"      Rango: {min(all_exp)} - {max(all_exp)} años")
    
except Exception as e:
    print(f"\n❌ Error en análisis agregado: {e}")

conn.close()

print("\n" + "="*80)
print("✅ Inspección completada")
print("="*80)
