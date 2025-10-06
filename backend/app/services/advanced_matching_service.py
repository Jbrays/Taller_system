from typing import Dict, List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class AdvancedMatchingService:
    """
    Servicio avanzado de matching que combina similitud semántica (SBERT)
    con análisis de características específicas extraídas por NER.
    """
    
    def __init__(self):
        """Inicializa los pesos para diferentes componentes del matching."""
        self.weights = {
            'semantic_similarity': 0.4,    # 40% - Similitud semántica general
            'skill_match': 0.35,           # 35% - Compatibilidad de habilidades específicas
            'experience_match': 0.15,      # 15% - Compatibilidad de experiencia
            'education_match': 0.10        # 10% - Compatibilidad educativa
        }

    def calculate_advanced_match(self, cv_entities: Dict, syllabus_entities: Dict, 
                               semantic_similarity: float) -> Dict:
        """
        Calcula un score de matching avanzado combinando múltiples factores.
        
        Args:
            cv_entities: Entidades extraídas del CV por NER
            syllabus_entities: Entidades extraídas del sílabo por NER
            semantic_similarity: Score de similitud semántica de SBERT
            
        Returns:
            Diccionario con scores detallados y explicación
        """
        
        # DEBUG: Imprimir datos de entrada para análisis
        teacher_name = cv_entities.get('name', 'Unknown')
        print(f"\n🔍 DEBUG AdvancedMatching - Teacher: {teacher_name}")
        print(f"   CV Skills: {cv_entities.get('technical_skills', [])}")
        print(f"   CV Experience: {cv_entities.get('experience_years', 0)} years")
        print(f"   Syllabus Required Skills: {syllabus_entities.get('required_skills', [])}")
        print(f"   Semantic Similarity INPUT: {semantic_similarity:.6f}")
        
        if semantic_similarity == 0.0:
            print(f"   ⚠️  WARNING: Semantic similarity is 0.0 - SBERT not contributing to score!")
        elif semantic_similarity < 0.1:
            print(f"   ⚠️  WARNING: Very low semantic similarity - check embedding quality")
        else:
            print(f"   ✅ Semantic similarity looks normal")
        
        # 1. Calcular compatibilidad de habilidades técnicas
        skill_score = self._calculate_skill_compatibility(
            cv_entities.get('technical_skills', []),
            syllabus_entities.get('required_skills', [])
        )
        
        # 2. Calcular compatibilidad de experiencia
        experience_score = self._calculate_experience_compatibility(
            cv_entities.get('experience_years', 0),
            syllabus_entities
        )
        
        # 3. Calcular compatibilidad educativa
        education_score = self._calculate_education_compatibility(
            cv_entities.get('education', []),
            syllabus_entities.get('course_topics', [])
        )
        
        # 4. Combinar todos los scores con pesos
        final_score = (
            semantic_similarity * self.weights['semantic_similarity'] +
            skill_score * self.weights['skill_match'] +
            experience_score * self.weights['experience_match'] +
            education_score * self.weights['education_match']
        )
        
        # DEBUG: Mostrar cálculo detallado
        semantic_contribution = semantic_similarity * self.weights['semantic_similarity']
        skill_contribution = skill_score * self.weights['skill_match']
        experience_contribution = experience_score * self.weights['experience_match']
        education_contribution = education_score * self.weights['education_match']
        
        print(f"   📊 Component Scores:")
        print(f"      Semantic: {semantic_similarity:.3f} * {self.weights['semantic_similarity']} = {semantic_contribution:.3f} ({semantic_contribution/final_score*100 if final_score > 0 else 0:.1f}% of total)")
        print(f"      Skills: {skill_score:.3f} * {self.weights['skill_match']} = {skill_contribution:.3f} ({skill_contribution/final_score*100 if final_score > 0 else 0:.1f}% of total)")
        print(f"      Experience: {experience_score:.3f} * {self.weights['experience_match']} = {experience_contribution:.3f} ({experience_contribution/final_score*100 if final_score > 0 else 0:.1f}% of total)")
        print(f"      Education: {education_score:.3f} * {self.weights['education_match']} = {education_contribution:.3f} ({education_contribution/final_score*100 if final_score > 0 else 0:.1f}% of total)")
        print(f"   🎯 Final Score: {final_score:.3f} -> {round(final_score * 100, 2)}%")
        
        # 5. Generar explicación detallada
        explanation = self._generate_explanation(
            semantic_similarity, skill_score, experience_score, education_score,
            cv_entities, syllabus_entities
        )
        
        return {
            'final_score': round(final_score * 100, 2),  # Convertir a porcentaje
            'component_scores': {
                'semantic_similarity': round(semantic_similarity * 100, 2),
                'skill_match': round(skill_score * 100, 2),
                'experience_match': round(experience_score * 100, 2),
                'education_match': round(education_score * 100, 2)
            },
            'explanation': explanation
        }

    def _calculate_skill_compatibility(self, cv_skills: List[str], required_skills: List[str]) -> float:
        """
        Calcula la compatibilidad entre las habilidades del CV y las requeridas.
        
        Args:
            cv_skills: Lista de habilidades técnicas del docente
            required_skills: Lista de habilidades requeridas para el curso
            
        Returns:
            Score de compatibilidad (0.0 a 1.0)
        """
        print(f"      🔧 Skills Debug:")
        print(f"         CV Skills raw: {cv_skills}")
        print(f"         Required Skills raw: {required_skills}")
        
        if not required_skills:
            print(f"         No required skills -> score = 1.0")
            return 1.0  # Si no hay requisitos específicos, score máximo
        
        if not cv_skills:
            print(f"         No CV skills -> score = 0.0")
            return 0.0  # Si el docente no tiene habilidades listadas
        
        # Normalizar a minúsculas para comparación
        cv_skills_lower = [skill.lower().strip() for skill in cv_skills]
        required_skills_lower = [skill.lower().strip() for skill in required_skills]
        
        # Calcular intersección exacta
        exact_matches = len(set(cv_skills_lower) & set(required_skills_lower))
        
        # Calcular matches parciales (palabras clave comunes)
        partial_matches = 0
        for req_skill in required_skills_lower:
            for cv_skill in cv_skills_lower:
                if req_skill in cv_skill or cv_skill in req_skill:
                    partial_matches += 0.5  # Peso menor para matches parciales
                    break
        
        total_matches = exact_matches + partial_matches
        max_possible_matches = len(required_skills_lower)
        
        final_skill_score = min(1.0, total_matches / max_possible_matches)
        
        print(f"         Exact matches: {exact_matches}")
        print(f"         Partial matches: {partial_matches}")
        print(f"         Total matches: {total_matches}")
        print(f"         Max possible: {max_possible_matches}")
        print(f"         Final skill score: {final_skill_score:.3f}")
        
        return final_skill_score

    def _calculate_experience_compatibility(self, cv_experience_years: int, syllabus_entities: Dict) -> float:
        """
        Calcula la compatibilidad basada en años de experiencia.
        
        Args:
            cv_experience_years: Años de experiencia del docente
            syllabus_entities: Entidades del sílabo para inferir nivel requerido
            
        Returns:
            Score de compatibilidad (0.0 a 1.0)
        """
        # Inferir experiencia requerida basándose en el contenido del curso
        required_experience = self._infer_required_experience(syllabus_entities)
        
        if cv_experience_years == 0:
            return 0.3  # Score mínimo si no se puede determinar experiencia
        
        if cv_experience_years >= required_experience:
            # Experiencia suficiente o más
            if cv_experience_years <= required_experience * 2:
                return 1.0  # Experiencia ideal
            else:
                # Demasiada experiencia puede ser sobre-calificación
                return 0.8
        else:
            # Menos experiencia de la requerida
            ratio = cv_experience_years / required_experience
            return max(0.1, ratio)  # Score mínimo del 10%

    def _infer_required_experience(self, syllabus_entities: Dict) -> int:
        """
        Infiere los años de experiencia requeridos basándose en el contenido del curso.
        
        Args:
            syllabus_entities: Entidades extraídas del sílabo
            
        Returns:
            Años de experiencia estimados requeridos
        """
        required_skills = syllabus_entities.get('required_skills', [])
        course_topics = syllabus_entities.get('course_topics', [])
        
        # Palabras clave que indican nivel avanzado
        advanced_keywords = [
            'avanzado', 'advanced', 'senior', 'expert', 'arquitectura', 'architecture',
            'microservices', 'machine learning', 'deep learning', 'devops', 'cloud'
        ]
        
        # Palabras clave que indican nivel intermedio
        intermediate_keywords = [
            'intermedio', 'intermediate', 'desarrollo', 'development', 'frameworks',
            'apis', 'databases', 'web development'
        ]
        
        all_text = ' '.join(required_skills + course_topics).lower()
        
        if any(keyword in all_text for keyword in advanced_keywords):
            return 5  # 5+ años para cursos avanzados
        elif any(keyword in all_text for keyword in intermediate_keywords):
            return 3  # 3+ años para cursos intermedios
        else:
            return 1  # 1+ año para cursos básicos

    def _calculate_education_compatibility(self, cv_education: List[str], course_topics: List[str]) -> float:
        """
        Calcula compatibilidad basada en background educativo.
        
        Args:
            cv_education: Lista de instituciones educativas del docente
            course_topics: Temas del curso
            
        Returns:
            Score de compatibilidad (0.0 a 1.0)
        """
        if not cv_education:
            return 0.5  # Score neutro si no hay información educativa
        
        # Por ahora, score básico basado en si tiene educación universitaria
        has_university = any(
            keyword in edu.lower() 
            for edu in cv_education 
            for keyword in ['universidad', 'university', 'institute']
        )
        
        return 0.8 if has_university else 0.5

    def _generate_explanation(self, semantic_sim: float, skill_score: float, 
                            exp_score: float, edu_score: float,
                            cv_entities: Dict, syllabus_entities: Dict) -> Dict:
        """
        Genera una explicación detallada del matching.
        
        Returns:
            Diccionario con explicación detallada
        """
        cv_skills = cv_entities.get('technical_skills', [])
        required_skills = syllabus_entities.get('required_skills', [])
        cv_experience = cv_entities.get('experience_years', 0)
        
        # Encontrar habilidades coincidentes
        matching_skills = []
        missing_skills = []
        
        if required_skills:
            cv_skills_lower = [skill.lower() for skill in cv_skills]
            for req_skill in required_skills:
                if req_skill.lower() in cv_skills_lower:
                    matching_skills.append(req_skill)
                else:
                    missing_skills.append(req_skill)
        
        # Generar factores clave
        key_factors = []
        
        if matching_skills:
            key_factors.append(f"Habilidades coincidentes: {', '.join(matching_skills[:3])}")
        
        if cv_experience > 0:
            key_factors.append(f"{cv_experience} años de experiencia")
        
        if skill_score > 0.8:
            key_factors.append("Excelente match de habilidades técnicas")
        elif skill_score > 0.6:
            key_factors.append("Buen match de habilidades técnicas")
        
        if semantic_sim > 0.8:
            key_factors.append("Alta similitud semántica del perfil")
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'key_factors': key_factors,
            'experience_years': cv_experience,
            'score_breakdown': f"Semántico: {semantic_sim*100:.1f}%, Habilidades: {skill_score*100:.1f}%, Experiencia: {exp_score*100:.1f}%"
        }

    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        Ordena una lista de candidatos por su score final.
        
        Args:
            candidates: Lista de diccionarios con información de matching
            
        Returns:
            Lista ordenada de candidatos
        """
        print(f"\n🏆 DEBUG Ranking - Antes del ordenamiento:")
        for i, candidate in enumerate(candidates):
            print(f"   {i+1}. {candidate.get('teacher_name', 'Unknown')}: {candidate.get('score', candidate.get('final_score', 0))}%")
        
        # Ordenar por score (puede ser 'score' o 'final_score' dependiendo de la estructura)
        sorted_candidates = sorted(candidates, key=lambda x: x.get('score', x.get('final_score', 0)), reverse=True)
        
        print(f"\n🏆 DEBUG Ranking - Después del ordenamiento:")
        for i, candidate in enumerate(sorted_candidates):
            print(f"   {i+1}. {candidate.get('teacher_name', 'Unknown')}: {candidate.get('score', candidate.get('final_score', 0))}%")
        
        return sorted_candidates


# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    matching_service = AdvancedMatchingService()
    
    # Datos de ejemplo
    cv_entities = {
        'technical_skills': ['python', 'django', 'react', 'aws'],
        'experience_years': 5,
        'education': ['Universidad Nacional'],
        'certifications': ['AWS Certified']
    }
    
    syllabus_entities = {
        'required_skills': ['python', 'web development', 'databases'],
        'course_topics': ['desarrollo web', 'frameworks', 'apis'],
        'prerequisites': ['programación básica']
    }
    
    semantic_similarity = 0.85  # Ejemplo de similitud semántica de SBERT
    
    result = matching_service.calculate_advanced_match(
        cv_entities, syllabus_entities, semantic_similarity
    )
    
    print("--- Resultado de Matching Avanzado ---")
    print(f"Score Final: {result['final_score']}%")
    print(f"Scores por Componente: {result['component_scores']}")
    print(f"Explicación: {result['explanation']}")
