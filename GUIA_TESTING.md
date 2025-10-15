# 🧪 Guía de Testing - Sistema Híbrido

## ✅ Tests Implementados

Tienes 3 scripts de testing:

1. **`test_sql_init.py`** - Test simple de inicialización
2. **`test_hybrid_system.py`** - Test completo del sistema
3. **`test_embeddings.py`** - Test de embeddings (ya existía)

---

## 📋 Procedimiento de Testing

### **PASO 1: Test de Inicialización**

Ejecuta en el terminal (Fish shell):

```fish
cd /home/jeff/Documentos/TALLER/backend
python test_sql_init.py
```

**Output esperado:**
```
🧪 TEST DE INICIALIZACIÓN SQL DATABASE
============================================================

1️⃣ Importando SQLDatabaseService...
   ✅ Import exitoso

2️⃣ Inicializando servicio SQL...
✅ SQL Database inicializada: sqlite:////path/to/metadata.db
   ✅ Servicio inicializado

3️⃣ Verificando base de datos...
   ✅ Estadísticas obtenidas:
      - Teachers: 0
      - Courses: 0
      - Skills: 0
      - Matches: 0

4️⃣ Verificando archivo metadata.db...
   ✅ Archivo existe: /home/jeff/Documentos/TALLER/backend/metadata.db
   ✅ Tamaño: 16384 bytes

============================================================
✅ TODOS LOS TESTS PASARON

Próximos pasos:
  1. Iniciar backend: uvicorn app.main:app --reload
  2. Hacer sync de datos desde frontend
  3. Ejecutar: python test_hybrid_system.py
============================================================
```

**Si falla:**
- Verifica que SQLAlchemy esté instalado: `pip list | grep -i sqlalchemy`
- Verifica permisos de escritura en `/home/jeff/Documentos/TALLER/backend/`

---

### **PASO 2: Iniciar Backend**

```fish
cd /home/jeff/Documentos/TALLER/backend
uvicorn app.main:app --reload --port 8000
```

**Output esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
✅ SQL Database inicializada: sqlite:///...
INFO:     Application startup complete.
```

**Verifica que veas:**
- ✅ Línea: `SQL Database inicializada`
- ✅ Archivo creado: `backend/metadata.db`

---

### **PASO 3: Sincronizar Datos**

#### **Opción A: Desde Frontend**

1. Abre el frontend en el navegador
2. Ve a **Configuración** (⚙️)
3. Ingresa los IDs de las carpetas de Drive:
   - CV Folder ID
   - Syllabus Folder ID
4. Click en **"Sincronizar"**

#### **Opción B: Con cURL**

```fish
curl -X POST http://localhost:8000/api/sync \
  -H "Content-Type: application/json" \
  -d '{
    "cv_folder_id": "TU_CV_FOLDER_ID",
    "syllabus_folder_id": "TU_SYLLABUS_FOLDER_ID"
  }'
```

**Output esperado en los logs del backend:**
```
Procesando: Juan_CV.pdf (1abc...)
  -> ✅ Teacher guardado en SQL (ID: 1) con 5 skills
  -> ✅ Procesado y guardado en ChromaDB + SQL con entidades extraídas.

Procesando: Desarrollo_Web.pdf (2xyz...)
  -> ✅ Course guardado en SQL (ID: 1) con 4 required skills
  -> ✅ Procesado y guardado en ChromaDB + SQL con entidades extraídas.
```

---

### **PASO 4: Test del Sistema Híbrido**

**En otra terminal (manteniendo el backend corriendo):**

```fish
cd /home/jeff/Documentos/TALLER/backend
python test_hybrid_system.py
```

**Output esperado:**
```
======================================================================
🧪 PRUEBA DE ARQUITECTURA HÍBRIDA SQL + ChromaDB
======================================================================

📊 TEST 1: Estadísticas de SQL Database
----------------------------------------------------------------------
✅ Total Teachers: 15
✅ Total Courses: 8
✅ Total Skills: 42
✅ Total Matches Realizados: 0

📋 Top 5 Skills Más Requeridas:
   - python: 6 cursos
   - javascript: 4 cursos
   - sql: 3 cursos
   - docker: 2 cursos
   - git: 2 cursos

👨‍🏫 Top 5 Skills de Docentes:
   - python: 12 docentes
   - git: 10 docentes
   - docker: 7 docentes
   - javascript: 6 docentes
   - mysql: 5 docentes


💾 TEST 2: Estadísticas de ChromaDB
----------------------------------------------------------------------
✅ Total CVs: 15
✅ Total Sílabos: 8


🔄 TEST 3: Verificación de Sincronización
----------------------------------------------------------------------
✅ Teachers en SQL: 15
   ✅ Juan Pérez: 5 skills en SQL, embedding en ChromaDB
   ✅ María González: 7 skills en SQL, embedding en ChromaDB
   ...

📈 Sincronización: 15/15 verificados


🔍 TEST 4: Búsqueda Híbrida por Skills
----------------------------------------------------------------------
Curso de prueba: Desarrollo Web
Required skills: ['python', 'django', 'postgresql', 'docker']

✅ Encontrados 5 candidatos con al menos 1 skill

   1. Juan Pérez
      - Matched Skills: ['python', 'django', 'postgresql']
      - Missing Skills: ['docker']
      - SQL Score: 75.00%
      - Experiencia: 5 años

   2. María González
      - Matched Skills: ['python', 'django']
      - Missing Skills: ['postgresql', 'docker']
      - SQL Score: 50.00%
      - Experiencia: 3 años

   ...


