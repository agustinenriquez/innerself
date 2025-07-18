import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import websocketService from '../services/websocket.ts';
import apiService from '../services/api.ts';

interface Message {
  id: string;
  author: {
    name: string;
    avatar: string;
    role: string;
  };
  content: string;
  timestamp: Date;
  essenceImpact?: {
    type: 'positive' | 'negative' | 'neutral';
    reason: string;
  };
}

const Chat: React.FC = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMessages();
    
    // Set up WebSocket listeners
    websocketService.onMessage((message) => {
      setMessages(prev => [...prev, message]);
    });
    
    return () => {
      // Cleanup listeners if needed
    };
  }, []);
  
  const loadMessages = async () => {
    try {
      setIsLoading(true);
      const messagesData = await apiService.getMessages('general', 50);
      setMessages(messagesData);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !user) return;

    try {
      // Send via API first (for persistence and analysis)
      await apiService.sendMessage(newMessage, 'general');
      
      // Also send via WebSocket for real-time updates
      websocketService.sendMessage(newMessage, 'general');
      
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const getEssenceIcon = (impact?: Message['essenceImpact']) => {
    if (!impact) return null;
    
    switch (impact.type) {
      case 'positive':
        return <div className="w-2 h-2 bg-green-400 rounded-full" title={impact.reason} />;
      case 'negative':
        return <div className="w-2 h-2 bg-red-400 rounded-full" title={impact.reason} />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" title={impact.reason} />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white rounded-lg shadow-md">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
          <div key={message.id} className="flex space-x-3">
            <img
              src={message.author.avatar}
              alt={message.author.name}
              className="w-8 h-8 rounded-full object-cover flex-shrink-0"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-medium text-gray-900">{message.author.name}</span>
                <span className="text-xs text-gray-500">{message.author.role}</span>
                {getEssenceIcon(message.essenceImpact)}
                <span className="text-xs text-gray-500">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-gray-700 mt-1">{message.content}</p>
              {message.essenceImpact && (
                <div className={`text-xs mt-1 px-2 py-1 rounded ${
                  message.essenceImpact.type === 'positive' ? 'bg-green-50 text-green-700' :
                  message.essenceImpact.type === 'negative' ? 'bg-red-50 text-red-700' :
                  'bg-gray-50 text-gray-700'
                }`}>
                  {message.essenceImpact.reason}
                </div>
              )}
            </div>
          </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Send
          </button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          💡 Tip: Your messages are analyzed for tone and frequency to build your essence level
        </div>
      </form>
    </div>
  );
};

export default Chat;