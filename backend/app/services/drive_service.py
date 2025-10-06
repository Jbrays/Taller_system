from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
from dotenv import load_dotenv
import io

# Importar el servicio de PDF
from .pdf_service import PDFService

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


# --- CONFIGURACIÓN ---
# La ruta al archivo de credenciales. 
# Buscar en el directorio padre del proyecto (raíz)
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'credentials.json')

# Los permisos que nuestra aplicación necesita.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveService:
    """
    Servicio para interactuar con la API de Google Drive.
    """
    def __init__(self):
        """
        Inicializa el servicio y se autentica con Google Drive.
        """
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Conexión exitosa con Google Drive.")
        except FileNotFoundError:
            print(f"❌ ERROR: No se encontró el archivo de credenciales en '{SERVICE_ACCOUNT_FILE}'")
            print("Por favor, asegúrate de que el archivo 'credentials.json' se encuentra en la raíz del proyecto.")
            self.service = None
        except Exception as e:
            print(f"❌ ERROR: Ocurrió un error al conectar con Google Drive: {e}")
            self.service = None
        
        # Cargamos los IDs de las carpetas para que estén disponibles en el servicio
        self.CV_FOLDER_ID = os.getenv("GOOGLE_DRIVE_CV_FOLDER_ID")
        self.SYLLABUS_FOLDER_ID = os.getenv("GOOGLE_DRIVE_SYLLABUS_FOLDER_ID")

    def list_files_in_folder(self, folder_id: str) -> list:
        """
        Lista todos los archivos y carpetas dentro de una carpeta específica.
        """
        if not self.service or not folder_id:
            return []

        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"❌ ERROR al listar archivos en la carpeta '{folder_id}': {e}")
            return []

    def download_file(self, file_id: str) -> bytes | None:
        """
        Descarga el contenido de un archivo de Drive.

        Args:
            file_id: El ID del archivo a descargar.

        Returns:
            El contenido del archivo en bytes, o None si hay un error.
        """
        if not self.service:
            print("Servicio de Drive no inicializado.")
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Descargando archivo {file_id}: {int(status.progress() * 100)}%.")
            
            return file_handle.getvalue()
        except Exception as e:
            print(f"❌ ERROR al descargar el archivo '{file_id}': {e}")
            return None

    def get_folder_structure(self, folder_id: str) -> list:
        """
        Escanea recursivamente una carpeta de Drive para obtener su estructura.

        Args:
            folder_id: El ID de la carpeta raíz desde donde empezar a escanear.

        Returns:
            Una lista de diccionarios representando la estructura jerárquica.
        """
        if not self.service:
            print("Servicio de Drive no inicializado.")
            return []
        
        def recurse_folder(current_folder_id):
            items_in_folder = self.list_files_in_folder(current_folder_id)
            children = []
            for item in items_in_folder:
                node = {
                    "id": item['id'],
                    "name": item['name'],
                    "type": 'folder' if item['mimeType'] == 'application/vnd.google-apps.folder' else 'file'
                }
                if node['type'] == 'folder':
                    # Si es una carpeta, escanea su contenido recursivamente
                    node['children'] = recurse_folder(item['id'])
                children.append(node)
            return children

        return recurse_folder(folder_id)


# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    CV_FOLDER_ID = os.getenv("GOOGLE_DRIVE_CV_FOLDER_ID")
    
    drive = DriveService()
    pdf_service = PDFService()
    
    if drive.service:
        print("\n--- Listando CVs ---")
        cv_files = drive.list_files_in_folder(CV_FOLDER_ID)
        
        # Si encontramos archivos, intentamos descargar y procesar el primero
        if cv_files:
            first_cv = cv_files[0]
            print(f"\n--- Descargando primer CV: {first_cv['name']} ---")
            
            cv_content = drive.download_file(first_cv['id'])
            
            if cv_content:
                print("\n--- Extrayendo texto del PDF ---")
                text = pdf_service.extract_text_from_pdf(cv_content)
                if text:
                    print("✅ Texto extraído exitosamente.")
                    print("Primeros 500 caracteres:")
                    print("-" * 30)
                    print(text[:500] + "...")
                else:
                    print("❌ No se pudo extraer texto del PDF.")
        else:
            print("No se encontraron archivos en la carpeta de CVs.")


