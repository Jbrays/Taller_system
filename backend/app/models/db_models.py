"""
Modelos de base de datos SQL para metadata estructurada.

Este módulo define las tablas relacionales para almacenar información
estructurada de docentes, cursos y habilidades.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Tabla intermedia para relación muchos-a-muchos: teachers <-> skills
teacher_skills = Table(
    'teacher_skills',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True),
    Column('proficiency_level', String, default='intermediate')  # beginner, intermediate, advanced
)

# Tabla intermedia para relación muchos-a-muchos: courses <-> skills
course_requirements = Table(
    'course_requirements',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True),
    Column('importance', String, default='required')  # required, preferred, optional
)


class Teacher(Base):
    """Modelo para almacenar información estructurada de docentes."""
    
    __tablename__ = 'teachers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    embedding_id = Column(String(255), unique=True)  # ID en ChromaDB
    experience_years = Column(Integer, default=0)
    email = Column(String(255))
    
    # Relaciones
    skills = relationship('Skill', secondary=teacher_skills, back_populates='teachers')
    
    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.name}', experience={self.experience_years})>"


class Skill(Base):
    """Modelo para habilidades técnicas únicas (sin duplicados)."""
    
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))  # language, framework, tool, database, methodology
    
    # Relaciones
    teachers = relationship('Teacher', secondary=teacher_skills, back_populates='skills')
    courses = relationship('Course', secondary=course_requirements, back_populates='required_skills')
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class Course(Base):
    """Modelo para cursos académicos."""
    
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    cycle = Column(String(50))
    embedding_id = Column(String(255), unique=True)  # ID en ChromaDB
    credits = Column(Integer)
    
    # Relaciones
    required_skills = relationship('Skill', secondary=course_requirements, back_populates='courses')
    
    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}', cycle='{self.cycle}')>"


class MatchingResult(Base):
    """Modelo para almacenar resultados de matching (historial)."""
    
    __tablename__ = 'matching_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    sql_score = Column(Float)  # Score basado en coincidencia de skills
    semantic_score = Column(Float)  # Score basado en SBERT
    final_score = Column(Float)  # Score combinado
    matched_skills_count = Column(Integer)
    created_at = Column(String(50))  # Timestamp
    
    # Relaciones
    teacher = relationship('Teacher')
    course = relationship('Course')
    
    def __repr__(self):
        return f"<MatchingResult(teacher_id={self.teacher_id}, course_id={self.course_id}, score={self.final_score})>"
