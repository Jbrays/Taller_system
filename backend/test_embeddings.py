#!/usr/bin/env python3
"""
Script para probar la generación de embeddings y verificar que SBERT funcione correctamente.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.nlp_service import NLPService
import numpy as np

def test_embeddings():
    """Prueba la generación de embeddings y calcula similitudes."""
    
    print("🔍 Iniciando test de embeddings...")
    
    # Inicializar servicio NLP
    nlp_service = NLPService()
    
    if not nlp_service.model:
        print("❌ ERROR: No se pudo cargar el modelo NLP")
        return
    
    # Textos de prueba similares y diferentes
    texto_cv1 = """
    Ingeniero de sistemas con experiencia en programación Java, Python y desarrollo web.
    Especialista en bases de datos Oracle y Git. Docente universitario con 5 años de experiencia.
    """
    
    texto_cv2 = """
    Profesional en computación con conocimientos en Java, desarrollo de software y manejo de Oracle.
    Experiencia académica en universidades y manejo de herramientas como Git y Python.
    """
    
    texto_cv3 = """
    Especialista en marketing digital y gestión de redes sociales.
    Experiencia en publicidad online y análisis de métricas de engagement.
    """
    
    texto_silabo = """
    Curso de Programación Orientada a Objetos. Requisitos: Java, Git, Oracle, Scala.
    Desarrollo de aplicaciones usando paradigmas de programación orientada a objetos.
    """
    
    print("\n📄 Generando embeddings...")
    
    # Generar embeddings
    emb_cv1 = nlp_service.generate_embedding(texto_cv1)
    emb_cv2 = nlp_service.generate_embedding(texto_cv2)
    emb_cv3 = nlp_service.generate_embedding(texto_cv3)
    emb_silabo = nlp_service.generate_embedding(texto_silabo)
    
    if not all([emb_cv1, emb_cv2, emb_cv3, emb_silabo]):
        print("❌ ERROR: No se pudieron generar todos los embeddings")
        return
    
    # Convertir a arrays de numpy
    emb_cv1 = np.array(emb_cv1)
    emb_cv2 = np.array(emb_cv2)
    emb_cv3 = np.array(emb_cv3)
    emb_silabo = np.array(emb_silabo)
    
    print("\n📊 Análisis de embeddings:")
    
    # Función para calcular distancia euclidiana
    def euclidean_distance(a, b):
        return np.linalg.norm(a - b)
    
    # Función para calcular similitud coseno
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    print("\n🔍 Distancias Euclidianas (como las usa ChromaDB):")
    dist_cv1_silabo = euclidean_distance(emb_cv1, emb_silabo)
    dist_cv2_silabo = euclidean_distance(emb_cv2, emb_silabo)
    dist_cv3_silabo = euclidean_distance(emb_cv3, emb_silabo)
    dist_cv1_cv2 = euclidean_distance(emb_cv1, emb_cv2)
    
    print(f"   CV1 ↔ Sílabo: {dist_cv1_silabo:.6f}")
    print(f"   CV2 ↔ Sílabo: {dist_cv2_silabo:.6f}")
    print(f"   CV3 ↔ Sílabo: {dist_cv3_silabo:.6f} (debería ser mayor)")
    print(f"   CV1 ↔ CV2: {dist_cv1_cv2:.6f} (deberían ser similares)")
    
    print("\n🔍 Similitudes Coseno (referencia):")
    cos_cv1_silabo = cosine_similarity(emb_cv1, emb_silabo)
    cos_cv2_silabo = cosine_similarity(emb_cv2, emb_silabo)
    cos_cv3_silabo = cosine_similarity(emb_cv3, emb_silabo)
    cos_cv1_cv2 = cosine_similarity(emb_cv1, emb_cv2)
    
    print(f"   CV1 ↔ Sílabo: {cos_cv1_silabo:.6f}")
    print(f"   CV2 ↔ Sílabo: {cos_cv2_silabo:.6f}")
    print(f"   CV3 ↔ Sílabo: {cos_cv3_silabo:.6f} (debería ser menor)")
    print(f"   CV1 ↔ CV2: {cos_cv1_cv2:.6f} (deberían ser similares)")
    
    print("\n✅ Verificaciones:")
    
    # Verificar que las distancias estén en un rango razonable
    max_dist = max(dist_cv1_silabo, dist_cv2_silabo, dist_cv3_silabo, dist_cv1_cv2)
    if max_dist > 3.0:
        print(f"❌ Distancias muy altas (max: {max_dist:.3f}) - posible problema")
    elif max_dist > 2.0:
        print(f"⚠️  Distancias altas (max: {max_dist:.3f}) - revisar")
    else:
        print(f"✅ Distancias en rango normal (max: {max_dist:.3f})")
    
    # Verificar que CV3 (irrelevante) tenga mayor distancia
    if dist_cv3_silabo > dist_cv1_silabo and dist_cv3_silabo > dist_cv2_silabo:
        print("✅ CV irrelevante tiene mayor distancia - correcto")
    else:
        print("❌ CV irrelevante no tiene mayor distancia - problema con el modelo")
    
    # Verificar que CV1 y CV2 sean similares entre sí
    if dist_cv1_cv2 < dist_cv1_silabo:
        print("✅ CVs similares tienen menor distancia entre sí - correcto")
    else:
        print("❌ CVs similares no son más parecidos entre sí - problema")
    
    print("\n🎯 Conversión a similitud (como en el sistema):")
    
    def convert_distance_to_similarity(distance):
        if distance > 10.0:
            return 0.0
        elif distance > 2.0:
            return max(0.0, 1.0 - (distance / 8.0))
        else:
            return max(0.0, 1.0 - (distance / 2.0))
    
    sim_cv1 = convert_distance_to_similarity(dist_cv1_silabo)
    sim_cv2 = convert_distance_to_similarity(dist_cv2_silabo)
    sim_cv3 = convert_distance_to_similarity(dist_cv3_silabo)
    
    print(f"   CV1 similarity: {sim_cv1:.6f}")
    print(f"   CV2 similarity: {sim_cv2:.6f}")
    print(f"   CV3 similarity: {sim_cv3:.6f}")
    
    if sim_cv1 > 0 or sim_cv2 > 0:
        print("✅ Al menos algunos embeddings generan similitud > 0")
    else:
        print("❌ Todos los embeddings generan similitud 0 - problema grave")

if __name__ == "__main__":
    test_embeddings()
