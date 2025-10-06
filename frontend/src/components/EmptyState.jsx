import React from 'react';
import { FileText, Settings, ArrowRight } from 'react-bootstrap-icons';

function EmptyState({ onConfigure }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <FileText size={80} />
      </div>
      <h2>Sistema de Emparejamiento Docente-Curso [ACTUALIZADO]</h2>
      <p>Bienvenido al sistema inteligente de recomendaciones.</p>
      <p>Para comenzar, configura las fuentes de datos de Google Drive.</p>
      
      <div className="setup-steps">
        <div className="step">
          <Settings size={24} />
          <span>Configurar carpetas de Drive</span>
        </div>
        <ArrowRight size={20} className="step-arrow" />
        <div className="step">
          <span>📁</span>
          <span>Explorar ciclos y cursos</span>
        </div>
        <ArrowRight size={20} className="step-arrow" />
        <div className="step">
          <span>🎯</span>
          <span>Ver recomendaciones</span>
        </div>
      </div>
      
      <button className="configure-btn" onClick={onConfigure}>
        <Settings size={20} />
        Configurar ahora
      </button>
    </div>
  );
}

export default EmptyState;
