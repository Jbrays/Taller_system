# 🔀 Arquitectura Híbrida SQL + ChromaDB

## 📚 ¿Por qué usar dos bases de datos?

### Problema Original
El sistema almacenaba todo en **ChromaDB**, incluyendo skills como strings separados por comas:
```python
metadata = {
    "entities_technical_skills": "python, django, postgresql, docker"
}
```

**Limitaciones:**
- ❌ No se pueden hacer queries relacionales (ej: "todos los docentes con Python Y Django")
- ❌ Skills duplicadas con diferentes escrituras ("javascript" vs "JavaScript" vs "JS")
- ❌ No se puede calcular match de skills de forma precisa
- ❌ Difícil obtener estadísticas (ej: "skill más demandada")

### Solución: Arquitectura Híbrida

Usamos **dos bases de datos complementarias**:

| Base de Datos | Propósito | Qué almacena |
|---------------|-----------|--------------|
| **SQLite** (SQLAlchemy) | Metadata estructurada | Teachers, Courses, Skills (normalizado) |
| **ChromaDB** | Búsqueda semántica | Embeddings de SBERT (vectores 384-dim) |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                     │
│            POST /recommendations/generate-hybrid                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + Python)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         HYBRID MATCHING ALGORITHM                        │  │
│  │                                                          │  │
│  │  1️⃣  SQL: Filtro por skills exactas (40% weight)        │  │
│  │      → find_teachers_by_skills(["python", "django"])    │  │
│  │      → Retorna solo teachers con match                  │  │
│  │                                                          │  │
│  │  2️⃣  ChromaDB: Similitud semántica (60% weight)         │  │
│  │      → Para cada teacher filtrado, calcular:           │  │
│  │      → cosine_similarity(teacher_emb, course_emb)      │  │
│  │                                                          │  │
│  │  3️⃣  Combinar scores:                                   │  │
│  │      → final = 0.4*sql_score + 0.6*semantic_score      │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│         ┌──────────────────┐      ┌──────────────────┐         │
│         │  SQLAlchemy ORM  │      │  ChromaDB Client │         │
│         └────────┬─────────┘      └────────┬─────────┘         │
└──────────────────┼──────────────────────────┼──────────────────┘
                   │                          │
                   ▼                          ▼
        ┌──────────────────┐      ┌──────────────────┐
        │  metadata.db     │      │  chroma_db/      │
        │  (SQLite)        │      │  (Vector Store)  │
        │                  │      │                  │
        │  Tables:         │      │  Collections:    │
        │  - teachers      │      │  - cvs           │
        │  - courses       │      │  - syllabi       │
        │  - skills        │      │                  │
        │  - teacher_skills│      │  Embeddings:     │
        │  - course_reqs   │      │  - 384-dim       │
        │  - matching_hist │      │  - normalized    │
        └──────────────────┘      └──────────────────┘
```

---

## 📊 Esquema de Base de Datos SQL

### Tabla: `teachers`
```sql
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    embedding_id VARCHAR(255) UNIQUE,  -- ID del embedding en ChromaDB
    experience_years INTEGER DEFAULT 0,
    email VARCHAR(255)
);
```

### Tabla: `skills`
```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- normalizado (lowercase)
    category VARCHAR(50)  -- language, framework, database, etc.
);
```

### Tabla: `courses`
```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cycle VARCHAR(50),
    embedding_id VARCHAR(255) UNIQUE,
    credits INTEGER
);
```

### Tabla Junction: `teacher_skills` (Many-to-Many)
```sql
CREATE TABLE teacher_skills (
    teacher_id INTEGER REFERENCES teachers(id),
    skill_id INTEGER REFERENCES skills(id),
    proficiency_level VARCHAR(50),  -- basic, intermediate, advanced
    PRIMARY KEY (teacher_id, skill_id)
);
```

### Tabla Junction: `course_requirements` (Many-to-Many)
```sql
CREATE TABLE course_requirements (
    course_id INTEGER REFERENCES courses(id),
    skill_id INTEGER REFERENCES skills(id),
    importance VARCHAR(50),  -- required, preferred, optional
    PRIMARY KEY (course_id, skill_id)
);
```

### Tabla: `matching_results` (Historial)
```sql
CREATE TABLE matching_results (
    id INTEGER PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id),
    course_id INTEGER REFERENCES courses(id),
    sql_score FLOAT,
    semantic_score FLOAT,
    final_score FLOAT,
    matched_skills_count INTEGER,
    created_at TIMESTAMP
);
```

---

## 🔄 Flujo de Sincronización

### POST `/sync`

```python
# 1. Usuario sube CV a Drive → Endpoint recibe file_id
# 2. Descargar PDF y extraer texto
text = pdf_service.extract_text_from_pdf(content)

