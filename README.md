# Sistema de Emparejamiento Docente-Curso 🎓

Sistema inteligente para recomendar docentes ideales para cursos académicos basado en análisis de CVs y sílabos usando técnicas de procesamiento de lenguaje natural.

## 🆕 Nueva Arquitectura Híbrida (SQL + Vectorial)

```
┌────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                        │
│                 /generate-hybrid endpoint                  │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────┐
│               BACKEND (FastAPI + Python)                   │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         HYBRID MATCHING ALGORITHM                    │ │
│  │                                                      │ │
│  │  1️⃣  SQL: Filter by exact skills (40% weight)      │ │
│  │  2️⃣  ChromaDB: Semantic similarity (60% weight)    │ │
│  │  3️⃣  Combine: final_score = 0.4*sql + 0.6*sbert   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│      ┌─────────────────┐       ┌─────────────────┐        │
│      │  SQLAlchemy ORM │       │  ChromaDB       │        │
│      └────────┬─────────┘       └────────┬────────┘        │
└───────────────┼──────────────────────────┼─────────────────┘
                │                          │
                ▼                          ▼
     ┌──────────────────┐      ┌──────────────────┐
     │  metadata.db     │      │  chroma_db/      │
     │  (SQLite)        │      │  (Vectors)       │
     │                  │      │                  │
     │  • teachers      │      │  • cvs           │
     │  • courses       │      │  • syllabi       │
     │  • skills        │      │  • embeddings    │
     │  • matching_hist │      │    (384-dim)     │
     └──────────────────┘      └──────────────────┘
```

## 🚀 Características

- **🔀 Arquitectura Híbrida**: Combina SQL (skills exactas) + ChromaDB (semántica)
- **🎯 Matching Preciso**: 40% coincidencia de skills + 60% similitud SBERT
- **📊 Estadísticas**: Top skills, skill gaps, historial de matches
- **🤖 NER Avanzado**: Extracción de entidades con spaCy
- **☁️ Google Drive**: Sincronización automática de documentos
- **⚡ API REST**: FastAPI con endpoints documentados
- **💅 Interfaz Moderna**: React 19 + Vite

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM para metadata estructurada
- **ChromaDB** - Base de datos vectorial
- **SBERT** - Embeddings semánticos (paraphrase-multilingual-MiniLM-L12-v2)
- **spaCy** - Named Entity Recognition
- **Google Drive API** - Gestión de documentos

### Frontend
- **React 19.2.0** - UI framework
- **Vite 7.1.9** - Build tool
- **Axios** - HTTP client

## 📦 Estructura del Proyecto

```
├── backend/                   # API FastAPI
│   ├── app/
│   │   ├── models/           # 🆕 Pydantic + SQLAlchemy models
│   │   │   ├── db_models.py          # SQLAlchemy ORM
│   │   │   ├── sync_models.py        # Sync schemas
│   │   │   ├── recommendation_models.py
│   │   │   └── common_models.py
│   │   ├── routes/           # API endpoints
│   │   │   ├── sync.py              # Sync Drive → SQL + ChromaDB
│   │   │   ├── recommendations.py   # 🆕 Hybrid matching
│   │   │   └── auto_sync.py
│   │   ├── services/         # Business logic
│   │   │   ├── sql_database_service.py  # 🆕 SQL CRUD
│   │   │   ├── database_service.py      # ChromaDB
│   │   │   ├── nlp_service.py           # SBERT embeddings
│   │   │   ├── ner_service.py           # spaCy NER
│   │   │   ├── advanced_matching_service.py
│   │   │   ├── drive_service.py
│   │   │   └── pdf_service.py
│   │   └── utils/
│   ├── chroma_db/            # ChromaDB storage
│   ├── metadata.db           # 🆕 SQLite database
│   ├── test_hybrid_system.py # 🆕 Test script
│   ├── HYBRID_ARCHITECTURE.md # 🆕 Technical docs
│   └── requirements.txt
├── frontend/                  # React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── MainView.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   └── SettingsModal.jsx
│   │   └── services/
│   └── package.json
├── IMPLEMENTACION_COMPLETA.md # 🆕 Implementation guide
├── avances.md                 # Progress document
├── netlify.toml               # Netlify config
└── README.md
```

