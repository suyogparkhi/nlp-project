import { useState, useEffect } from 'react';
import type { Case } from './types';
import { api } from './api';
import CaseList from './components/CaseList';
import CaseView from './components/CaseView';
import './App.css';

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [newCaseName, setNewCaseName] = useState('');

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    const data = await api.listCases();
    setCases(data);
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseName.trim()) return;

    await api.createCase(newCaseName);
    setNewCaseName('');
    await loadCases();
  };

  return (
    <div className="app">
      <header>
        <h1>Legal Document Assistant</h1>
      </header>

      <div className="container">
        {!selectedCase ? (
          <div className="cases-view">
            <form onSubmit={handleCreateCase} className="create-case">
              <input
                type="text"
                placeholder="New case name"
                value={newCaseName}
                onChange={(e) => setNewCaseName(e.target.value)}
              />
              <button type="submit">Create Case</button>
            </form>

            <CaseList
              cases={cases}
              onSelectCase={setSelectedCase}
            />
          </div>
        ) : (
          <CaseView
            case={selectedCase}
            onBack={() => setSelectedCase(null)}
            onUpdate={loadCases}
          />
        )}
      </div>
    </div>
  );
}

export default App;