# 3. Procesar con NLP
embedding = nlp_service.generate_embedding(text)  # SBERT 384-dim
entities = ner_service.extract_entities_from_cv(text)  # spaCy NER

# 4. Guardar en ChromaDB (embedding vectorial)
db_service.add_embedding("cvs", embedding, file_id, metadata)

# 5. Guardar en SQL (metadata estructurada)
teacher_id = sql_db_service.add_teacher(
    name=file_name.replace('.pdf', ''),
    embedding_id=file_id,
    skills_list=entities['technical_skills'],  # ["python", "django", "postgresql"]
    experience_years=entities['experience_years']
)
```

**Resultado:**
- ✅ Vector en ChromaDB para búsqueda semántica
- ✅ Metadata estructurada en SQL para queries relacionales
- ✅ `embedding_id` vincula ambas bases de datos

---

## 🎯 Flujo de Matching Híbrido

### POST `/recommendations/generate-hybrid`

```python
# PASO 1: Obtener required_skills del curso (SQL)
course = sql_db.get_course_by_name("Desarrollo Web")
required_skills = ["python", "django", "postgresql", "docker"]

# PASO 2: Filtrar candidatos con SQL (al menos 1 skill)
candidates = sql_db.find_teachers_by_skills(required_skills, min_matches=1)
# Retorna: [(Teacher(id=1, name="Juan"), matches=3), ...]

# PASO 3: Para cada candidato, calcular scores
for teacher, match_count in candidates:
    
    # 3a. SQL Score (porcentaje de skills que coinciden)
    sql_score = match_count / len(required_skills)
    # Ej: 3 matches / 4 required = 0.75
    
    # 3b. Semantic Score (similitud de embeddings)
    teacher_embedding = chromadb.get_embedding(teacher.embedding_id)
    course_embedding = chromadb.get_embedding(course.embedding_id)
    semantic_score = cosine_similarity(teacher_embedding, course_embedding)
    # Ej: 0.82 (similitud semántica)
    
    # 3c. Final Score (combinado)
    final_score = (0.4 * sql_score) + (0.6 * semantic_score)
    # Ej: (0.4 * 0.75) + (0.6 * 0.82) = 0.792

# PASO 4: Ordenar por final_score y retornar top 10
```

**Ventajas:**
- ✅ **Precisión:** Skills exactas + contexto semántico
- ✅ **Velocidad:** SQL filtra primero (menos cálculos vectoriales)
- ✅ **Transparencia:** Sabemos qué skills coinciden exactamente
- ✅ **Historial:** Guardamos todos los matches en `matching_results`

---

## 📈 Comparación: Antiguo vs. Híbrido

| Aspecto | Sistema Antiguo (Solo ChromaDB) | Sistema Híbrido (SQL + ChromaDB) |
|---------|----------------------------------|----------------------------------|
| **Precisión de skills** | ❌ Baja (strings separados por comas) | ✅ Alta (tabla normalizada) |
| **Queries complejas** | ❌ No soportadas | ✅ SQL con JOINs |
| **Duplicados** | ❌ "python" vs "Python" vs "py" | ✅ Normalizados a lowercase |
| **Estadísticas** | ❌ Difícil calcular | ✅ SQL agregaciones |
| **Matching transparente** | ❌ Solo similarity score | ✅ Skills exactas + semántica |
| **Velocidad** | ⚠️ Calcula todo con vectores | ✅ SQL filtra primero |

---

## 🧪 Pruebas del Sistema

### 1. Verificar sincronización
```bash
cd backend
python test_hybrid_system.py
```

**Output esperado:**
```
✅ Total Teachers: 15
✅ Total Courses: 8
✅ Total Skills: 42
✅ Sincronización: 15/15 verificados
🎉 La arquitectura híbrida está lista para usarse!
```

### 2. Probar endpoint híbrido
```bash
curl -X POST http://localhost:8000/api/recommendations/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_name": "Ciclo 1",
    "course_name": "Desarrollo Web"
  }'
