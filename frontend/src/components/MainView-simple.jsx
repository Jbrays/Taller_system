import React from 'react';

function MainView() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#e8f5e8',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px',
      color: '#333'
    }}>
      <div>
        <h1>🎯 MainView Simple</h1>
        <p>Esta es una versión simplificada del MainView.</p>
        <p>Si ves esto, el problema no es el componente base.</p>
      </div>
    </div>
  );
}

export default MainView;
