from fastapi import APIRouter, HTTPException, Body
from ..models.sync_models import SyncRequest, SyncResponse
from ..services.drive_service import DriveService
from ..services.pdf_service import PDFService
from ..services.nlp_service import NLPService
from ..services.ner_service import NERService
from ..services.database_service import DatabaseService
from ..services.sql_database_service import SQLDatabaseService

router = APIRouter()

# Inicializamos los servicios
drive_service = DriveService()
pdf_service = PDFService()
nlp_service = NLPService()
ner_service = NERService()
db_service = DatabaseService()  # ChromaDB (vectorial)
sql_db_service = SQLDatabaseService()  # SQLite (relacional)

def process_file(file_id: str, file_name: str, collection_name: str, cycle_name: str = "", course_name: str = ""):
    """Función auxiliar para procesar un único archivo (CV o Sílabo)."""
    print(f"Procesando: {file_name} ({file_id})")
    
    content = drive_service.download_file(file_id)
    if not content:
        print(f"  -> Error al descargar. Saltando.")
        return False

    text = pdf_service.extract_text_from_pdf(content)
    if not text:
        print(f"  -> No se pudo extraer texto. Saltando.")
        return False
    
    # Generar embedding semántico
    embedding = nlp_service.generate_embedding(text)
    if not embedding:
        print(f"  -> Error al generar embedding. Saltando.")
        return False

    # Extraer entidades con NER
    if collection_name == "cvs":
        entities = ner_service.extract_entities_from_cv(text)
    else:  # syllabi
        entities = ner_service.extract_entities_from_syllabus(text)
    
    # Incluir tanto el texto original como las entidades extraídas en metadata
    metadata = {
        "name": file_name.replace('.pdf', ''),
        "filename": file_name,
        "raw_text": text[:1000],  # Primeros 1000 caracteres para referencia
        "entities": entities
    }
    
    # Para sílabos, agregar información del ciclo y curso
    if collection_name == "syllabi":
        metadata["cycle"] = cycle_name
        metadata["course"] = course_name
        print(f"  -> Asociando con: ciclo='{cycle_name}', curso='{course_name}'")
    
    # 1. Guardar en ChromaDB (embedding vectorial)
    db_service.add_embedding(collection_name, embedding, file_id, metadata)
    
    # 2. Guardar en SQL (metadata estructurada)
    try:
        if collection_name == "cvs":
            # Extraer skills del CV
            skills_list = entities.get('technical_skills', [])
            experience_years = entities.get('experience_years', 0)
            teacher_name = file_name.replace('.pdf', '')
            
            teacher_id = sql_db_service.add_teacher(
                name=teacher_name,
                embedding_id=file_id,
                skills_list=skills_list,
                experience_years=experience_years
            )
            print(f"  -> ✅ Teacher guardado en SQL (ID: {teacher_id}) con {len(skills_list)} skills")
        
        else:  # syllabi
            # Extraer required_skills del sílabo
            required_skills = entities.get('required_skills', [])
            
            course_id = sql_db_service.add_course(
                name=course_name,
                cycle=cycle_name,
                embedding_id=file_id,
                required_skills=required_skills
            )
            print(f"  -> ✅ Course guardado en SQL (ID: {course_id}) con {len(required_skills)} required skills")
    
    except Exception as e:
        print(f"  -> ⚠️ Error al guardar en SQL: {e}")
    
    print(f"  -> ✅ Procesado y guardado en ChromaDB + SQL con entidades extraídas.")
    return True

@router.post("/sync", tags=["Sync"])
async def sync_documents(request: SyncRequest):
    """
    Inicia el proceso de sincronización con los IDs de las carpetas proporcionados.
    """
    print("Iniciando proceso de sincronización...")
    
    # --- 1. Procesar todos los CVs ---
    print("\n--- Procesando CVs ---")
    cv_files = drive_service.list_files_in_folder(request.cv_folder_id)
    processed_cvs = 0
    for cv_file in cv_files:
        if cv_file['mimeType'] == 'application/pdf':
            if process_file(cv_file['id'], cv_file['name'], "cvs", "", ""):
                processed_cvs += 1

    # --- 2. Procesar todos los Sílabos recursivamente ---
    print("\n--- Procesando Sílabos ---")
    processed_syllabi = 0
    
    def recurse_and_process(folder_id, cycle_name="", course_name=""):
        nonlocal processed_syllabi
        items = drive_service.list_files_in_folder(folder_id)
        
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Determinar si es un ciclo o un curso
                folder_name = item['name']
                
                if 'ciclo' in folder_name.lower():
                    # Es una carpeta de ciclo
                    print(f"📁 Procesando ciclo: {folder_name}")
                    recurse_and_process(item['id'], cycle_name=folder_name, course_name="")
                elif cycle_name and not course_name and folder_name.lower() != 'silabo':
                    # Es una carpeta de curso dentro de un ciclo
                    print(f"📚 Procesando curso: {folder_name} en {cycle_name}")
                    recurse_and_process(item['id'], cycle_name=cycle_name, course_name=folder_name)
                else:
                    # Es otra carpeta (como 'silabo'), continuar recursivamente
                    recurse_and_process(item['id'], cycle_name=cycle_name, course_name=course_name)
                    
            elif item['mimeType'] == 'application/pdf':
                # Solo procesar PDFs si tenemos información del ciclo y curso
                if cycle_name and course_name:
                    if process_file(item['id'], item['name'], "syllabi", cycle_name, course_name):
                        processed_syllabi += 1
                else:
                    print(f"  -> Saltando {item['name']} - Sin información de ciclo/curso")

    recurse_and_process(request.syllabus_folder_id)

    return {
        "status": "completed",
        "processed_cvs": processed_cvs,
        "processed_syllabi": processed_syllabi
    }
