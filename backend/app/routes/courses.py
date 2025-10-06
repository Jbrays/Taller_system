from fastapi import APIRouter, HTTPException
from ..services.drive_service import DriveService

router = APIRouter()
# No inicializamos el servicio aquí para evitar cargar las credenciales
# si no se usa este endpoint. Se instancia a demanda.

@router.get("/courses/structure/{folder_id}", tags=["Courses"])
async def get_courses_structure(folder_id: str):
    """
    Obtiene la estructura jerárquica completa de una carpeta de sílabos
    desde Google Drive, convertida al formato esperado por el frontend.
    """
    print(f"Solicitud para obtener la estructura de la carpeta: {folder_id}")
    drive_service = DriveService()
    if not drive_service.service:
        raise HTTPException(status_code=500, detail="No se pudo inicializar el servicio de Google Drive.")

    try:
        raw_structure = drive_service.get_folder_structure(folder_id)
        print(f"Estructura raw obtenida: {raw_structure}")
        
        # Convertir la estructura de lista a diccionario como espera el frontend
        structure = {}
        
        for folder in raw_structure:
            if folder['type'] == 'folder':
                folder_name = folder['name']
                print(f"Procesando carpeta: {folder_name}")
                
                # Crear diccionario de cursos dentro de esta carpeta
                courses = {}
                if 'children' in folder:
                    for child in folder['children']:
                        if child['type'] == 'folder':
                            # Cada subcarpeta es un curso
                            course_name = child['name']
                            course_files = {}
                            
                            # Procesar archivos dentro del curso
                            if 'children' in child:
                                for file in child['children']:
                                    if file['type'] == 'file':
                                        course_files[file['name']] = {
                                            'id': file['id'],
                                            'name': file['name']
                                        }
                            
                            courses[course_name] = course_files
                        elif child['type'] == 'file':
                            # Archivo directo en la carpeta del ciclo
                            courses[child['name']] = {
                                'id': child['id'],
                                'name': child['name']
                            }
                
                structure[folder_name] = courses
        
        print(f"Estructura convertida: {structure}")
        return {"structure": structure}
    except Exception as e:
        print(f"Error al procesar estructura: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura de carpetas: {e}")