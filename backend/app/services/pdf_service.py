import PyPDF2
from io import BytesIO

class PDFService:
    """
    Servicio para extraer texto de archivos PDF.
    """

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extrae el texto de un archivo PDF proporcionado como bytes.

        Args:
            pdf_content: El contenido del archivo PDF en bytes.

        Returns:
            El texto extraído como una sola cadena de texto.
            Retorna una cadena vacía si el PDF no se puede leer o no tiene texto.
        """
        text = ""
        try:
            # Abrir el contenido del PDF en memoria
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            
            # Iterar a través de todas las páginas y extraer el texto
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip()
        except Exception as e:
            print(f"❌ ERROR al leer el contenido del PDF: {e}")
            return ""