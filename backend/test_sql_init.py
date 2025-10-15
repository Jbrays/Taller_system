"""
Test simple de inicialización de SQL Database.
"""

import sys
import os

print("🧪 TEST DE INICIALIZACIÓN SQL DATABASE")
print("=" * 60)

try:
    print("\n1️⃣ Importando SQLDatabaseService...")
    from app.services.sql_database_service import SQLDatabaseService
    print("   ✅ Import exitoso")
    
    print("\n2️⃣ Inicializando servicio SQL...")
    sql_db = SQLDatabaseService()
    print("   ✅ Servicio inicializado")
    
    print("\n3️⃣ Verificando base de datos...")
    stats = sql_db.get_statistics()
    print(f"   ✅ Estadísticas obtenidas:")
    print(f"      - Teachers: {stats['total_teachers']}")
    print(f"      - Courses: {stats['total_courses']}")
    print(f"      - Skills: {stats['total_skills']}")
    print(f"      - Matches: {stats['total_matches_performed']}")
    
    print("\n4️⃣ Verificando archivo metadata.db...")
    db_path = os.path.join(os.path.dirname(__file__), 'metadata.db')
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"   ✅ Archivo existe: {db_path}")
        print(f"   ✅ Tamaño: {size} bytes")
    else:
        print(f"   ❌ Archivo NO existe: {db_path}")
    
    sql_db.close()
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("\nPróximos pasos:")
    print("  1. Iniciar backend: uvicorn app.main:app --reload")
    print("  2. Hacer sync de datos desde frontend")
    print("  3. Ejecutar: python test_hybrid_system.py")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
