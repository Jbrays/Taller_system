import spacy
import re
from typing import List, Dict, Tuple
from datetime import datetime

class NERService:
    """
    Servicio para extracción de entidades nombradas (NER) de CVs y sílabos.
    Utiliza spaCy para identificar habilidades, experiencia, instituciones, etc.
    """
    def __init__(self):
        """
        Inicializa el modelo de spaCy para español.
        """
        try:
            # Cargar modelo de spaCy para español
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ Modelo NER (spaCy) cargado exitosamente.")
        except OSError:
            print("❌ ERROR: Modelo de spaCy 'es_core_news_sm' no encontrado.")
            print("Instálalo con: python -m spacy download es_core_news_sm")
            self.nlp = None

        # Patrones de habilidades técnicas comunes
        self.technical_skills = {
            'languages': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'rails', 'express'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra'],
            'tools': ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'linux', 'nginx'],
            'ml_ai': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy']
        }

    def extract_entities_from_cv(self, cv_text: str) -> Dict:
        """
        Extrae entidades clave de un CV.
        
        Args:
            cv_text: Texto completo del CV
            
        Returns:
            Diccionario con entidades extraídas
        """
        if not self.nlp:
            return self._fallback_extraction(cv_text)

        doc = self.nlp(cv_text)
        
        return {
            'technical_skills': self._extract_technical_skills(cv_text.lower()),
            'experience_years': self._extract_experience_years(cv_text),
            'education': self._extract_education_info(doc),
            'organizations': self._extract_organizations(doc),
            'certifications': self._extract_certifications(cv_text),
            'languages': self._extract_languages(cv_text)
        }

    def extract_entities_from_syllabus(self, syllabus_text: str) -> Dict:
        """
        Extrae entidades clave de un sílabo.
        
        Args:
            syllabus_text: Texto completo del sílabo
            
        Returns:
            Diccionario con entidades extraídas
        """
        if not self.nlp:
            return self._fallback_syllabus_extraction(syllabus_text)

        doc = self.nlp(syllabus_text)
        
        return {
            'required_skills': self._extract_technical_skills(syllabus_text.lower()),
            'course_topics': self._extract_course_topics(syllabus_text),
            'prerequisites': self._extract_prerequisites(syllabus_text),
            'methodologies': self._extract_methodologies(syllabus_text),
            'tools_required': self._extract_required_tools(syllabus_text)
        }

    def _extract_technical_skills(self, text: str) -> List[str]:
        """Extrae habilidades técnicas del texto."""
        found_skills = []
        
        for category, skills in self.technical_skills.items():
            for skill in skills:
                if skill in text:
                    found_skills.append(skill)
        
        # Buscar patrones adicionales
        additional_patterns = [
            r'\b(html5?|css3?|sass|scss)\b',
            r'\b(api|rest|graphql|microservices)\b',
            r'\b(agile|scrum|kanban)\b',
            r'\b(devops|ci/cd)\b'
        ]
        
        for pattern in additional_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_skills.extend(matches)
        
        return list(set(found_skills))  # Eliminar duplicados

    def _extract_experience_years(self, text: str) -> int:
        """Extrae años de experiencia del CV."""
        patterns = [
            r'(\d+)\s*años?\s*de\s*experiencia',
            r'experiencia\s*de\s*(\d+)\s*años?',
            r'(\d+)\s*years?\s*of\s*experience',
            r'experience:\s*(\d+)\s*years?'
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = int(match)
                    max_years = max(max_years, years)
                except ValueError:
                    continue
        
        # Si no encuentra años explícitos, intentar calcular por fechas
        if max_years == 0:
            max_years = self._calculate_years_from_dates(text)
        
        return max_years

    def _calculate_years_from_dates(self, text: str) -> int:
        """Calcula años de experiencia basándose en fechas encontradas."""
        # Buscar patrones de años (2020-2023, 2018-presente, etc.)
        date_patterns = [
            r'(20\d{2})\s*-\s*(20\d{2})',  # 2020-2023
            r'(20\d{2})\s*-\s*(presente|actual|now)',  # 2020-presente
        ]
        
        current_year = datetime.now().year
        total_experience = 0
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                start_year = int(match[0])
                if 'presente' in match[1].lower() or 'actual' in match[1].lower() or 'now' in match[1].lower():
                    end_year = current_year
                else:
                    try:
                        end_year = int(match[1])
                    except ValueError:
                        end_year = current_year
                
                experience = max(0, end_year - start_year)
                total_experience += experience
        
        return min(total_experience, 50)  # Máximo razonable de 50 años

    def _extract_education_info(self, doc) -> List[str]:
        """Extrae información educativa usando NER de spaCy."""
        education = []
        
        # Buscar organizaciones que puedan ser universidades
        for ent in doc.ents:
            if ent.label_ == "ORG":
                text = ent.text.lower()
                if any(keyword in text for keyword in ['universidad', 'institute', 'college', 'school']):
                    education.append(ent.text)
        
        return education

    def _extract_organizations(self, doc) -> List[str]:
        """Extrae nombres de organizaciones/empresas."""
        organizations = []
        for ent in doc.ents:
            if ent.label_ == "ORG":
                organizations.append(ent.text)
        return organizations

    def _extract_certifications(self, text: str) -> List[str]:
        """Extrae certificaciones mencionadas."""
        cert_patterns = [
            r'certificado?\s+en\s+([^.,\n]+)',
            r'certificación\s+([^.,\n]+)',
            r'certified?\s+([^.,\n]+)',
            r'aws\s+certified',
            r'microsoft\s+certified',
            r'google\s+certified'
        ]
        
        certifications = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)
        
        return certifications

    def _extract_languages(self, text: str) -> List[str]:
        """Extrae idiomas mencionados."""
        language_patterns = [
            r'\b(español|inglés|francés|alemán|italiano|portugués|chino|japonés)\b',
            r'\b(spanish|english|french|german|italian|portuguese|chinese|japanese)\b'
        ]
        
        languages = []
        for pattern in language_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            languages.extend(matches)
        
        return list(set(languages))

    def _extract_course_topics(self, text: str) -> List[str]:
        """Extrae temas principales del curso."""
        # Buscar después de palabras clave como "temas", "contenido", "unidades"
        topic_patterns = [
            r'temas?[:\s]*([^.]+)',
            r'contenidos?[:\s]*([^.]+)',
            r'unidades?[:\s]*([^.]+)',
            r'topics?[:\s]*([^.]+)'
        ]
        
        topics = []
        for pattern in topic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        
        return topics

    def _extract_prerequisites(self, text: str) -> List[str]:
        """Extrae prerrequisitos del curso."""
        prereq_patterns = [
            r'prerrequisitos?[:\s]*([^.]+)',
            r'requisitos?[:\s]*([^.]+)',
            r'prerequisites?[:\s]*([^.]+)',
            r'requirements?[:\s]*([^.]+)'
        ]
        
        prerequisites = []
        for pattern in prereq_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            prerequisites.extend(matches)
        
        return prerequisites

    def _extract_methodologies(self, text: str) -> List[str]:
        """Extrae metodologías de enseñanza."""
        method_keywords = ['aprendizaje', 'metodología', 'enfoque', 'approach', 'learning']
        methodologies = []
        
        for keyword in method_keywords:
            pattern = rf'{keyword}[^.]*'
            matches = re.findall(pattern, text, re.IGNORECASE)
            methodologies.extend(matches)
        
        return methodologies

    def _extract_required_tools(self, text: str) -> List[str]:
        """Extrae herramientas requeridas para el curso."""
        return self._extract_technical_skills(text.lower())

    def _fallback_extraction(self, text: str) -> Dict:
        """Extracción básica cuando spaCy no está disponible."""
        return {
            'technical_skills': self._extract_technical_skills(text.lower()),
            'experience_years': self._extract_experience_years(text),
            'education': [],
            'organizations': [],
            'certifications': self._extract_certifications(text),
            'languages': self._extract_languages(text)
        }

    def _fallback_syllabus_extraction(self, text: str) -> Dict:
        """Extracción básica de sílabo cuando spaCy no está disponible."""
        return {
            'required_skills': self._extract_technical_skills(text.lower()),
            'course_topics': self._extract_course_topics(text),
            'prerequisites': self._extract_prerequisites(text),
            'methodologies': self._extract_methodologies(text),
            'tools_required': self._extract_required_tools(text)
        }


# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    ner_service = NERService()
    
    # Ejemplo con CV
    cv_sample = """
    Juan Pérez, Ingeniero de Software con 5 años de experiencia en desarrollo web.
    Experiencia con Python, Django, React y AWS. Graduado de la Universidad Nacional.
    Certificado en AWS Solutions Architect. Domina español e inglés.
    """
    
    print("--- Extracción de CV ---")
    cv_entities = ner_service.extract_entities_from_cv(cv_sample)
    for key, value in cv_entities.items():
        print(f"{key}: {value}")
    
    # Ejemplo con sílabo
    syllabus_sample = """
    Curso: Desarrollo Web Avanzado
    Temas: React, Node.js, bases de datos, APIs REST
    Prerrequisitos: Conocimientos básicos de JavaScript y HTML
    Metodología: Aprendizaje basado en proyectos
    """
    
    print("\n--- Extracción de Sílabo ---")
    syllabus_entities = ner_service.extract_entities_from_syllabus(syllabus_sample)
    for key, value in syllabus_entities.items():
        print(f"{key}: {value}")
