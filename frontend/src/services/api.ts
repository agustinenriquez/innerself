import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private token: string | null = null;
  
  constructor() {
    // Get token from localStorage
    this.token = localStorage.getItem('access_token');
    
    // Set up axios interceptor
    axios.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });
    
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }
  
  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
  }
  
  // Auth endpoints
  async getGitHubAuthUrl() {
    const response = await axios.get(`${API_BASE_URL}/auth/github`);
    return response.data.auth_url;
  }
  
  async getCurrentUser() {
    const response = await axios.get(`${API_BASE_URL}/auth/me`);
    return response.data;
  }
  
  // User endpoints
  async getUsers() {
    const response = await axios.get(`${API_BASE_URL}/users/`);
    return response.data;
  }
  
  async getUser(userId: string) {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}`);
    return response.data;
  }
  
  async getUserEssenceHistory(userId: string, days: number = 30) {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/essence/history?days=${days}`);
    return response.data;
  }
  
  // Message endpoints
  async getMessages(channel: string = 'general', limit: number = 50) {
    const response = await axios.get(`${API_BASE_URL}/messages/?channel=${channel}&limit=${limit}`);
    return response.data;
  }
  
  async sendMessage(content: string, channel: string = 'general', replyTo?: string) {
    const response = await axios.post(`${API_BASE_URL}/messages/`, {
      content,
      channel,
      reply_to: replyTo
    });
    return response.data;
  }
  
  async updateMessage(messageId: string, content: string) {
    const response = await axios.put(`${API_BASE_URL}/messages/${messageId}`, {
      content
    });
    return response.data;
  }
  
  async deleteMessage(messageId: string) {
    const response = await axios.delete(`${API_BASE_URL}/messages/${messageId}`);
    return response.data;
  }
  
  // Essence endpoints
  async getEssenceLeaderboard(limit: number = 10, timeframe: string = 'week') {
    const response = await axios.get(`${API_BASE_URL}/reputation/leaderboard?limit=${limit}&timeframe=${timeframe}`);
    return response.data;
  }
  
  async getEssenceAnalytics(days: number = 30) {
    const response = await axios.get(`${API_BASE_URL}/reputation/analytics?days=${days}`);
    return response.data;
  }
  
  async getUserEssenceDetails(userId: string, days: number = 30) {
    const response = await axios.get(`${API_BASE_URL}/reputation/user/${userId}/details?days=${days}`);
    return response.data;
  }
  
  async recalculateUserEssence(userId: string) {
    const response = await axios.post(`${API_BASE_URL}/reputation/recalculate/${userId}`);
    return response.data;
  }
}

export default new ApiService();