"""
Servicio para gestionar la base de datos SQL relacional.
Complementa ChromaDB con metadata estructurada.
"""

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from ..models.db_models import Base, Teacher, Skill, Course, MatchingResult, teacher_skills, course_requirements
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os


class SQLDatabaseService:
    """
    Servicio para operaciones CRUD en la base de datos SQL.
    Trabaja en conjunto con ChromaDB para arquitectura híbrida.
    """
    
    def __init__(self):
        """Inicializa la conexión a SQLite."""
        # Base de datos SQLite en la misma carpeta que ChromaDB
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        
        self.engine = create_engine(db_url, echo=False)  # echo=True para debug
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f"✅ SQL Database inicializada: {db_url}")
    
    # ==================== TEACHERS ====================
    
    def add_teacher(self, name: str, embedding_id: str, skills_list: List[str], 
                   experience_years: int = 0, email: str = None) -> int:
        """
        Agrega un docente con sus habilidades.
        
        Args:
            name: Nombre del docente
            embedding_id: ID del embedding en ChromaDB
            skills_list: Lista de nombres de habilidades
            experience_years: Años de experiencia
            email: Email del docente
            
        Returns:
            ID del docente creado
        """
        # Verificar si ya existe (por embedding_id)
        existing = self.session.query(Teacher).filter_by(embedding_id=embedding_id).first()
        if existing:
            print(f"   Teacher '{name}' ya existe (ID: {existing.id}), actualizando...")
            existing.name = name
            existing.experience_years = experience_years
            if email:
                existing.email = email
            teacher = existing
        else:
            teacher = Teacher(
                name=name,
                embedding_id=embedding_id,
                experience_years=experience_years,
                email=email
            )
            self.session.add(teacher)
        
        # Agregar skills (crear si no existen)
        teacher.skills.clear()  # Limpiar skills existentes
        for skill_name in skills_list:
            if not skill_name or skill_name.strip() == '':
                continue
                
            skill_name_clean = skill_name.strip().lower()
            skill = self.session.query(Skill).filter_by(name=skill_name_clean).first()
            
            if not skill:
                # Crear nueva skill
                skill = Skill(name=skill_name_clean, category=self._categorize_skill(skill_name_clean))
                self.session.add(skill)
            
            if skill not in teacher.skills:
                teacher.skills.append(skill)
        
        self.session.commit()
        return teacher.id
    
    def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        """Obtiene un docente por su ID."""
        return self.session.query(Teacher).filter_by(id=teacher_id).first()
    
    def get_all_teachers(self) -> List[Teacher]:
        """Obtiene todos los docentes."""
        return self.session.query(Teacher).all()
    
    # ==================== COURSES ====================
    
    def add_course(self, name: str, cycle: str, embedding_id: str, 
                  required_skills: List[str], credits: int = None) -> int:
        """
        Agrega un curso con sus habilidades requeridas.
        
        Args:
            name: Nombre del curso
            cycle: Ciclo académico
            embedding_id: ID del embedding en ChromaDB
            required_skills: Lista de habilidades requeridas
            credits: Créditos del curso
            
        Returns:
            ID del curso creado
        """
        # Verificar si ya existe
        existing = self.session.query(Course).filter_by(embedding_id=embedding_id).first()
        if existing:
            print(f"   Course '{name}' ya existe (ID: {existing.id}), actualizando...")
            existing.name = name
            existing.cycle = cycle
            if credits:
                existing.credits = credits
            course = existing
        else:
            course = Course(
                name=name,
                cycle=cycle,
                embedding_id=embedding_id,
                credits=credits
            )
            self.session.add(course)
        
        # Agregar required skills
        course.required_skills.clear()
        for skill_name in required_skills:
            if not skill_name or skill_name.strip() == '':
                continue
                
            skill_name_clean = skill_name.strip().lower()
            skill = self.session.query(Skill).filter_by(name=skill_name_clean).first()
            
            if not skill:
                skill = Skill(name=skill_name_clean, category=self._categorize_skill(skill_name_clean))
                self.session.add(skill)
            
            if skill not in course.required_skills:
                course.required_skills.append(skill)
        
        self.session.commit()
        return course.id
    
    def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Obtiene un curso por su ID."""
        return self.session.query(Course).filter_by(id=course_id).first()
    
    def get_all_courses(self) -> List[Course]:
        """Obtiene todos los cursos."""
        return self.session.query(Course).all()
    
    # ==================== MATCHING ====================
    
    def find_teachers_by_skills(self, required_skill_names: List[str], 
                               min_matches: int = 1) -> List[Tuple[Teacher, int]]:
        """
        Encuentra docentes que tengan al menos min_matches de las skills requeridas.
        
        Args:
            required_skill_names: Lista de nombres de skills requeridas
            min_matches: Número mínimo de coincidencias
            
        Returns:
            Lista de tuplas (Teacher, matching_skills_count) ordenadas por coincidencias
        """
        if not required_skill_names:
            return []
        
        # Normalizar nombres
        skill_names_clean = [s.strip().lower() for s in required_skill_names if s.strip()]
        
        # Query con join y conteo
        results = self.session.query(
            Teacher,
            func.count(Skill.id).label('matching_skills')
        ).join(
            teacher_skills, Teacher.id == teacher_skills.c.teacher_id
        ).join(
            Skill, Skill.id == teacher_skills.c.skill_id
        ).filter(
            Skill.name.in_(skill_names_clean)
        ).group_by(
            Teacher.id
        ).having(
            func.count(Skill.id) >= min_matches
        ).order_by(
            func.count(Skill.id).desc(),
            Teacher.experience_years.desc()
        ).all()
        
        return results
    
    def calculate_sql_match_score(self, teacher_id: int, course_id: int) -> Dict:
        """
        Calcula el score de matching basado en coincidencia de skills.
        
        Returns:
            Dict con score, matched_skills, missing_skills
        """
        teacher = self.get_teacher_by_id(teacher_id)
        course = self.get_course_by_id(course_id)
        
        if not teacher or not course:
            return {'score': 0.0, 'matched_skills': [], 'missing_skills': []}
        
        teacher_skill_names = {s.name for s in teacher.skills}
        required_skill_names = {s.name for s in course.required_skills}
        
        matched_skills = teacher_skill_names.intersection(required_skill_names)
        missing_skills = required_skill_names.difference(teacher_skill_names)
        
        if len(required_skill_names) == 0:
            score = 0.0
        else:
            score = len(matched_skills) / len(required_skill_names)
        
        return {
            'score': score,
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'total_teacher_skills': len(teacher_skill_names),
            'total_required_skills': len(required_skill_names)
        }
    
    def save_matching_result(self, teacher_id: int, course_id: int, 
                            sql_score: float, semantic_score: float, 
                            final_score: float, matched_skills_count: int):
        """Guarda un resultado de matching para historial."""
        result = MatchingResult(
            teacher_id=teacher_id,
            course_id=course_id,
            sql_score=sql_score,
            semantic_score=semantic_score,
            final_score=final_score,
            matched_skills_count=matched_skills_count,
            created_at=datetime.now().isoformat()
        )
        self.session.add(result)
        self.session.commit()
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas generales del sistema."""
        total_teachers = self.session.query(Teacher).count()
        total_courses = self.session.query(Course).count()
        total_skills = self.session.query(Skill).count()
        total_matches = self.session.query(MatchingResult).count()
        
        # Top skills más demandadas
        top_required_skills = self.session.query(
            Skill.name,
            func.count(course_requirements.c.course_id).label('course_count')
        ).join(
            course_requirements, Skill.id == course_requirements.c.skill_id
        ).group_by(
            Skill.name
        ).order_by(
            func.count(course_requirements.c.course_id).desc()
        ).limit(10).all()
        
        # Top skills más comunes en docentes
        top_teacher_skills = self.session.query(
            Skill.name,
            func.count(teacher_skills.c.teacher_id).label('teacher_count')
        ).join(
            teacher_skills, Skill.id == teacher_skills.c.skill_id
        ).group_by(
            Skill.name
        ).order_by(
            func.count(teacher_skills.c.teacher_id).desc()
        ).limit(10).all()
        
        return {
            'total_teachers': total_teachers,
            'total_courses': total_courses,
            'total_skills': total_skills,
            'total_matches_performed': total_matches,
            'top_required_skills': [{'skill': s, 'courses': c} for s, c in top_required_skills],
            'top_teacher_skills': [{'skill': s, 'teachers': c} for s, c in top_teacher_skills]
        }
    
    # ==================== UTILITIES ====================
    
    def _categorize_skill(self, skill_name: str) -> str:
        """Categoriza una skill automáticamente."""
        skill_lower = skill_name.lower()
        
        languages = ['python', 'java', 'javascript', 'js', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift']
        frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'rails', 'express', 'fastapi']
        databases = ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra', 'dynamodb']
        tools = ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'linux', 'nginx']
        ml = ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy']
        
        if skill_lower in languages:
            return 'language'
        elif skill_lower in frameworks:
            return 'framework'
        elif skill_lower in databases:
            return 'database'
        elif skill_lower in tools:
            return 'tool'
        elif skill_lower in ml or 'learning' in skill_lower:
            return 'ml_ai'
        else:
            return 'other'
    
    def close(self):
        """Cierra la conexión a la base de datos."""
        self.session.close()
