import React, { useState, useRef, useEffect } from 'react';

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Mock messages - replace with real-time WebSocket
    const mockMessages: Message[] = [
      {
        id: '1',
        author: {
          name: 'Sarah Johnson',
          avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=32&h=32&fit=crop&crop=face',
          role: 'PM'
        },
        content: 'Hey team, can we get an update on the authentication feature?',
        timestamp: new Date(Date.now() - 300000),
        essenceImpact: {
          type: 'neutral',
          reason: 'Standard project check-in'
        }
      },
      {
        id: '2',
        author: {
          name: 'Alex Chen',
          avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
          role: 'Developer'
        },
        content: 'Sure! Just finished the OAuth integration. PR is ready for review: #45',
        timestamp: new Date(Date.now() - 240000),
        essenceImpact: {
          type: 'positive',
          reason: 'Timely response with actionable update'
        }
      },
      {
        id: '3',
        author: {
          name: 'Sarah Johnson',
          avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=32&h=32&fit=crop&crop=face',
          role: 'PM'
        },
        content: 'Great! Can you also check on the user profile component? And the settings page? Also need status on the dashboard updates.',
        timestamp: new Date(Date.now() - 180000),
        essenceImpact: {
          type: 'negative',
          reason: 'Multiple requests in rapid succession (micromanagement detected)'
        }
      }
    ];
    setMessages(mockMessages);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const message: Message = {
      id: Date.now().toString(),
      author: {
        name: 'You',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
        role: 'Developer'
      },
      content: newMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');
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