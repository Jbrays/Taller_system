import React from 'react';

function EmptyState({ onConfigure }) {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#667eea',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: '40px 20px'
    }}>
      <div>
        <h2 style={{ fontSize: '2.5em', marginBottom: '16px', fontWeight: '300' }}>
          Sistema de Emparejamiento Docente-Curso
        </h2>
        <p style={{ fontSize: '1.2em', marginBottom: '8px', opacity: '0.9' }}>
          Bienvenido al sistema inteligente de recomendaciones.
        </p>
        <p style={{ fontSize: '1.2em', marginBottom: '8px', opacity: '0.9' }}>
          Para comenzar, usa el botón de configuración en la esquina superior derecha.
        </p>
      </div>
    </div>
  );
}

export default EmptyState;
