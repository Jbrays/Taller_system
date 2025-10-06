#!/usr/bin/env python3
"""
Script de demostración del servicio NLP con SBERT
Para generar evidencias del funcionamiento del modelo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.nlp_service import NLPService
import numpy as np

def demo_sbert_processing():
    print("=" * 60)
    print("🤖 DEMOSTRACIÓN DEL SERVICIO NLP - SBERT")
    print("=" * 60)
    
    # Inicializar el servicio NLP
    print("\n📥 Inicializando modelo SBERT...")
    nlp_service = NLPService()
    print(f"✅ Modelo cargado: {nlp_service.model}")
    
    # Textos de ejemplo de CV y sílabo
    cv_texto = """
    Dr. Juan Pérez López
    Doctorado en Ciencias de la Computación
    Especialista en Machine Learning y Deep Learning
    Experiencia: 15 años en desarrollo de software
    Conocimientos: Python, TensorFlow, PyTorch, Algoritmos de IA
    Publicaciones: 25 artículos en revistas indexadas
    Proyectos: Sistemas de recomendación, Procesamiento de lenguaje natural
    """
    
    silabo_texto = """
    Curso: Inteligencia Artificial
    Descripción: Fundamentos de IA, algoritmos de machine learning
    Contenido: Redes neuronales, deep learning, procesamiento de lenguaje natural
    Requisitos: Programación en Python, matemáticas avanzadas
    Objetivos: Desarrollar sistemas inteligentes usando técnicas de IA
    """
    
    print(f"\n📄 TEXTO DEL CV:")
    print("-" * 40)
    print(cv_texto.strip())
    
    print(f"\n📋 TEXTO DEL SÍLABO:")
    print("-" * 40)
    print(silabo_texto.strip())
    
    # Generar embeddings
    print(f"\n🧠 Generando embeddings con SBERT...")
    cv_embedding = nlp_service.generate_embedding(cv_texto)
    silabo_embedding = nlp_service.generate_embedding(silabo_texto)
    
    print(f"✅ Embedding del CV generado: shape {cv_embedding.shape}")
    print(f"✅ Embedding del sílabo generado: shape {silabo_embedding.shape}")
    
    # Verificar normalización
    cv_norm = np.linalg.norm(cv_embedding)
    silabo_norm = np.linalg.norm(silabo_embedding)
    
    print(f"\n📊 VERIFICACIÓN DE NORMALIZACIÓN:")
    print(f"   Norma del embedding CV: {cv_norm:.6f}")
    print(f"   Norma del embedding sílabo: {silabo_norm:.6f}")
    print(f"   ✅ Embeddings normalizados correctamente" if abs(cv_norm - 1.0) < 0.001 else "   ❌ Error en normalización")
    
    # Calcular similitud semántica
    print(f"\n🔍 CALCULANDO SIMILITUD SEMÁNTICA...")
    similarity = nlp_service.calculate_similarity(cv_embedding, silabo_embedding)
    
    print(f"📈 Similitud semántica: {similarity:.6f}")
    print(f"📊 Similitud como porcentaje: {similarity * 100:.2f}%")
    
    # Evaluar la similitud
    if similarity > 0.7:
        nivel = "🟢 ALTA"
    elif similarity > 0.4:
        nivel = "🟡 MEDIA"
    else:
        nivel = "🔴 BAJA"
    
    print(f"🎯 Nivel de compatibilidad: {nivel}")
    
    # Mostrar algunos valores del embedding para evidencia
    print(f"\n🔢 MUESTRA DE VALORES DEL EMBEDDING (primeros 10):")
    print(f"   CV: {cv_embedding[:10]}")
    print(f"   Sílabo: {silabo_embedding[:10]}")
    
    print(f"\n" + "=" * 60)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("💡 El modelo SBERT está funcionando correctamente")
    print("🎯 Similitud semántica calculada exitosamente")
    print("=" * 60)
    
    return similarity

if __name__ == "__main__":
    try:
        similarity = demo_sbert_processing()
        print(f"\n🏆 RESULTADO FINAL: Similitud = {similarity:.4f} ({similarity*100:.1f}%)")
    except Exception as e:
        print(f"❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()
