import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AppContext } from '../App';
import { ArrowLeft, FolderFill, FileText, Trophy, ChevronRight } from 'react-bootstrap-icons';

// 🔧 Usar ngrok URL para producción, localhost para desarrollo
const API_URL = 'https://scabrous-nestor-geometrically.ngrok-free.dev/api';

// Configurar Axios para incluir header de ngrok en todas las peticiones
axios.defaults.headers.common['ngrok-skip-browser-warning'] = 'true';

function MainView() {
  const { config } = useContext(AppContext);
  const [currentView, setCurrentView] = useState('cycles'); // 'cycles', 'courses', 'recommendations'
  const [cycles, setCycles] = useState([]);
  const [currentCycle, setCurrentCycle] = useState(null);
  const [courses, setCourses] = useState([]);
  const [currentCourse, setCurrentCourse] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Cargar ciclos al montar el componente
  useEffect(() => {
    if (!config?.syllabusFolderId) return;
    loadCycles();
  }, [config]);

  const loadCycles = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API_URL}/courses/structure/${config.syllabusFolderId}`);
      const structure = response.data.structure;
      
      // Filtrar solo las carpetas que parecen ciclos (CICLO 1, CICLO 2, etc.)
      const cycleData = structure.filter(item => 
        item.type === 'folder' && 
        item.name.toLowerCase().includes('ciclo')
      ).sort((a, b) => {
        // Ordenar numéricamente por número de ciclo
        const numA = parseInt(a.name.match(/\d+/)?.[0] || 0);
        const numB = parseInt(b.name.match(/\d+/)?.[0] || 0);
        return numA - numB;
      });
      
      setCycles(cycleData);
    } catch (err) {
      setError('Error al cargar los ciclos.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCoursesFromCycle = async (cycle) => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API_URL}/courses/structure/${cycle.id}`);
      const structure = response.data.structure;
      
      // Obtener todos los archivos PDF y carpetas de cursos
      const courseData = structure.filter(item => 
        item.type === 'folder' || 
        (item.type === 'file' && item.name.toLowerCase().endsWith('.pdf'))
      );
      
      setCourses(courseData);
      setCurrentCycle(cycle);
      setCurrentView('courses');
    } catch (err) {
      setError(`Error al cargar cursos del ${cycle.name}.`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async (course) => {
    try {
      setLoading(true);
      setCurrentCourse(course);
      setRecommendations(null);
      setError('');
      
      // 🆕 Usar el nuevo endpoint híbrido SQL + ChromaDB
      const response = await axios.post(`${API_URL}/recommendations/generate-hybrid`, {
        cycle_name: currentCycle.name,
        course_name: course.name
      });
      setRecommendations(response.data);
      setCurrentView('recommendations');
    } catch (err) {
      setError(`Error al obtener recomendaciones para ${course.name}.`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    if (currentView === 'recommendations') {
      setCurrentView('courses');
      setRecommendations(null);
      setCurrentCourse(null);
    } else if (currentView === 'courses') {
      setCurrentView('cycles');
      setCourses([]);
      setCurrentCycle(null);
    }
  };

  const renderBreadcrumb = () => (
    <div className="breadcrumb">
      <span className="breadcrumb-item">Sistema</span>
      {currentCycle && (
        <>
          <ChevronRight size={16} />
          <span className="breadcrumb-item">{currentCycle.name}</span>
        </>
      )}
      {currentCourse && (
        <>
          <ChevronRight size={16} />
          <span className="breadcrumb-item active">{currentCourse.name}</span>
        </>
      )}
    </div>
  );

  const renderCycles = () => (
    <div className="cycles-view">
      <div className="view-header">
        <h2>Selecciona un Ciclo Académico</h2>
        <p>Explora los cursos organizados por ciclos</p>
      </div>
      
      {loading && <div className="loading">Cargando ciclos...</div>}
      {error && <div className="error">{error}</div>}
      
      <div className="cycles-grid">
        {cycles.map(cycle => (
          <div 
            key={cycle.id} 
            className="cycle-card"
            onClick={() => loadCoursesFromCycle(cycle)}
          >
            <div className="cycle-icon">
              <FolderFill size={40} />
            </div>
            <h3>{cycle.name}</h3>
            <p>Explorar cursos</p>
            <ChevronRight size={20} className="cycle-arrow" />
          </div>
        ))}
      </div>
    </div>
  );

  const renderCourses = () => (
    <div className="courses-view">
      <div className="view-header">
        <button className="back-btn" onClick={goBack}>
          <ArrowLeft size={20} />
          Volver a Ciclos
        </button>
        <h2>Cursos de {currentCycle?.name}</h2>
        <p>Selecciona un curso para ver recomendaciones de docentes</p>
      </div>
      
      {loading && <div className="loading">Cargando cursos...</div>}
      {error && <div className="error">{error}</div>}
      
      <div className="courses-grid">
        {courses.map(course => (
          <div 
            key={course.id} 
            className="course-card"
            onClick={() => course.type === 'file' ? loadRecommendations(course) : null}
          >
            <div className="course-icon">
              {course.type === 'file' ? (
                <FileText size={30} />
              ) : (
                <FolderFill size={30} />
              )}
            </div>
            <h4>{course.name.replace('.pdf', '')}</h4>
            {course.type === 'file' && (
              <>
                <p>Ver recomendaciones</p>
                <ChevronRight size={16} className="course-arrow" />
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="recommendations-view">
      <div className="view-header">
        <button className="back-btn" onClick={goBack}>
          <ArrowLeft size={20} />
          Volver a Cursos
        </button>
        <h2>
          <Trophy size={24} />
          Ranking de Docentes
        </h2>
        <p>Para: {currentCourse?.name.replace('.pdf', '')}</p>
      </div>
      
      {loading && <div className="loading">Generando recomendaciones...</div>}
      {error && <div className="error">{error}</div>}
      
      {recommendations && (
        <div className="recommendations-container">
          <div className="course-info">
            <h4>Información del Curso:</h4>
            <p><strong>Habilidades requeridas:</strong> {recommendations.syllabus_info?.required_skills?.join(', ') || 'No especificadas'}</p>
            <p><strong>Temas del curso:</strong> {recommendations.syllabus_info?.course_topics?.join(', ') || 'No especificados'}</p>
          </div>
          
          <div className="recommendations-table">
            <table>
              <thead>
                <tr>
                  <th>Ranking</th>
                  <th>Nombre del Docente</th>
                  <th>Score Final</th>
                  <th>Componentes</th>
                  <th>Habilidades Coincidentes</th>
                </tr>
              </thead>
              <tbody>
                {recommendations.recommendations.map((rec, index) => {
                  // 🆕 Compatibilidad con endpoint híbrido (score 0-1) vs antiguo (final_score 0-100)
                  const finalScore = rec.final_score ? rec.final_score : (rec.score * 100).toFixed(1);
                  const semanticScore = rec.component_scores.semantic_similarity ? 
                    (rec.component_scores.semantic_similarity > 1 ? 
                      rec.component_scores.semantic_similarity : 
                      (rec.component_scores.semantic_similarity * 100).toFixed(1)) : 
                    'N/A';
                  const sqlScore = rec.component_scores.sql_score ? 
                    (rec.component_scores.sql_score * 100).toFixed(1) : 
                    rec.component_scores.skill_match || 'N/A';
                  const experienceScore = rec.component_scores.experience_match || 'N/A';
                  
                  // Compatibilidad: matched_skills (híbrido) o matching_skills (antiguo)
                  const matchedSkills = rec.explanation.matched_skills || rec.explanation.matching_skills || [];
                  
                  return (
                    <tr key={index}>
                      <td className="ranking-cell">
                        <div className="ranking-badge">{index + 1}</div>
                      </td>
                      <td>{rec.teacher_name}</td>
                      <td className="score-cell">{finalScore}%</td>
                      <td className="components-cell">
                        <div>
                          <small>Semántico: {semanticScore}%</small><br/>
                          <small>SQL Skills: {sqlScore}%</small><br/>
                          {experienceScore !== 'N/A' && <small>Experiencia: {experienceScore}%</small>}
                        </div>
                      </td>
                      <td className="skills-cell">
                        {matchedSkills.length > 0 ? (
                          <span className="matching-skills">
                            {matchedSkills.slice(0, 3).join(', ')}
                            {matchedSkills.length > 3 && ` (+${matchedSkills.length - 3} más)`}
                          </span>
                        ) : (
                          <span className="no-skills">Sin coincidencias específicas</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          
          <div className="analysis-summary">
            <p><strong>Total de candidatos analizados:</strong> {recommendations.total_analyzed}</p>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="main-view">
      {renderBreadcrumb()}
      
      {currentView === 'cycles' && renderCycles()}
      {currentView === 'courses' && renderCourses()}
      {currentView === 'recommendations' && renderRecommendations()}
    </div>
  );
}

export default MainView;
