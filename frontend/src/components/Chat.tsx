import { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import type { ChatMessage } from '../types';

interface Props {
    caseId: string;
}

export default function Chat({ caseId }: Props) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const websocket = api.createChatWebSocket(caseId);

        websocket.onopen = () => console.log('WebSocket connected');

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'chunk') {
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last && last.role === 'assistant') {
                        return [...prev.slice(0, -1), { ...last, content: last.content + data.content }];
                    }
                    return [...prev, { role: 'assistant', content: data.content }];
                });
            } else if (data.type === 'done') {
                setIsStreaming(false);
            }
        };

        setWs(websocket);

        return () => websocket.close();
    }, [caseId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        if (!input.trim() || !ws || isStreaming) return;

        setMessages(prev => [...prev, { role: 'user', content: input }]);
        ws.send(input);
        setInput('');
        setIsStreaming(true);
    };

    return (
        <div className="chat">
            <div className="messages">
                {messages.length === 0 && (
                    <div className="empty">Ask questions about your documents...</div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                        <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
                        <p>{msg.content}</p>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask about your documents..."
                    disabled={isStreaming}
                />
                <button onClick={handleSend} disabled={isStreaming || !input.trim()}>
                    Send
                </button>
            </div>
        </div>
    );
}
