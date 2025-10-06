# Sistema de Emparejamiento Docente-Curso

Sistema inteligente para recomendar docentes ideales para cursos académicos basado en análisis de CVs y sílabos usando técnicas de procesamiento de lenguaje natural.

## 🚀 Características

- **Análisis Inteligente**: Utiliza SBERT para análisis semántico de CVs y sílabos
- **Integración con Google Drive**: Sincronización automática de documentos
- **Ranking Dinámico**: Sistema de puntuación multifactorial
- **Interfaz Moderna**: Frontend responsive desarrollado en React

## 🛠️ Tecnologías

### Backend
- FastAPI (Python)
- SBERT (Sentence Transformers)
- ChromaDB (Vector Database)
- Google Drive API

### Frontend
- React 18
- Vite
- Axios

## 📦 Estructura del Proyecto

```
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── models/    # Modelos de datos
│   │   ├── routes/    # Endpoints de la API
│   │   ├── services/  # Lógica de negocio
│   │   └── utils/     # Utilidades
│   └── requirements.txt
├── frontend/          # Aplicación React
│   ├── src/
│   │   ├── components/
│   │   └── services/
│   └── package.json
└── netlify.toml      # Configuración de despliegue
```

## 🚀 Despliegue

### Frontend (Netlify)
El frontend se despliega automáticamente en Netlify desde este repositorio.

### Backend (Local + ngrok)
1. Instalar dependencias: `pip install -r backend/requirements.txt`
2. Ejecutar: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
3. Exponer con ngrok: `ngrok http 8001`

## ⚙️ Configuración

1. Configurar credenciales de Google Drive API
2. Proporcionar URLs de carpetas de CVs y sílabos
3. Sincronizar datos desde Google Drive
4. ¡Comenzar a generar recomendaciones!

## 🎯 Uso

1. **Configuración Inicial**: Conectar carpetas de Google Drive
2. **Sincronización**: Procesar CVs y sílabos automáticamente
3. **Navegación**: Explorar por ciclos académicos y cursos
4. **Recomendaciones**: Obtener rankings de docentes por curso

## 📊 Algoritmo de Recomendación

El sistema utiliza múltiples factores para generar recomendaciones:
- Similitud semántica (40%)
- Experiencia relevante (30%)
- Formación académica (20%)
- Disponibilidad (10%)

## 📁 Estructura de Google Drive

```
Carpeta de Sílabos/
├── Ciclo 01/
│   ├── Curso A.pdf
│   └── Curso B.pdf
├── Ciclo 02/
│   ├── Curso C.pdf
│   └── Curso D.pdf
└── ...

Carpeta de CVs/
├── Docente 1.pdf
├── Docente 2.pdf
└── ...
```

## 🔧 Instalación Local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📡 API Endpoints

- `GET /api/courses/structure/{folder_id}` - Obtener estructura de cursos
- `POST /api/recommendations/generate` - Generar recomendaciones de docentes
- `POST /api/sync` - Sincronizar datos desde Google Drive

---

Desarrollado para optimizar la asignación docente en instituciones educativas.