## 🎯 Endpoints de la API

### Sincronización
- `POST /api/sync` - Sincroniza documentos de Drive a SQL + ChromaDB

### Recomendaciones
- `POST /api/recommendations/generate` - Matching solo con ChromaDB (antiguo)
- `POST /api/recommendations/generate-hybrid` - 🆕 **Matching híbrido** (SQL + ChromaDB)
- `GET /api/recommendations/stats` - 🆕 Estadísticas del sistema

### Auto-Sync
- `POST /api/auto-sync/start` - Inicia sincronización automática
- `POST /api/auto-sync/stop` - Detiene sincronización

## 🚀 Instalación y Uso

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- Cuenta de Google con acceso a Drive API
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/Jbrays/Taller_system.git
cd Taller_system
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo spaCy
python -m spacy download es_core_news_sm

# Configurar credenciales de Google Drive
# Colocar credentials.json en la raíz del proyecto
```

### 3. Iniciar Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

El backend estará disponible en: `http://localhost:8000`  
Documentación Swagger: `http://localhost:8000/docs`

### 4. Verificar Sistema Híbrido
```bash
# Después de hacer sync con datos, ejecutar:
python test_hybrid_system.py
```

**Output esperado:**
```
✅ Total Teachers: 15
✅ Total Courses: 8
✅ Total Skills: 42
🎉 La arquitectura híbrida está lista para usarse!
```

### 5. Configurar Frontend
```bash
cd frontend
npm install

# Editar src/services/api.js para apuntar al backend
# const API_URL = 'http://localhost:8000/api'
```

### 6. Iniciar Frontend
```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## 📖 Uso del Sistema

### Paso 1: Sincronizar Documentos
1. Subir CVs a una carpeta de Google Drive
2. Subir sílabos organizados por ciclo/curso
3. Obtener los IDs de las carpetas
4. Hacer POST a `/api/sync`:

```json
{
  "cv_folder_id": "1abc...xyz",
  "syllabus_folder_id": "2def...uvw"
}
```

### Paso 2: Generar Recomendaciones Híbridas
```bash
curl -X POST http://localhost:8000/api/recommendations/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_name": "Ciclo 1",
    "course_name": "Desarrollo Web"
  }'
```

**Respuesta:**
```json
{
  "matching_method": "hybrid_sql_chromadb",
  "recommendations": [
    {
      "teacher_name": "Juan Pérez",
      "score": 0.856,
      "component_scores": {
        "sql_score": 0.75,
        "semantic_similarity": 0.92
      },
      "explanation": {
        "matched_skills": ["python", "django", "postgresql"],
        "missing_skills": ["docker"]
      }
    }
  ],
  "weights": {
    "sql_skill_match": "40%",
    "semantic_similarity": "60%"
  }
}
```

### Paso 3: Ver Estadísticas
```bash
curl http://localhost:8000/api/recommendations/stats
```

## 📊 Comparación: Antiguo vs Híbrido

| Característica | `/generate` (Antiguo) | `/generate-hybrid` (Nuevo) |
|----------------|----------------------|---------------------------|
| **Método** | Solo ChromaDB | SQL + ChromaDB |
| **Precisión de skills** | ❌ Baja | ✅ Alta |
| **Transparencia** | Solo similarity score | Skills exactas + semántica |
| **Velocidad** | Lenta (calcula todo) | Rápida (SQL filtra primero) |
| **Estadísticas** | ❌ No disponible | ✅ Disponible |
| **Uso recomendado** | Búsqueda exploratoria | Matching de producción |

## 🧪 Testing

### Test de Sistema Híbrido
```bash
cd backend
python test_hybrid_system.py
```

### Test Manual con Postman/curl
Importar colección de Postman desde `docs/postman_collection.json`

## 📚 Documentación Adicional

- **`IMPLEMENTACION_COMPLETA.md`** - Guía completa de la implementación híbrida
- **`backend/HYBRID_ARCHITECTURE.md`** - Documentación técnica detallada
- **`avances.md`** - Documento de avances del proyecto
- **Swagger UI** - `http://localhost:8000/docs`
