import chromadb
import os

class DatabaseService:
    """
    Servicio para gestionar la base de datos vectorial ChromaDB.
    """
    def __init__(self):
        """
        Inicializa el cliente de ChromaDB y crea o carga las colecciones.
        """
        try:
            # Configura ChromaDB para que guarde los datos en un directorio local.
            # Esto hace que los datos persistan entre ejecuciones.
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'chroma_db')
            self.client = chromadb.PersistentClient(path=db_path)

            # Crea o carga las colecciones. Una para CVs y otra para Sílabos.
            self.cv_collection = self.client.get_or_create_collection(name="cvs")
            self.syllabus_collection = self.client.get_or_create_collection(name="syllabi")
            
            print("✅ Base de datos ChromaDB inicializada exitosamente.")
            print(f"   - Directorio de datos: {db_path}")
            print(f"   - Colecciones cargadas: cvs, syllabi")

        except Exception as e:
            print(f"❌ ERROR al inicializar ChromaDB: {e}")
            self.client = None

    def _flatten_metadata(self, metadata: dict) -> dict:
        """
        Aplana los metadatos para que sean compatibles con ChromaDB.
        ChromaDB solo acepta string, int, float, bool para metadata values.
        """
        flattened = {}
        
        for key, value in metadata.items():
            if key == "entities" and isinstance(value, dict):
                # Aplanar entidades con prefijo
                for entity_key, entity_value in value.items():
                    new_key = f"entities_{entity_key}"
                    if isinstance(entity_value, list):
                        # Convertir listas a strings separados por comas
                        flattened[new_key] = ', '.join(map(str, entity_value))
                    elif isinstance(entity_value, dict):
                        # Para diccionarios anidados, convertir a string
                        flattened[new_key] = str(entity_value)
                    else:
                        flattened[new_key] = str(entity_value)
            elif isinstance(value, list):
                # Convertir listas a strings separados por comas
                flattened[key] = ', '.join(map(str, value))
            elif isinstance(value, dict):
                # Para diccionarios no-entities, convertir a string
                flattened[key] = str(value)
            elif isinstance(value, (str, int, float, bool)):
                # Tipos que ChromaDB puede manejar directamente
                flattened[key] = value
            else:
                # Convertir cualquier otro tipo a string
                flattened[key] = str(value)
        
        return flattened

    def _reinitialize_database(self):
        """
        Reinicializa la base de datos ChromaDB en caso de corrupción.
        """
        try:
            import shutil
            import os
            
            # Cerrar cliente actual
            self.client = None
            self.cv_collection = None
            self.syllabus_collection = None
            
            # Eliminar directorio de datos corrupto
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
                print(f"🗑️ Directorio de base de datos eliminado: {db_path}")
            
            # Reinicializar
            self._initialize_client()
            print("✅ Base de datos ChromaDB reinicializada exitosamente.")
            
        except Exception as e:
            print(f"❌ ERROR al reinicializar base de datos: {e}")

    def add_embedding(self, collection_name: str, embedding: list[float], doc_id: str, metadata: dict):
        """
        Añade un embedding a una colección específica.

        Args:
            collection_name: El nombre de la colección ('cvs' o 'syllabi').
            embedding: El vector de embedding.
            doc_id: Un ID único para el documento (ej: el ID de archivo de Drive).
            metadata: Un diccionario con datos adicionales (ej: nombre del docente).
        """
        if not self.client:
            print("Cliente de ChromaDB no inicializado.")
            return

        try:
            if collection_name == "cvs":
                collection = self.cv_collection
            elif collection_name == "syllabi":
                collection = self.syllabus_collection
            else:
                print(f"Colección '{collection_name}' no válida.")
                return

            # Aplanar metadatos para hacerlos compatibles con ChromaDB
            flattened_metadata = self._flatten_metadata(metadata)
            
            print(f"🔧 DEBUG - Metadatos originales: {metadata}")
            print(f"🔧 DEBUG - Metadatos aplanados: {flattened_metadata}")

            collection.add(
                embeddings=[embedding],
                metadatas=[flattened_metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"❌ ERROR al añadir embedding a la colección '{collection_name}': {e}")
            # Si hay error de base de datos corrupta, intentar reinicializar
            if "unable to open database" in str(e) or "no such table" in str(e):
                print("🔄 Detectando corrupción de base de datos, reinicializando...")
                self._reinitialize_database()

    def search_similar(self, collection_name: str, query_embedding: list[float], n_results: int = 5) -> tuple[list, list] | None:
        """
        Busca los N embeddings más similares a un embedding de consulta.

        Args:
            collection_name: La colección en la que buscar.
            query_embedding: El embedding a comparar.
            n_results: El número de resultados a devolver.

        Returns:
            Una tupla con las listas de metadatos y distancias correspondientes, o None si hay error.
        """
        if not self.client:
            print("Cliente de ChromaDB no inicializado.")
            return None

        try:
            if collection_name == "cvs":
                collection = self.cv_collection
            elif collection_name == "syllabi":
                collection = self.syllabus_collection
            else:
                print(f"Colección '{collection_name}' no válida.")
                return None

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )

            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []

            # DEBUG: Analizar las distancias obtenidas
            if distances:
                import numpy as np
                print(f"\n🔍 DEBUG ChromaDB Search - Collection: {collection_name}")
                print(f"   Query embedding norm: {np.linalg.norm(query_embedding):.3f}")
                print(f"   Results found: {len(distances)}")
                print(f"   Distance range: [{min(distances):.3f}, {max(distances):.3f}]")
                print(f"   Distance mean: {np.mean(distances):.3f}")
                
                # Verificar si las distancias son anómalamente altas
                if max(distances) > 3.0:
                    print(f"   ⚠️  WARNING: Very high distances detected! May indicate embedding normalization issues.")
                elif max(distances) > 2.0:
                    print(f"   ⚠️  WARNING: High distances detected! Check embedding quality.")
                else:
                    print(f"   ✅ Distances look reasonable.")

            return metadatas, distances

        except Exception as e:
            print(f"❌ ERROR al buscar en la colección '{collection_name}': {e}")
            # Si hay error de base de datos corrupta, intentar reinicializar
            if "unable to open database" in str(e) or "no such table" in str(e):
                print("🔄 Detectando corrupción de base de datos, reinicializando...")
                self._reinitialize_database()
            return None

# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    # Para esta prueba, necesitamos el NLPService para crear embeddings de ejemplo.
    from .nlp_service import NLPService

    db_service = DatabaseService()
    nlp_service = NLPService()

    if db_service.client and nlp_service.model:
        print("\n--- Probando la base de datos ---")
        
        # 1. Crear embeddings de ejemplo
        cv_text_1 = "Experto en inteligencia artificial y machine learning."
        cv_text_2 = "Desarrollador web especializado en React y Node.js."
        syllabus_text = "Curso de introducción a la inteligencia artificial."

        embedding_cv_1 = nlp_service.generate_embedding(cv_text_1)
        embedding_cv_2 = nlp_service.generate_embedding(cv_text_2)
        embedding_syllabus = nlp_service.generate_embedding(syllabus_text)

        # 2. Añadir los CVs a la colección 'cvs'
        print("\nAñadiendo embeddings de CVs a la base de datos...")
        db_service.add_embedding("cvs", embedding_cv_1, "cv_001", {"name": "Docente AI"})
        db_service.add_embedding("cvs", embedding_cv_2, "cv_002", {"name": "Docente Web"})
        print("Embeddings añadidos.")

        # 3. Buscar CVs similares al sílabo
        print(f"\nBuscando CVs similares al sílabo: '{syllabus_text}'")
        results, distances = db_service.search_similar("cvs", embedding_syllabus, n_results=2)

        if results:
            print("\nResultados de la búsqueda:")
            for i, (metadata, dist) in enumerate(zip(results, distances)):
                print(f"  {i+1}. Docente: {metadata.get('name', 'N/A')}, Distancia: {dist:.4f}")
        else:
            print("No se encontraron resultados.")