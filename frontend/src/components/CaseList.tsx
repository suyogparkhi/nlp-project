import type { Case } from '../types';

interface Props {
    cases: Case[];
    onSelectCase: (c: Case) => void;
}

export default function CaseList({ cases, onSelectCase }: Props) {
    return (
        <div className="case-list">
            <h2>Cases</h2>
            {cases.length === 0 ? (
                <p>No cases yet. Create one to get started.</p>
            ) : (
                <div className="cases-grid">
                    {cases.map(c => (
                        <div
                            key={c.id}
                            className="case-card"
                            onClick={() => onSelectCase(c)}
                        >
                            <h3>{c.name}</h3>
                            <p>{c.document_count} documents</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
