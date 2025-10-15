# 📋 Modelos de Datos - Sistema de Emparejamiento

Esta carpeta contiene todos los **schemas de validación** (Pydantic models) para la API.

## 📁 Estructura

```
models/
├── __init__.py                  # Exporta todos los modelos
├── sync_models.py              # Modelos para sincronización con Drive
├── recommendation_models.py    # Modelos para recomendaciones
└── common_models.py            # Modelos reutilizables
```

## 🎯 Propósito

Los modelos en esta carpeta sirven para:

1. **Validación automática** de datos de entrada (requests)
2. **Documentación automática** en Swagger/OpenAPI
3. **Type hints** para mejor autocompletado en IDE
4. **Serialización/deserialización** consistente
5. **Reutilización** de estructuras de datos

## 📦 Modelos Disponibles

### **sync_models.py**
- `SyncRequest` - Request para iniciar sincronización
- `SyncResponse` - Response con resultados de sincronización

### **recommendation_models.py**
- `RecommendationRequest` - Request para generar recomendaciones
- `RecommendationResponse` - Response con lista de recomendaciones
- `TeacherRecommendation` - Recomendación individual de un docente
- `ComponentScores` - Desglose de scores por componente

### **common_models.py**
- `DocumentMetadata` - Metadata de documentos procesados
- `EmbeddingInfo` - Información sobre embeddings
- `ErrorResponse` - Response estándar para errores
- `HealthCheckResponse` - Response del health check

## 🔧 Uso

### Importar modelos en routes:

```python
from ..models.sync_models import SyncRequest, SyncResponse
from ..models.recommendation_models import RecommendationRequest

@router.post("/sync")
async def sync_documents(request: SyncRequest) -> SyncResponse:
    # FastAPI valida automáticamente el request
    # usando el schema de SyncRequest
    ...
```

### Usar modelos directamente:

```python
# Crear instancia con validación
sync_request = SyncRequest(
    cv_folder_id="abc123",
    syllabus_folder_id="xyz789"
)

# Validación automática detecta errores
try:
    bad_request = SyncRequest(cv_folder_id=123)  # ❌ TypeError
except ValidationError as e:
    print(e)
```

## ✅ Ventajas

### Antes (sin models/):
```python
# routes/sync.py
class SyncRequest(BaseModel):  # ❌ Duplicado en cada ruta
    cv_folder_id: str
    syllabus_folder_id: str

# routes/recommendations.py  
class SyncRequest(BaseModel):  # ❌ Mismo modelo redefinido
    cv_folder_id: str
    syllabus_folder_id: str
```

### Después (con models/):
```python
# models/sync_models.py
class SyncRequest(BaseModel):  # ✅ Definido UNA VEZ
    cv_folder_id: str = Field(..., description="...", example="...")
    syllabus_folder_id: str = Field(..., description="...", example="...")

# routes/sync.py
from ..models import SyncRequest  # ✅ Reutilizar

# routes/recommendations.py
from ..models import SyncRequest  # ✅ Reutilizar
```

## 📚 Mejores Prácticas

1. **Field con metadata**: Usar `Field()` con descripciones y ejemplos
2. **Config con examples**: Agregar ejemplos completos en `Config.json_schema_extra`
3. **Validadores**: Usar `ge`, `le`, `min_length`, etc. para validaciones
4. **Type hints completos**: `List[str]`, `Optional[int]`, `Dict[str, Any]`
5. **Documentación**: Docstrings para cada clase

## 🔄 Migración Completada

Se refactorizaron los siguientes archivos:

- ✅ `routes/sync.py` - Ahora importa `SyncRequest` desde models
- ✅ `routes/recommendations.py` - Ahora importa modelos desde models
- ✅ Modelos centralizados con documentación completa
- ✅ 407 líneas de código de modelos bien organizadas

## 📖 Referencias

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Field Validation](https://docs.pydantic.dev/latest/concepts/fields/)