======================================================================
📋 RESUMEN DE LA ARQUITECTURA
======================================================================
✅ SQL Database: FUNCIONANDO
✅ ChromaDB: FUNCIONANDO
✅ Sincronización: OK

🎉 La arquitectura híbrida está lista para usarse!

Próximos pasos:
  1. Usa el endpoint /recommendations/generate-hybrid para matching
  2. Compara resultados con /recommendations/generate (antiguo)
  3. El nuevo sistema combina: 40% SQL + 60% Semántico
======================================================================
```

---

### **PASO 5: Probar Endpoint Híbrido**

#### **Opción A: Desde Frontend**

1. En el frontend, selecciona un ciclo y curso
2. Click en **"Generar Recomendaciones"**
3. El sistema usará automáticamente el endpoint híbrido

#### **Opción B: Con cURL**

```fish
curl -X POST http://localhost:8000/api/recommendations/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_name": "Ciclo 1",
    "course_name": "Desarrollo Web"
  }' | python -m json.tool
```

**Output esperado:**
```json
{
  "cycle_name": "Ciclo 1",
  "course_name": "Desarrollo Web",
  "matching_method": "hybrid_sql_chromadb",
  "syllabus_info": {
    "name": "Desarrollo Web",
    "cycle": "Ciclo 1",
    "required_skills": ["python", "django", "postgresql", "docker"]
  },
  "recommendations": [
    {
      "teacher_name": "Juan Pérez",
      "cv_filename": "Juan_CV.pdf",
      "score": 0.856,
      "component_scores": {
        "sql_score": 0.75,
        "semantic_similarity": 0.92,
        "matched_skills_count": 3,
        "total_required_skills": 4
      },
      "explanation": {
        "matched_skills": ["python", "django", "postgresql"],
        "missing_skills": ["docker"],
        "teacher_skills": ["python", "django", "postgresql", "git", "linux"],
        "experience_years": 5
      }
    }
  ],
  "total_analyzed": 5,
  "weights": {
    "sql_skill_match": "40%",
    "semantic_similarity": "60%"
  }
}
```

---

### **PASO 6: Ver Estadísticas del Sistema**

```fish
curl http://localhost:8000/api/recommendations/stats | python -m json.tool
```

**Output esperado:**
```json
{
  "sql_database": {
    "total_teachers": 15,
    "total_courses": 8,
    "total_skills": 42,
    "total_matches_performed": 12,
    "top_required_skills": [
      {"skill": "python", "courses": 6},
      {"skill": "javascript", "courses": 4}
    ],
    "top_teacher_skills": [
      {"skill": "python", "teachers": 12},
      {"skill": "git", "teachers": 10}
    ]
  },
  "chromadb": {
    "total_cvs": 15,
    "total_syllabi": 8
  }
}
```

---

## 🐛 Troubleshooting

### **Error: "No module named 'sqlalchemy'"**
```fish
pip install sqlalchemy
```

### **Error: "No se encontraron sílabos en la base de datos"**
- Haz sync primero: `POST /api/sync`
- Verifica que las carpetas de Drive tengan PDFs

### **Error: "metadata.db permission denied"**
```fish
chmod 777 /home/jeff/Documentos/TALLER/backend/metadata.db
```

### **Base de datos vacía (0 teachers, 0 courses)**
1. Detén el backend (Ctrl+C)
2. Elimina: `rm metadata.db chroma_db/chroma.sqlite3`
3. Reinicia backend
4. Haz sync de nuevo

---

## 📊 Comparación: Antiguo vs Híbrido

Para ver la diferencia, prueba ambos endpoints con el mismo curso:

```fish
# Antiguo (solo ChromaDB)
curl -X POST http://localhost:8000/api/recommendations/generate \
  -H "Content-Type: application/json" \
  -d '{"cycle_name": "Ciclo 1", "course_name": "Desarrollo Web"}'

# Nuevo (híbrido SQL + ChromaDB)
curl -X POST http://localhost:8000/api/recommendations/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{"cycle_name": "Ciclo 1", "course_name": "Desarrollo Web"}'
```

**Compara:**
- ✅ Scores (el híbrido debería ser más preciso)
- ✅ Explicaciones (híbrido muestra matched/missing skills)
- ✅ Orden de candidatos (híbrido prioriza skill match)

---

## ✅ Checklist de Testing

- [ ] `test_sql_init.py` pasa sin errores
- [ ] Backend inicia y crea `metadata.db`
- [ ] Sync funciona (logs muestran "guardado en SQL")
- [ ] `test_hybrid_system.py` muestra estadísticas correctas
- [ ] Endpoint `/generate-hybrid` retorna recomendaciones
- [ ] Endpoint `/stats` muestra datos correctos
- [ ] Comparación antiguo vs híbrido muestra mejoras

---

## 📝 Documentar Resultados

Para tu informe académico, captura:

1. **Screenshots:**
   - Output de `test_hybrid_system.py`
   - Response JSON de `/generate-hybrid`
   - Estadísticas de `/stats`

2. **Métricas:**
   - Tiempo de respuesta antiguo vs híbrido
   - Precisión de matching (validar manualmente top 3)
   - Número de skills detectadas vs reales

3. **Comparación:**
   - Tabla: "Antiguo vs Híbrido" con ejemplos reales
   - Gráfico: Distribution de SQL scores vs Semantic scores

---

¡Buena suerte con el testing! 🚀
