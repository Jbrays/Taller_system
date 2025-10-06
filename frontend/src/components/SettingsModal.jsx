import React, { useState, useEffect } from 'react';
import { X, FolderFill, PeopleFill, CheckCircleFill } from 'react-bootstrap-icons';

function SettingsModal({ isOpen, onClose, onSave, currentConfig }) {
  const [cvUrl, setCvUrl] = useState('');
  const [syllabusUrl, setSyllabusUrl] = useState('');

  // Cargar configuración actual si existe
  useEffect(() => {
    if (currentConfig && isOpen) {
      // Reconstruir URLs desde los IDs si es necesario
      setCvUrl(currentConfig.cvUrl || '');
      setSyllabusUrl(currentConfig.syllabusUrl || '');
    }
  }, [currentConfig, isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (!cvUrl.trim() || !syllabusUrl.trim()) {
      alert('Por favor, completa ambas URLs.');
      return;
    }
    onSave({ cvUrl, syllabusUrl });
  };

  const isValidUrl = (url) => {
    return url && url.includes('drive.google.com/drive/folders/');
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content settings-modal">
        <div className="modal-header">
          <h2>Configuración de Fuentes de Datos</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <p className="modal-description">
          Configura las carpetas de Google Drive que contienen los documentos del sistema.
        </p>
        
        <div className="settings-sections">
          {/* Sección de Cursos */}
          <div className="settings-section">
            <div className="section-header">
              <FolderFill size={24} className="section-icon courses-icon" />
              <h3>Cursos (Sílabos)</h3>
            </div>
            <p className="section-description">
              Carpeta que contiene los sílabos organizados por ciclos
            </p>
            <div className="form-group">
              <label>URL de la carpeta de cursos</label>
              <input 
                type="text" 
                value={syllabusUrl} 
                onChange={(e) => setSyllabusUrl(e.target.value)} 
                placeholder="https://drive.google.com/drive/folders/..."
                className={syllabusUrl && !isValidUrl(syllabusUrl) ? 'invalid' : ''}
              />
              {syllabusUrl && isValidUrl(syllabusUrl) && (
                <div className="validation-success">
                  <CheckCircleFill size={16} /> URL válida
                </div>
              )}
            </div>
          </div>

          {/* Sección de Docentes */}
          <div className="settings-section">
            <div className="section-header">
              <PeopleFill size={24} className="section-icon teachers-icon" />
              <h3>Docentes (CVs)</h3>
            </div>
            <p className="section-description">
              Carpeta que contiene los CVs de los docentes
            </p>
            <div className="form-group">
              <label>URL de la carpeta de docentes</label>
              <input 
                type="text" 
                value={cvUrl} 
                onChange={(e) => setCvUrl(e.target.value)} 
                placeholder="https://drive.google.com/drive/folders/..."
                className={cvUrl && !isValidUrl(cvUrl) ? 'invalid' : ''}
              />
              {cvUrl && isValidUrl(cvUrl) && (
                <div className="validation-success">
                  <CheckCircleFill size={16} /> URL válida
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button 
            className="btn-primary" 
            onClick={handleSave}
            disabled={!isValidUrl(cvUrl) || !isValidUrl(syllabusUrl)}
          >
            Guardar y Sincronizar
          </button>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
