import { useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { api } from '../api';
import type { GraphData } from '../types';

interface Props {
    caseId: string;
}

export default function GraphView({ caseId }: Props) {
    const [graphData, setGraphData] = useState<GraphData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadGraph();
    }, [caseId]);

    const loadGraph = async () => {
        setLoading(true);
        try {
            const data = await api.getGraphData(caseId);
            setGraphData(data);
        } catch (error) {
            console.error('Failed to load graph:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading">Loading graph...</div>;
    if (!graphData || graphData.nodes.length === 0) {
        return <div className="empty">No graph data yet. Upload documents first.</div>;
    }

    const formattedData = {
        nodes: graphData.nodes.map(n => ({ ...n, id: n.id })),
        links: graphData.edges.map(e => ({
            source: e.source,
            target: e.target,
            label: e.label
        }))
    };

    return (
        <div className="graph-view">
            <ForceGraph2D
                graphData={formattedData}
                nodeLabel="label"
                nodeAutoColorBy="type"
                linkLabel="label"
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                width={800}
                height={600}
            />
        </div>
    );
}
