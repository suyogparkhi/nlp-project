import axios from 'axios';
import type { GraphData, DocumentInfo } from './types';

const API_BASE = 'http://localhost:8000';

export const api = {
  async listDocuments(): Promise<{ documents: DocumentInfo[]; count: number }> {
    const response = await axios.get(`${API_BASE}/documents`);
    return response.data;
  },

  async uploadDocuments(files: File[]): Promise<void> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    await axios.post(`${API_BASE}/upload`, formData);
  },

  async getGraphData(): Promise<GraphData> {
    const response = await axios.get(`${API_BASE}/graph`);
    return response.data;
  },

  createChatWebSocket(): WebSocket {
    return new WebSocket(`ws://localhost:8000/ws/chat`);
  }
};
