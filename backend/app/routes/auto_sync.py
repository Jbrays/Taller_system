from fastapi import APIRouter, HTTPException
from ..services.database_service import DatabaseService
from ..services.drive_service import DriveService
from ..services.pdf_service import PDFService
from ..services.nlp_service import NLPService
from ..services.ner_service import NERService

router = APIRouter()

# Servicios
db_service = DatabaseService()
drive_service = DriveService()
pdf_service = PDFService()
nlp_service = NLPService()
ner_service = NERService()

@router.post("/auto-sync", tags=["Sync"])
async def auto_sync():
    """
    Sincronización automática usando las carpetas configuradas en el servicio de Drive.
    """
    print("Iniciando sincronización automática...")
    
    if not drive_service.CV_FOLDER_ID or not drive_service.SYLLABUS_FOLDER_ID:
        raise HTTPException(
            status_code=400, 
            detail="IDs de carpetas no configurados. Verifique las variables de entorno."
        )
    
    # Procesar CVs
    print("\n--- Procesando CVs ---")
    cv_files = drive_service.list_files_in_folder(drive_service.CV_FOLDER_ID)
    processed_cvs = 0
    for cv_file in cv_files:
        if cv_file['mimeType'] == 'application/pdf':
            if await process_document(cv_file, "cvs"):
                processed_cvs += 1
    
    # Procesar Sílabos recursivamente
    print("\n--- Procesando Sílabos ---")
    processed_syllabi = 0
    
    def recurse_and_process(folder_id):
        nonlocal processed_syllabi
        items = drive_service.list_files_in_folder(folder_id)
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                recurse_and_process(item['id'])
            elif item['mimeType'] == 'application/pdf':
                if process_document_sync(item, "syllabi"):
                    processed_syllabi += 1
    
    recurse_and_process(drive_service.SYLLABUS_FOLDER_ID)
    
    return {
        "status": "completed",
        "processed_cvs": processed_cvs,
        "processed_syllabi": processed_syllabi
    }

async def process_document(file_info, collection_name):
    """Procesa un documento asincrónicamente."""
    return process_document_sync(file_info, collection_name)

def process_document_sync(file_info, collection_name):
    """Procesa un documento de forma síncrona."""
    print(f"Procesando: {file_info['name']} ({file_info['id']})")
    
    # Verificar si ya existe en la base de datos
    try:
        collection = db_service.cv_collection if collection_name == "cvs" else db_service.syllabus_collection
        existing = collection.get(ids=[file_info['id']])
        if existing and existing.get('ids'):
            print(f"  -> Ya procesado. Saltando.")
            return False
    except:
        pass  # Si hay error, continuar con el procesamiento
    
    content = drive_service.download_file(file_info['id'])
    if not content:
        print(f"  -> Error al descargar. Saltando.")
        return False

    text = pdf_service.extract_text_from_pdf(content)
    if not text:
        print(f"  -> No se pudo extraer texto. Saltando.")
        return False
    
    embedding = nlp_service.generate_embedding(text)
    if not embedding:
        print(f"  -> Error al generar embedding. Saltando.")
        return False

    # Extraer entidades con NER
    if collection_name == "cvs":
        entities = ner_service.extract_entities_from_cv(text)
    else:
        entities = ner_service.extract_entities_from_syllabus(text)
    
    metadata = {
        "name": file_info['name'].replace('.pdf', ''),
        "raw_text": text[:1000],
        "entities": entities
    }
    
    db_service.add_embedding(collection_name, embedding, file_info['id'], metadata)
    print(f"  -> ✅ Procesado y guardado en '{collection_name}'.")
    return True
