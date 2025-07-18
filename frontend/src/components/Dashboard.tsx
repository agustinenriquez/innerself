import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/api';
import EssenceChart from './EssenceChart';
import websocketService from '../services/websocket';

interface EssenceMetrics {
  overall: number;
  prQuality: number;
  communicationScore: number;
  commitActivity: number;
  teamCollaboration: number;
}

interface TeamMember {
  id: string;
  name: string;
  role: 'developer' | 'pm' | 'qa' | 'designer';
  avatar: string;
  essence: EssenceMetrics;
  isOnline: boolean;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    
    // Listen for real-time essence updates
    websocketService.onEssenceUpdate((update) => {
      setTeamMembers(prev => prev.map(member => 
        member.id === update.userId 
          ? { ...member, essence: { ...member.essence, overall: update.newEssence } }
          : member
      ));
    });
    
    websocketService.onUserOnline((userId) => {
      setTeamMembers(prev => prev.map(member => 
        member.id === userId ? { ...member, isOnline: true } : member
      ));
    });
    
    websocketService.onUserOffline((userId) => {
      setTeamMembers(prev => prev.map(member => 
        member.id === userId ? { ...member, isOnline: false } : member
      ));
    });
  }, []);
  
  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const [usersData, analyticsData, leaderboardData] = await Promise.all([
        apiService.getUsers(),
        apiService.getEssenceAnalytics(30),
        apiService.getEssenceLeaderboard(10, 'week')
      ]);
      
      setTeamMembers(usersData);
      setAnalytics(analyticsData);
      setLeaderboard(leaderboardData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getEssenceColor = (score: number) => {
    if (score >= 80) return 'text-essence-high';
    if (score >= 40) return 'text-essence-medium';
    if (score >= 10) return 'text-essence-low';
    return 'text-essence-zero';
  };

  const getEssenceBadge = (score: number) => {
    if (score >= 80) return 'bg-essence-high';
    if (score >= 40) return 'bg-essence-medium';
    if (score >= 10) return 'bg-essence-low';
    return 'bg-essence-zero';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Team Dashboard</h1>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            {teamMembers.filter(m => m.isOnline).length} online
          </span>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          {/* Analytics Overview */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="text-2xl font-bold text-primary-600">{analytics.top_performers?.length || 0}</div>
                <div className="text-sm text-gray-600">Active Contributors</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="text-2xl font-bold text-green-600">{teamMembers.filter(m => m.isOnline).length}</div>
                <div className="text-sm text-gray-600">Online Now</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="text-2xl font-bold text-yellow-600">{analytics.micromanagement_incidents || 0}</div>
                <div className="text-sm text-gray-600">Micromanagement Alerts</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round(teamMembers.reduce((acc, m) => acc + m.essence.overall, 0) / teamMembers.length) || 0}
                </div>
                <div className="text-sm text-gray-600">Team Avg Essence</div>
              </div>
            </div>
          )}
          
          {/* Team Members Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teamMembers.map((member) => (
              <div key={member.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="relative">
                    <img
                      src={member.avatar || member.github_profile?.avatar_url || 'https://via.placeholder.com/48'}
                      alt={member.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    {member.isOnline && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></div>
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{member.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{member.role}</p>
                  </div>
                </div>

                {/* Essence Chart */}
                <div className="flex justify-center mb-4">
                  <EssenceChart 
                    essence={member.essence} 
                    role={member.role}
                    size="small"
                  />
                </div>

                <button 
                  onClick={() => window.location.href = `/profile/${member.id}`}
                  className="w-full mt-4 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
                >
                  View Profile
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Leaderboard and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leaderboard */}
        {leaderboard && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Weekly Leaderboard</h2>
            <div className="space-y-3">
              {leaderboard.leaderboard?.slice(0, 5).map((member: any, index: number) => (
                <div key={member.user_id} className="flex items-center space-x-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    index === 0 ? 'bg-yellow-400 text-yellow-900' :
                    index === 1 ? 'bg-gray-300 text-gray-700' :
                    index === 2 ? 'bg-amber-600 text-amber-100' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {index + 1}
                  </div>
                  <img 
                    src={member.avatar_url || 'https://via.placeholder.com/32'} 
                    alt={member.name}
                    className="w-8 h-8 rounded-full"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{member.name}</div>
                    <div className="text-xs text-gray-500 capitalize">{member.role}</div>
                  </div>
                  <div className={`font-bold ${getEssenceColor(member.overall_essence)}`}>
                    {Math.round(member.overall_essence)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {analytics?.trends?.slice(-5).map((trend: any, index: number) => (
              <div key={index} className="flex items-center space-x-3 text-sm">
                <div className={`w-2 h-2 rounded-full ${
                  trend.event_type === 'pr_merged' ? 'bg-green-400' :
                  trend.event_type === 'code_review' ? 'bg-blue-400' :
                  trend.event_type === 'micromanagement_detected' ? 'bg-red-400' :
                  'bg-gray-400'
                }`}></div>
                <span className="text-gray-600">
                  {trend.count} {trend.event_type.replace('_', ' ')} events
                </span>
                <span className="text-gray-400">{trend.date}</span>
              </div>
            )) || (
              <div className="text-gray-500 text-center py-4">
                No recent activity data available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;