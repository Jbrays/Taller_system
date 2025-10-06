// Backup del App.jsx original
import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import SettingsModal from './components/SettingsModal';
import EmptyState from './components/EmptyState';
import MainView from './components/MainView';
import { Gear } from 'react-bootstrap-icons';

// Creamos un contexto para compartir la configuración
export const AppContext = React.createContext();

function App() {
  const [config, setConfig] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);

  // Al cargar, intentar leer la configuración desde localStorage
  useEffect(() => {
    const savedConfig = localStorage.getItem('driveConfig');
    if (savedConfig) {
      const parsedConfig = JSON.parse(savedConfig);
      setConfig(parsedConfig);
      setIsConfigured(true);
    }
  }, []);

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
  };

  return (
    <AppContext.Provider value={{ config, isConfigured }}>
      <Router>
        <div className="app-container">
          <button className="settings-btn" onClick={() => setIsSettingsOpen(true)}>
            <Gear size={24} />
          </button>

          <SettingsModal
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            onSave={handleSaveSettings}
            currentConfig={config}
          />

          <main>
            {isConfigured ? (
              <MainView />
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
