export interface Case {
  id: string;
  name: string;
  document_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
