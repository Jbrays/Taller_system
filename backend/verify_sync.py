#!/usr/bin/env python3
"""
Script rápido para verificar que la sincronización híbrida funcionó
"""
import sys
sys.path.append('/home/jeff/Documentos/TALLER/backend')

from app.services.sql_database_service import SQLDatabaseService
from app.services.database_service import get_database

def main():
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN RÁPIDA POST-SYNC")
    print("="*70 + "\n")
    
    # SQL Database
    sql_service = SQLDatabaseService()
    stats = sql_service.get_statistics()
    
    print("📊 SQL Database:")
    print(f"   ✅ Teachers: {stats['total_teachers']}")
    print(f"   ✅ Courses: {stats['total_courses']}")
    print(f"   ✅ Skills únicas: {stats['total_skills']}")
    
    if stats['total_teachers'] > 0:
        print(f"\n   📋 Top 5 Skills más comunes:")
        for i, (skill, count) in enumerate(stats['top_skills'][:5], 1):
            print(f"      {i}. {skill}: {count} veces")
    
    # ChromaDB
    db = get_database()
    cvs_count = db.count_embeddings("cvs")
    syllabi_count = db.count_embeddings("syllabi")
    
    print(f"\n💾 ChromaDB:")
    print(f"   ✅ CVs: {cvs_count}")
    print(f"   ✅ Sílabos: {syllabi_count}")
    
    # Verificación de sincronización
    print(f"\n🔄 Sincronización:")
    if stats['total_teachers'] == cvs_count and stats['total_courses'] == syllabi_count:
        print(f"   ✅ PERFECTA: SQL y ChromaDB sincronizados ({stats['total_teachers']} teachers, {stats['total_courses']} courses)")
    else:
        print(f"   ⚠️  DESAJUSTE: SQL ({stats['total_teachers']} teachers, {stats['total_courses']} courses) != ChromaDB ({cvs_count} CVs, {syllabi_count} sílabos)")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
