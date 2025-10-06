from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import sync, courses, recommendations, auto_sync

app = FastAPI(
    title="Sistema de Emparejamiento Docente-Curso",
    description="API para procesar documentos y encontrar las mejores coincidencias usando NER + SBERT.",
    version="0.1.0"
)

# Configurar CORS para permitir el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],  # URLs del frontend de Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas de los controladores
app.include_router(sync.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(auto_sync.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Sistema de Emparejamiento Docente-Curso"}