```

**Response esperado:**
```json
{
  "matching_method": "hybrid_sql_chromadb",
  "recommendations": [
    {
      "teacher_name": "Juan Pérez",
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
        "experience_years": 5
      }
    }
  ],
  "weights": {
    "sql_skill_match": "40%",
    "semantic_similarity": "60%"
  }
}
```

---

## 🔧 Configuración

### Requisitos
```txt
sqlalchemy==2.0.25
chromadb==0.4.22
sentence-transformers==2.3.1
fastapi==0.109.0
```

### Variables de Entorno
```env
# No necesarias para SQLite, ya que se crea localmente
# Ubicación: backend/metadata.db
```

### Inicialización Automática
```python
# Las tablas se crean automáticamente al iniciar el servicio
sql_db = SQLDatabaseService()  # Crea metadata.db si no existe
```

---

## 📊 Estadísticas del Sistema

### GET `/recommendations/stats`

```json
{
  "sql_database": {
    "total_teachers": 15,
    "total_courses": 8,
    "total_skills": 42,
    "total_matches_performed": 127,
    "top_required_skills": [
      {"skill": "python", "courses": 6},
      {"skill": "javascript", "courses": 4},
      {"skill": "sql", "courses": 3}
    ],
    "top_teacher_skills": [
      {"skill": "python", "teachers": 12},
      {"skill": "git", "teachers": 10},
      {"skill": "docker", "teachers": 7}
    ]
  },
  "chromadb": {
    "total_cvs": 15,
    "total_syllabi": 8
  }
}
```

---

## 🚀 Ventajas de esta Arquitectura

### Para el Usuario
- ✅ **Resultados más precisos:** Combina skills exactas + contexto semántico
- ✅ **Transparencia:** Ve qué skills coinciden y cuáles faltan
- ✅ **Velocidad:** Respuestas más rápidas (SQL filtra primero)

### Para el Desarrollador
- ✅ **Mantenibilidad:** Código modular (`sql_database_service.py`)
- ✅ **Escalabilidad:** SQL puede migrar a PostgreSQL sin cambiar código
- ✅ **Debugging:** Queries SQL más fáciles de entender que vectores
- ✅ **Estadísticas:** Reportes y dashboards con SQL

### Para el Proyecto Académico
- ✅ **Aprendizaje:** Entiende diferencia entre DB relacionales y vectoriales
- ✅ **Profesional:** Arquitectura usada en sistemas reales de producción
- ✅ **Documentable:** Fácil explicar en el informe técnico

---

## 🔮 Mejoras Futuras

1. **PostgreSQL en producción**
   - Cambiar de SQLite a PostgreSQL para concurrencia
   - Solo cambiar connection string, código permanece igual

2. **Fuzzy matching de skills**
   - Agregar columna `aliases` en tabla `skills`
   - Ejemplo: "js" → "javascript", "py" → "python"

3. **Machine Learning en SQL**
   - Tabla `skill_importance_weights` aprendidos de histórico
   - Ajustar pesos dinámicamente: 40% SQL → 45% si skills críticas

4. **Cache de resultados**
   - Guardar top 10 en tabla `cached_recommendations`
   - TTL de 1 hora para evitar recalcular

5. **API de estadísticas**
   - Dashboard con métricas: "skill gap" (skills faltantes en docentes)
   - Gráficos con Chart.js en frontend

---

## 📚 Referencias

- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/
- **ChromaDB:** https://docs.trychroma.com/
- **Sentence-BERT:** https://www.sbert.net/
- **Hybrid Search:** https://www.pinecone.io/learn/hybrid-search/

---

## 👨‍💻 Autor

Sistema desarrollado como proyecto académico.  
Arquitectura híbrida implementada para mejorar precisión de matching.

**Fecha:** 2024  
**Stack:** Python + FastAPI + SQLAlchemy + ChromaDB + React
