from sentence_transformers import SentenceTransformer

class NLPService:
    """
    Servicio para tareas de Procesamiento de Lenguaje Natural (NLP),
    específicamente la generación de embeddings.
    """
    def __init__(self):
        """
        Inicializa el servicio y carga el modelo de Sentence Transformers.
        El modelo se descarga la primera vez y luego se carga desde el caché.
        """
        # Modelo multilingüe, bueno para empezar y balanceado en rendimiento/calidad.
        self.model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        try:
            print(f"Cargando modelo NLP '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)
            print("✅ Modelo NLP cargado exitosamente.")
        except Exception as e:
            print(f"❌ ERROR al cargar el modelo NLP: {e}")
            self.model = None

    def generate_embedding(self, text: str) -> list[float] | None:
        """
        Genera un vector de embedding para un texto dado.

        Args:
            text: La cadena de texto a procesar.

        Returns:
            Una lista de floats representando el embedding, o None si hay un error.
        """
        if not self.model:
            print("Modelo NLP no cargado. No se puede generar embedding.")
            return None
        
        if not text or not isinstance(text, str):
            print("El texto de entrada debe ser una cadena no vacía.")
            return None

        try:
            # .encode() convierte el texto en un vector.
            # .tolist() lo convierte a una lista de Python estándar.
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # NORMALIZAR el embedding para que tenga norma 1.0
            # Esto es crucial para que las distancias euclidianas en ChromaDB sean correctas
            import numpy as np
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            
            if norm > 0:
                normalized_embedding = embedding_array / norm
            else:
                normalized_embedding = embedding_array
            
            # Convertir de vuelta a lista
            embedding_list = normalized_embedding.tolist()
            
            # DEBUG: Verificar propiedades del embedding
            new_norm = np.linalg.norm(normalized_embedding)
            mean_val = np.mean(normalized_embedding)
            std_val = np.std(normalized_embedding)
            
            print(f"🔍 DEBUG Embedding - Text length: {len(text)} chars")
            print(f"   Embedding dim: {len(embedding_list)}")
            print(f"   Original norm: {norm:.3f}")
            print(f"   Normalized norm: {new_norm:.3f} (should be ≈1.0)")
            print(f"   Mean: {mean_val:.6f}")
            print(f"   Std: {std_val:.6f}")
            print(f"   Range: [{min(embedding_list):.6f}, {max(embedding_list):.6f}]")
            
            return embedding_list
        except Exception as e:
            print(f"❌ ERROR al generar el embedding: {e}")
            return None

# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    nlp_service = NLPService()
    
    if nlp_service.model:
        sample_text = "Ingeniero de Software con experiencia en Python y desarrollo web."
        print(f"\n--- Generando embedding para el texto de ejemplo ---")
        print(f"Texto: '{sample_text}'")
        
        embedding = nlp_service.generate_embedding(sample_text)
        
        if embedding:
            print(f"✅ Embedding generado exitosamente.")
            print(f"   - Dimensión del vector: {len(embedding)}")
            print(f"   - Primeros 5 valores: {embedding[:5]}")
        else:
            print("❌ Falló la generación del embedding.")
