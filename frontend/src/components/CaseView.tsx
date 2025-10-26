import { useState } from 'react';
import type { Case } from '../types';
import { api } from '../api';
import FileUpload from './FileUpload';
import GraphView from './GraphView';
import Chat from './Chat';

interface Props {
    case: Case;
    onBack: () => void;
    onUpdate: () => void;
}

export default function CaseView({ case: caseData, onBack, onUpdate }: Props) {
    const [activeTab, setActiveTab] = useState<'upload' | 'graph' | 'chat'>('upload');

    const handleUpload = async (files: File[]) => {
        await api.uploadDocuments(caseData.id, files);
        onUpdate();
    };

    return (
        <div className="case-view">
            <div className="case-header">
                <button onClick={onBack}>← Back</button>
                <h2>{caseData.name}</h2>
                <span>{caseData.document_count} documents</span>
            </div>

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
                {activeTab === 'graph' && <GraphView caseId={caseData.id} />}
                {activeTab === 'chat' && <Chat caseId={caseData.id} />}
            </div>
        </div>
    );
}
