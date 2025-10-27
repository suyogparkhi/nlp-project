import { useState } from 'react';
import { api } from './api';
import FileUpload from './components/FileUpload';
import GraphView from './components/GraphView';
import Chat from './components/Chat';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'graph' | 'chat'>('upload');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUpload = async (files: File[]) => {
    await api.uploadDocuments(files);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="app">
      <header>
        <h1>Legal Document Assistant</h1>
      </header>

      <div className="container">
        <div className="tabs">
          <button
            className={activeTab === 'upload' ? 'active' : ''}
            onClick={() => setActiveTab('upload')}
          >
            Upload
          </button>
          <button
            className={activeTab === 'graph' ? 'active' : ''}
            onClick={() => setActiveTab('graph')}
          >
            Knowledge Graph
          </button>
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'upload' && <FileUpload onUpload={handleUpload} />}
          {activeTab === 'graph' && <GraphView key={refreshKey} />}
          {activeTab === 'chat' && <Chat />}
        </div>
      </div>
    </div>
  );
}

export default App;
