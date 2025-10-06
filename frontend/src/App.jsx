import React, { useState, useEffect } from 'react';
import { HashRouter as Router } from 'react-router-dom';
import axios from 'axios';
import SettingsModal from './components/SettingsModal';
import EmptyState from './components/EmptyState-simple';
import './App.css';

const API_URL = 'https://scabrous-nestor-geometrically.ngrok-free.dev/api';

// Creamos un contexto para compartir la configuración
export const AppContext = React.createContext();

function App() {
  const [config, setConfig] = useState(null);
  const [isConfigured, setIsConfigured] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [cycles, setCycles] = useState([]);
  const [selectedCycle, setSelectedCycle] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingRankings, setLoadingRankings] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [error, setError] = useState('');

  // Al cargar, intentar leer la configuración desde localStorage
  useEffect(() => {
    const savedConfig = localStorage.getItem('driveConfig');
    if (savedConfig) {
      const parsedConfig = JSON.parse(savedConfig);
      setConfig(parsedConfig);
      setIsConfigured(true);
    }
  }, []);

  // Cargar ciclos cuando el sistema esté configurado
  useEffect(() => {
    if (isConfigured && config?.syllabusFolderId) {
      loadCycles();
    }
  }, [isConfigured, config]);

  const loadCycles = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API_URL}/courses/structure/${config.syllabusFolderId}`);
      
      // Debug: Ver toda la respuesta
      console.log('Respuesta completa:', response);
      console.log('Response data:', response.data);
      console.log('Response data structure:', response.data?.structure);
      
      // Validar que la respuesta tiene la estructura esperada
      if (!response.data || typeof response.data !== 'object') {
        setError(`Respuesta inválida del servidor. Respuesta recibida: ${JSON.stringify(response.data)}`);
        setCycles([]);
        return;
      }
      
      const structure = response.data.structure;
      
      // Validar que structure existe y es un objeto
      if (!structure || typeof structure !== 'object') {
        setError(`Estructura de datos inválida. Estructura recibida: ${JSON.stringify(structure)}. 
                  ID de carpeta: ${config.syllabusFolderId}`);
        setCycles([]);
        return;
      }
      
      // Debug: Ver qué datos estamos recibiendo
      console.log('Estructura recibida:', structure);
      console.log('Llaves de la estructura:', Object.keys(structure));
      console.log('Tipo de estructura:', typeof structure);
      
      // Verificar si la estructura está vacía
      if (Object.keys(structure).length === 0) {
        setError(`No se encontraron carpetas en el ID proporcionado. 
                  Verifica que la carpeta de sílabos tenga subcarpetas con nombres como "Ciclo 01", "Ciclo I", etc.
                  ID de carpeta utilizado: ${config.syllabusFolderId}`);
        setCycles([]);
        return;
      }
      
      // Ahora el backend devuelve los nombres reales de las carpetas
      // Extraer y procesar los ciclos de la estructura
      const cycleList = Object.keys(structure)
        .filter(cycleKey => {
          // Filtrar solo carpetas que parecen ser ciclos académicos
          return /ciclo/i.test(cycleKey) || /^(I{1,3}V?|V|VI{0,3}|IX|X)$/i.test(cycleKey);
        })
        .map((cycleKey) => {
          console.log('Procesando ciclo key:', cycleKey);
          
          let displayName;
          
          // Normalizar el nombre para mostrar
          const cycleMatch = cycleKey.match(/ciclo\s*(\d+|[IVX]+)/i);
          
          if (cycleMatch) {
            const cycleNumber = cycleMatch[1];
            
            // Convertir números romanos a arábigos si es necesario
            const romanToArabic = {
              'I': '01', 'II': '02', 'III': '03', 'IV': '04', 'V': '05',
              'VI': '06', 'VII': '07', 'VIII': '08', 'IX': '09', 'X': '10'
            };
            
            if (romanToArabic[cycleNumber.toUpperCase()]) {
              displayName = `Ciclo ${romanToArabic[cycleNumber.toUpperCase()]}`;
            } else if (!isNaN(cycleNumber)) {
              const paddedNumber = cycleNumber.padStart(2, '0');
              displayName = `Ciclo ${paddedNumber}`;
            } else {
              displayName = cycleKey; // Usar el nombre original como fallback
            }
          } else {
            // Si no sigue el patrón "Ciclo X", usar el nombre tal como viene
            displayName = cycleKey;
          }
          
          console.log('Display name final:', displayName);
          
          return {
            originalName: cycleKey,
            displayName: displayName,
            courses: Object.keys(structure[cycleKey] || {})
          };
        })
        // Ordenar por display name para mantener orden lógico
        .sort((a, b) => a.displayName.localeCompare(b.displayName));
      
      console.log('Lista final de ciclos:', cycleList);
      setCycles(cycleList);
    } catch (err) {
      console.error('Error loading cycles:', err);
      
      // Mensaje de error más detallado
      let errorMessage = 'Error al cargar los ciclos desde Google Drive.';
      
      if (err.response) {
        errorMessage += ` Estado: ${err.response.status}`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += `. Detalle: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        errorMessage += ' No se pudo conectar con el servidor backend.';
      } else {
        errorMessage += ` Error: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCycleClick = (cycle) => {
    setSelectedCycle(cycle);
    setSelectedCourse(null); // Reset course selection
    setRankings([]); // Reset rankings
  };

  const handleBackToCycles = () => {
    setSelectedCycle(null);
    setSelectedCourse(null);
    setRankings([]);
  };

  const handleCourseClick = async (courseName) => {
    setSelectedCourse(courseName);
    await loadCourseRankings(courseName);
  };

  const handleBackToCourses = () => {
    setSelectedCourse(null);
    setRankings([]);
  };

  const loadCourseRankings = async (courseName) => {
    try {
      setLoadingRankings(true);
      setError('');
      
      // Llamar al endpoint de recomendaciones
      const response = await axios.post(`${API_URL}/recommendations/generate`, {
        cycle_name: selectedCycle.originalName,
        course_name: courseName,
        cv_folder_id: config.cvFolderId,
        syllabus_folder_id: config.syllabusFolderId
      });
      
      console.log('Rankings recibidos:', response.data);
      console.log('Estructura de recommendations:', response.data.recommendations);
      console.log('Primer recommendation:', response.data.recommendations?.[0]);
      
      const recommendations = response.data.recommendations || [];
      console.log('Recommendations procesadas:', recommendations);
      setRankings(recommendations);
    } catch (err) {
      console.error('Error loading rankings:', err);
      setError(`Error al cargar el ranking para ${courseName}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoadingRankings(false);
    }
  };

  const handleSyncData = async () => {
    try {
      setSyncLoading(true);
      setSyncStatus(null);
      setError('');
      
      console.log('Iniciando sincronización con:', {
        cv_folder_id: config.cvFolderId,
        syllabus_folder_id: config.syllabusFolderId
      });
      
      const response = await axios.post(`${API_URL}/sync`, {
        cv_folder_id: config.cvFolderId,
        syllabus_folder_id: config.syllabusFolderId
      });
      
      console.log('Sincronización completada:', response.data);
      setSyncStatus({
        success: true,
        cvs: response.data.processed_cvs,
        syllabi: response.data.processed_syllabi
      });
    } catch (err) {
      console.error('Error en sincronización:', err);
      setError(`Error en la sincronización: ${err.response?.data?.detail || err.message}`);
      setSyncStatus({ success: false });
    } finally {
      setSyncLoading(false);
    }
  };

  const handleSaveSettings = (newConfig) => {
    // Extraer IDs de las URLs
    const cvFolderId = newConfig.cvUrl.split('/folders/')[1]?.split('?')[0];
    const syllabusFolderId = newConfig.syllabusUrl.split('/folders/')[1]?.split('?')[0];

    if (!cvFolderId || !syllabusFolderId) {
      alert("URLs de Google Drive no válidas. Asegúrate de que sean enlaces a carpetas.");
      return;
    }

    const finalConfig = { cvFolderId, syllabusFolderId };
    setConfig(finalConfig);
    setIsConfigured(true);
    localStorage.setItem('driveConfig', JSON.stringify(finalConfig));
    setIsSettingsOpen(false);
    
    // Los ciclos se cargarán automáticamente por el useEffect
  };

  return (
    <AppContext.Provider value={{ config, isConfigured }}>
      <Router>
        <div className="app-container">
          {/* Solo mostrar el botón de configuración cuando NO esté configurado */}
          {!isConfigured && (
            <button className="settings-btn" onClick={() => setIsSettingsOpen(true)}>
              Configurar
            </button>
          )}

          <SettingsModal
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            onSave={handleSaveSettings}
            currentConfig={config}
          />

          <main>
            {isConfigured ? (
              <div style={{
                minHeight: '100vh',
                backgroundColor: '#f7f8fa',
                padding: '20px'
              }}>
                {/* Header simplificado */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  alignItems: 'center',
                  marginBottom: '20px',
                  padding: '15px 0'
                }}>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button 
                      onClick={handleSyncData}
                      disabled={syncLoading}
                      style={{
                        backgroundColor: syncLoading ? '#6c757d' : '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '8px 16px',
                        cursor: syncLoading ? 'not-allowed' : 'pointer',
                        opacity: syncLoading ? 0.7 : 1
                      }}
                    >
                      {syncLoading ? 'Sincronizando...' : 'Sincronizar'}
                    </button>
                    <button 
                      onClick={() => setIsSettingsOpen(true)}
                      style={{
                        backgroundColor: '#0366d6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '8px 16px',
                        cursor: 'pointer'
                      }}
                    >
                      Configuración
                    </button>
                  </div>
                </div>

                {/* Contenido principal */}
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '8px',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  {/* Estado de sincronización */}
                  {syncLoading && (
                    <div style={{ 
                      backgroundColor: '#e7f3ff', 
                      color: '#0366d6', 
                      padding: '15px', 
                      borderRadius: '6px',
                      marginBottom: '20px',
                      border: '1px solid #0366d6'
                    }}>
                      <p style={{ margin: 0 }}>
                        <strong>Sincronizando datos...</strong> Procesando archivos desde Google Drive
                      </p>
                    </div>
                  )}

                  {syncStatus?.success && (
                    <div style={{ 
                      backgroundColor: '#d4edda', 
                      color: '#155724', 
                      padding: '15px', 
                      borderRadius: '6px',
                      marginBottom: '20px',
                      border: '1px solid #c3e6cb'
                    }}>
                      <p style={{ margin: 0 }}>
                        <strong>Sincronización completada exitosamente</strong>
                      </p>
                      <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                        {syncStatus.cvs} CVs procesados | {syncStatus.syllabi} sílabos procesados
                      </p>
                    </div>
                  )}

                  {syncStatus?.success === false && (
                    <div style={{ 
                      backgroundColor: '#f8d7da', 
                      color: '#721c24', 
                      padding: '15px', 
                      borderRadius: '6px',
                      marginBottom: '20px',
                      border: '1px solid #f1aeb5'
                    }}>
                      <p style={{ margin: 0 }}>
                        <strong>Error en la sincronización</strong>
                      </p>
                      <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                        Verifica la configuración de Google Drive y vuelve a intentarlo.
                      </p>
                    </div>
                  )}

                  {!selectedCycle ? (
                    // Vista de ciclos
                    <>
                      <h2 style={{ marginTop: 0, color: '#24292e' }}>Ciclos Académicos</h2>
                      
                      {loading && (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#586069' }}>
                          <p>Cargando ciclos desde Google Drive...</p>
                        </div>
                      )}
                      
                      {error && (
                        <div style={{ 
                          backgroundColor: '#ffeaea', 
                          color: '#d73a49', 
                          padding: '15px', 
                          borderRadius: '6px',
                          marginTop: '20px'
                        }}>
                          <p style={{ margin: 0 }}>{error}</p>
                          <button 
                            onClick={loadCycles}
                            style={{
                              marginTop: '10px',
                              backgroundColor: '#d73a49',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '6px 12px',
                              cursor: 'pointer'
                            }}
                          >
                            Reintentar
                          </button>
                        </div>
                      )}
                      
                      {!loading && !error && cycles.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#586069' }}>
                          <p>No se encontraron ciclos en la carpeta configurada.</p>
                          <p style={{ fontSize: '14px' }}>Verifica que la carpeta contenga subcarpetas con nombres que incluyan "Ciclo".</p>
                        </div>
                      )}
                      
                      {!loading && !error && cycles.length > 0 && (
                        <div style={{ display: 'grid', gap: '15px', marginTop: '20px' }}>
                          {cycles.map(cycle => (
                            <div 
                              key={cycle.originalName} 
                              onClick={() => handleCycleClick(cycle)}
                              style={{
                                padding: '20px',
                                border: '1px solid #e1e4e8',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                backgroundColor: '#fff'
                              }}
                              onMouseEnter={(e) => e.target.style.backgroundColor = '#f6f8fa'}
                              onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                            >
                              <h3 style={{ margin: '0 0 8px 0', color: '#0366d6' }}>
                                {cycle.displayName}
                              </h3>
                              <p style={{ margin: 0, color: '#586069', fontSize: '14px' }}>
                                {cycle.courses.length} curso{cycle.courses.length !== 1 ? 's' : ''} disponible{cycle.courses.length !== 1 ? 's' : ''}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : !selectedCourse ? (
                    // Vista de cursos del ciclo seleccionado
                    <>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: '20px',
                        gap: '15px'
                      }}>
                        <button 
                          onClick={handleBackToCycles}
                          style={{
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '8px 16px',
                            cursor: 'pointer'
                          }}
                        >
                          Volver
                        </button>
                        <h2 style={{ margin: 0, color: '#24292e' }}>
                          {selectedCycle.displayName}
                        </h2>
                      </div>

                      {selectedCycle.courses.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#586069' }}>
                          <p>No se encontraron cursos en este ciclo.</p>
                        </div>
                      ) : (
                        <div style={{ display: 'grid', gap: '12px' }}>
                          {selectedCycle.courses.map(course => (
                            <div 
                              key={course} 
                              onClick={() => handleCourseClick(course)}
                              style={{
                                padding: '15px 20px',
                                border: '1px solid #e1e4e8',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                backgroundColor: '#fff'
                              }}
                              onMouseEnter={(e) => e.target.style.backgroundColor = '#f6f8fa'}
                              onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                            >
                              <h4 style={{ margin: '0', color: '#0366d6' }}>
                                {course}
                              </h4>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    // Vista de ranking para el curso seleccionado
                    <>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: '20px',
                        gap: '15px'
                      }}>
                        <button 
                          onClick={handleBackToCourses}
                          style={{
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '8px 16px',
                            cursor: 'pointer'
                          }}
                        >
                          Volver
                        </button>
                        <div>
                          <h2 style={{ margin: 0, color: '#24292e' }}>
                            {selectedCourse}
                          </h2>
                          <p style={{ margin: '4px 0 0 0', color: '#586069', fontSize: '14px' }}>
                            {selectedCycle.displayName}
                          </p>
                        </div>
                      </div>

                      {loadingRankings && (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#586069' }}>
                          <p>Generando ranking de docentes...</p>
                          <p style={{ fontSize: '14px' }}>Esto puede tomar unos segundos...</p>
                        </div>
                      )}

                      {error && (
                        <div style={{ 
                          backgroundColor: '#ffeaea', 
                          color: '#d73a49', 
                          padding: '15px', 
                          borderRadius: '6px',
                          marginTop: '20px'
                        }}>
                          <p style={{ margin: 0 }}>❌ {error}</p>
                          <button 
                            onClick={() => loadCourseRankings(selectedCourse)}
                            style={{
                              marginTop: '10px',
                              backgroundColor: '#d73a49',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '6px 12px',
                              cursor: 'pointer'
                            }}
                          >
                            Reintentar
                          </button>
                        </div>
                      )}

                      {!loadingRankings && !error && rankings.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#586069' }}>
                          <p>No se encontraron recomendaciones para este curso.</p>
                          <p style={{ fontSize: '14px' }}>
                            Es posible que necesites sincronizar los datos primero.
                          </p>
                          <button 
                            onClick={handleSyncData}
                            disabled={syncLoading}
                            style={{
                              marginTop: '15px',
                              backgroundColor: syncLoading ? '#6c757d' : '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              padding: '10px 20px',
                              cursor: syncLoading ? 'not-allowed' : 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            {syncLoading ? 'Sincronizando...' : 'Sincronizar Datos'}
                          </button>
                        </div>
                      )}

                      {!loadingRankings && !error && rankings.length > 0 && (
                        <div style={{ display: 'grid', gap: '12px' }}>
                          <h3 style={{ color: '#24292e', marginBottom: '15px' }}>
                            Docentes Recomendados
                          </h3>
                          {rankings.map((recommendation, index) => {
                            console.log(`Renderizando recommendation ${index}:`, recommendation);
                            return (
                            <div 
                              key={index}
                              style={{
                                padding: '20px',
                                border: '1px solid #e1e4e8',
                                borderRadius: '8px',
                                backgroundColor: index === 0 ? '#f0f8f0' : '#fff',
                                borderLeft: index === 0 ? '4px solid #28a745' : index === 1 ? '4px solid #ffc107' : index === 2 ? '4px solid #fd7e14' : '4px solid #dee2e6'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <h4 style={{ margin: 0, color: '#24292e' }}>
                                  {String(recommendation.teacher_name || 'Docente')}
                                </h4>
                                <span style={{ 
                                  fontSize: '18px', 
                                  fontWeight: 'bold',
                                  color: index === 0 ? '#28a745' : index === 1 ? '#ffc107' : index === 2 ? '#fd7e14' : '#6c757d'
                                }}>
                                  {typeof recommendation.score === 'number' ? recommendation.score.toFixed(1) : String(recommendation.score || 'N/A')}%
                                </span>
                              </div>
                              
                              {recommendation.explanation && (
                                <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: '#586069' }}>
                                  {String(recommendation.explanation)}
                                </p>
                              )}
                            </div>
                            );
                          })}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ) : (
              <EmptyState onConfigure={() => setIsSettingsOpen(true)} />
            )}
          </main>
        </div>
      </Router>
    </AppContext.Provider>
  );
}

export default App;
