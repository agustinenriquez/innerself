import { io, Socket } from 'socket.io-client';

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

interface EssenceUpdate {
  userId: string;
  newEssence: number;
  delta: number;
  reason: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private isConnected = false;
  
  connect(userId: string, token: string) {
    if (this.isConnected) return;
    
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    
    this.socket = io(`${wsUrl}/ws/${userId}`, {
      auth: {
        token
      }
    });
    
    this.socket.on('connect', () => {
      this.isConnected = true;
      console.log('Connected to WebSocket');
    });
    
    this.socket.on('disconnect', () => {
      this.isConnected = false;
      console.log('Disconnected from WebSocket');
    });
    
    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }
  
  sendMessage(content: string, channel: string = 'general') {
    if (this.socket && this.isConnected) {
      this.socket.emit('message', {
        content,
        channel,
        timestamp: new Date().toISOString()
      });
    }
  }
  
  onMessage(callback: (message: Message) => void) {
    if (this.socket) {
      this.socket.on('message', callback);
    }
  }
  
  onEssenceUpdate(callback: (update: EssenceUpdate) => void) {
    if (this.socket) {
      this.socket.on('essence_update', callback);
    }
  }
  
  onUserOnline(callback: (userId: string) => void) {
    if (this.socket) {
      this.socket.on('user_online', callback);
    }
  }
  
  onUserOffline(callback: (userId: string) => void) {
    if (this.socket) {
      this.socket.on('user_offline', callback);
    }
  }
  
  getConnectionStatus() {
    return this.isConnected;
  }
}

export default new WebSocketService();