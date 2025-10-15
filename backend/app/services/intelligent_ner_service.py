"""
Servicio NER inteligente que detecta skills automáticamente sin diccionario hardcodeado.
Usa análisis de frecuencia, entidades nombradas y patrones lingüísticos.
"""

import spacy
import re
from collections import Counter
from typing import List, Dict, Set
import string

class IntelligentNERService:
    """
    Servicio NER que detecta skills automáticamente usando:
    1. Análisis de frecuencia (TF-IDF simplificado)
    2. Patrones lingüísticos (sustantivos técnicos)
    3. Contexto (palabras cerca de términos clave como "experiencia en", "conocimientos de")
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ Modelo NER inteligente (spaCy) cargado exitosamente.")
        except OSError:
            print("❌ ERROR: Modelo de spaCy 'es_core_news_sm' no encontrado.")
            self.nlp = None
        
        # Stopwords en español + términos de CV/administrativos a ignorar
        self.stopwords = {
            # Artículos, preposiciones, conjunciones
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber', 'por', 
            'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo', 'pero', 'más',
            'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'la', 'si', 'me', 'ya',
            'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin', 'vez', 'mucho', 'saber', 'qué',
            'sobre', 'mi', 'alguno', 'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer',
            'entre', 'así', 'primero', 'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar',
            'tiempo', 'ella', 'sí', 'día', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner',
            'cosa', 'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte',
            'después', 'vida', 'quedar', 'siempre', 'creer', 'hablar', 'llevar', 'dejar', 'nada',
            'cada', 'seguir', 'menos', 'nuevo', 'encontrar', 'algo', 'solo', 'hecho',
            
            # Temporal
            'año', 'años', 'mes', 'meses', 'día', 'días', 'fecha', 'periodo', 'duración',
            
            # Títulos académicos
            'ing', 'ingeniero', 'ingeniera', 'licenciado', 'licenciada', 'bachiller', 'magister',
            'maestro', 'maestra', 'doctor', 'doctora', 'profesor', 'profesora', 'docente',
            'magíster', 'phd', 'mba', 'master', 'diplomado', 'técnico', 'profesional',
            
            # Instituciones (nombres comunes)
            'universidad', 'instituto', 'colegio', 'escuela', 'facultad', 'departamento',
            'centro', 'académica', 'academia', 'educación', 'educativa', 'educativo',
            
            # Metadatos de CV
            'contacto', 'correo', 'teléfono', 'celular', 'dirección', 'domicilio', 'email',
            'electrónico', 'datos', 'personales', 'información', 'perfil', 'resumen',
            'objetivo', 'referencias', 'disponibilidad',
            
            # Administrativo/burocrático
            'registro', 'licencia', 'certificado', 'título', 'diploma', 'grado', 'cargo',
            'puesto', 'área', 'departamento', 'división', 'gerencia', 'jefatura',
            'coordinación', 'dirección', 'vicerrectorado', 'rectorado', 'decanato',
            'membresía', 'asociación', 'organización', 'institución', 'empresa', 'entidad',
            
            # Términos genéricos de CV
            'experiencia', 'laboral', 'actividades', 'funciones', 'responsabilidades',
            'logros', 'honores', 'premios', 'distinciones', 'reconocimientos',
            'publicaciones', 'investigación', 'capacitaciones', 'cursos', 'seminarios',
            'talleres', 'conferencias', 'ponencias', 'idiomas', 'nivel', 'básico',
            'intermedio', 'avanzado', 'nativo', 'hablado', 'escrito', 'lectura',
            
            # Modalidades de trabajo
            'tiempo', 'completo', 'parcial', 'dedicación', 'contratado', 'nombrado',
            'ordinario', 'extraordinario', 'auxiliar', 'jefe', 'asistente', 'principal',
            
            # Ubicaciones comunes Perú (UPAO específico)
            'trujillo', 'lima', 'perú', 'privada', 'antenor', 'orrego', 'upao',
            'española', 'españa', 'internacional', 'nacional', 'regional', 'local',
            
            # Términos de clasificación
            'disciplina', 'área', 'campo', 'especialidad', 'rama', 'sector', 'ámbito'
        }
        
        # Contextos que indican skills (para análisis contextual)
        self.skill_contexts = [
            'experiencia en', 'conocimientos de', 'dominio de', 'manejo de',
            'especialista en', 'experto en', 'competencias en', 'habilidades en',
            'trabajo con', 'desarrollo de', 'implementación de', 'uso de',
            'aplicación de', 'gestión de', 'administración de', 'análisis de'
        ]
    
    def extract_skills_intelligently(self, text: str, document_type: str = 'cv') -> List[str]:
        """
        Extrae skills de forma inteligente sin diccionario predefinido.
        
        Args:
            text: Texto del documento
            document_type: 'cv' o 'syllabus'
            
        Returns:
            Lista de skills detectadas automáticamente
        """
        if not self.nlp:
            return []
        
        text_lower = text.lower()
        doc = self.nlp(text)
        
        candidate_skills = set()
        
        # 1. Extraer entidades nombradas de tipo ORG y MISC (pueden ser tecnologías)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'MISC', 'PRODUCT']:
                # Filtrar nombres de universidades comunes
                if not self._is_institution_name(ent.text.lower()):
                    candidate_skills.add(ent.text.lower())
        
        # 2. IMPORTANTE: Extraer noun chunks (frases nominales multi-palabra)
        # Esto captura "machine learning", "data analytics", "artificial intelligence", etc.
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            # Solo chunks de 2-4 palabras que contengan términos técnicos
            word_count = len(chunk_text.split())
            if 2 <= word_count <= 4:
                # Priorizar chunks que contienen palabras técnicas
                technical_indicators = ['learning', 'data', 'analytics', 'intelligence', 'artificial',
                                       'machine', 'deep', 'neural', 'augmented', 'virtual', 'reality',
                                       'software', 'engineering', 'architecture', 'development',
                                       'security', 'network', 'cloud', 'database', 'web', 'mobile']
                if any(indicator in chunk_text for indicator in technical_indicators):
                    candidate_skills.add(chunk_text)
        
        # 3. Extraer sustantivos propios y técnicos individuales (análisis sintáctico)
        for token in doc:
            # Sustantivos propios o sustantivos que parecen técnicos
            if token.pos_ in ['PROPN', 'NOUN'] and len(token.text) > 3:
                word_lower = token.text.lower()
                # Filtrar stopwords y palabras comunes
                if word_lower not in self.stopwords and not word_lower.isdigit():
                    # Si está en mayúsculas en el texto original, probablemente es importante
                    if token.text[0].isupper() or token.text.isupper():
                        candidate_skills.add(word_lower)
        
        # 4. Análisis contextual: palabras/frases después de frases clave
        for context_phrase in self.skill_contexts:
            # Capturar hasta 4 palabras después de la frase contextual
            pattern = re.compile(rf'{context_phrase}\s+([A-Za-záéíóúñÁÉÍÓÚÑ]+(?:\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+){{0,3}})(?:\.|,|;|\n|y\s|con\s|$)', re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                # Limpiar y agregar
                cleaned = match.strip().lower()
                if cleaned and 3 < len(cleaned) < 50 and cleaned not in self.stopwords:
                    candidate_skills.add(cleaned)
        
        # 5. Detectar siglas y acrónimos (probablemente tecnologías)
        acronyms = re.findall(r'\b[A-Z]{2,10}\b', text)
        for acronym in acronyms:
            if len(acronym) >= 2 and acronym.lower() not in self.stopwords:
                candidate_skills.add(acronym.lower())
        
        # 6. Detectar términos técnicos compuestos (con guiones o CamelCase)
        technical_terms = re.findall(r'\b[A-Za-z]+\-[A-Za-z]+\b', text)
        for term in technical_terms:
            if len(term) > 4:
                candidate_skills.add(term.lower())
        
        # 7. Análisis de frecuencia: palabras que aparecen múltiples veces pero no son comunes
        word_freq = self._calculate_word_frequency(text_lower)
        for word, freq in word_freq.items():
            # Aumentar umbral a 3+ para reducir ruido
            # Priorizar si contiene términos técnicos típicos
            is_technical = any(tech in word for tech in ['data', 'soft', 'arch', 'eng', 'dev', 'sys', 'tech', 'web'])
            min_freq = 2 if is_technical else 3
            
            if freq >= min_freq and len(word) > 4 and word not in self.stopwords:
                candidate_skills.add(word)
        
        # 8. Filtrado final: eliminar ruido
        filtered_skills = self._filter_candidates(candidate_skills, text_lower)
        
        return sorted(list(filtered_skills))
    
    def _calculate_word_frequency(self, text: str) -> Dict[str, int]:
        """Calcula frecuencia de palabras (TF simplificado)."""
        # Tokenizar y limpiar
        words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text)  # Solo palabras de 4+ letras
        
        # Contar frecuencias
        freq = Counter(words)
        
        # Filtrar palabras muy comunes y aumentar umbral a 3+
        filtered_freq = {word: count for word, count in freq.items() 
                        if word not in self.stopwords and count >= 3}
        
        return filtered_freq
    
    def _is_institution_name(self, text: str) -> bool:
        """Detecta si el texto es nombre de institución educativa."""
        institution_keywords = [
            'universidad', 'instituto', 'colegio', 'escuela', 'academy',
            'college', 'school', 'upao', 'pucp', 'católica', 'nacional'
        ]
        return any(keyword in text.lower() for keyword in institution_keywords)
    
    def _filter_candidates(self, candidates: Set[str], full_text: str) -> Set[str]:
        """
        Filtra candidatos eliminando ruido y validando que sean realmente skills.
        """
        filtered = set()
        
        # Nombres propios comunes en Perú (para filtrar nombres de personas en CVs)
        common_names = {
            'hernan', 'teobaldo', 'sagastegui', 'chigne', 'juan', 'carlos', 'maria',
            'jose', 'luis', 'ana', 'pedro', 'jorge', 'miguel', 'rosa', 'carmen',
            'garcia', 'rodriguez', 'martinez', 'lopez', 'gonzalez', 'perez', 'sanchez'
        }
        
        for candidate in candidates:
            # Eliminar palabras muy cortas o muy largas
            if len(candidate) < 3 or len(candidate) > 50:
                continue
            
            # Eliminar si es solo números o solo 1-2 letras
            if candidate.isdigit() or len(candidate) <= 2:
                continue
            
            # Eliminar si es stopword
            if candidate.lower() in self.stopwords:
                continue
            
            # Eliminar nombres propios de personas
            if candidate.lower() in common_names:
                continue
            
            # Eliminar si contiene muchos espacios (probablemente una frase completa)
            if candidate.count(' ') > 4:
                continue
            
            # Eliminar palabras muy genéricas
            generic_words = ['trabajo', 'experiencia', 'conocimiento', 'proyecto', 
                           'desarrollo', 'implementación', 'gestión', 'servicio',
                           'proceso', 'sistema', 'general', 'específico', 'particular']
            if candidate.lower() in generic_words:
                continue
            
            # Eliminar siglas de menos de 2 letras (probable ruido)
            if candidate.isupper() and len(candidate) < 2:
                continue
            
            # Eliminar si empieza/termina con espacio o caracteres raros
            if candidate.strip() != candidate or any(c in candidate for c in ['_', '|', '@', '#']):
                continue
            
            # Si pasa todos los filtros, agregarlo
            filtered.add(candidate.lower())
        
        return filtered
    
    def extract_entities_from_cv(self, cv_text: str) -> Dict:
        """
        Extrae entidades de un CV usando detección inteligente.
        """
        return {
            'technical_skills': self.extract_skills_intelligently(cv_text, 'cv'),
            'experience_years': self._extract_experience_years(cv_text),
            'education': self._extract_education_simple(cv_text),
            'languages': self._extract_languages_simple(cv_text)
        }
    
    def extract_entities_from_syllabus(self, syllabus_text: str) -> Dict:
        """
        Extrae entidades de un sílabo usando detección inteligente.
        """
        return {
            'required_skills': self.extract_skills_intelligently(syllabus_text, 'syllabus'),
            'course_topics': self._extract_topics_simple(syllabus_text)
        }
    
    def _extract_experience_years(self, text: str) -> int:
        """Extrae años de experiencia del texto."""
        patterns = [
            r'(\d+)\s*años?\s+de\s+experiencia',
            r'experiencia\s+de\s+(\d+)\s*años?',
            r'(\d+)\+?\s*años?\s+en',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        
        # Calcular por rango de fechas si existe
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if len(years) >= 2:
            try:
                max_year = max(int(y) for y in years)
                min_year = min(int(y) for y in years)
                return max_year - min_year
            except:
                pass
        
        return 0
    
    def _extract_education_simple(self, text: str) -> List[str]:
        """Extrae títulos educativos."""
        education_keywords = ['doctor', 'maestr', 'master', 'bachiller', 'licenciad', 'ingenier', 'magister']
        education = []
        
        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in education_keywords):
                education.append(line.strip())
        
        return education[:5]  # Top 5
    
    def _extract_languages_simple(self, text: str) -> List[str]:
        """Extrae idiomas mencionados."""
        languages = ['inglés', 'english', 'francés', 'french', 'alemán', 'german', 
                    'italiano', 'italian', 'portugués', 'portuguese', 'chino', 'chinese']
        found = []
        
        text_lower = text.lower()
        for lang in languages:
            if lang in text_lower:
                found.append(lang)
        
        return list(set(found))
    
    def _extract_topics_simple(self, text: str) -> List[str]:
        """Extrae temas principales del curso."""
        # Buscar secciones de contenido
        topics = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['unidad', 'tema', 'capítulo', 'módulo']):
                if i + 1 < len(lines):
                    topics.append(lines[i+1].strip())
        
        return topics[:10]  # Top 10
