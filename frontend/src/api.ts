import axios from 'axios';
import type { Case, GraphData } from './types';

const API_BASE = 'http://localhost:8000';

export const api = {
  async createCase(name: string): Promise<Case> {
    const response = await axios.post(`${API_BASE}/cases`, { name });
    return response.data;
  },

  async listCases(): Promise<Case[]> {
    const response = await axios.get(`${API_BASE}/cases`);
    return response.data;
  },

  async uploadDocuments(caseId: string, files: File[]): Promise<void> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    await axios.post(`${API_BASE}/cases/${caseId}/upload`, formData);
  },

  async getGraphData(caseId: string): Promise<GraphData> {
    const response = await axios.get(`${API_BASE}/cases/${caseId}/graph`);
    return response.data;
  },

  createChatWebSocket(caseId: string): WebSocket {
    return new WebSocket(`ws://localhost:8000/ws/chat/${caseId}`);
  }
};
