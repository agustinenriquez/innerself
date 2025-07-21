import React, { useState, useEffect } from 'react';
import apiService from '../services/api.ts';
import LoadingSpinner from './LoadingSpinner.tsx';

interface EssenceMetrics {
  overall: number;
  pr_quality: number;
  communication_score: number;
  commit_activity: number;
  team_collaboration: number;
  last_updated: string;
}

interface User {
  id: string;
  name: string;
  email: string;
  essence: EssenceMetrics;
  avatar_url?: string;
}

interface LeaderboardEntry {
  user_id: string;
  name: string;
  essence: number;
  rank: number;
}

const Stats: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'all'>('week');

  useEffect(() => {
    fetchStatsData();
  }, [timeframe]);

  const fetchStatsData = async () => {
    try {
      setLoading(true);
      const [usersData, leaderboardData] = await Promise.all([
        apiService.getUsersPublic(),
        apiService.getEssenceLeaderboardPublic(20, timeframe)
      ]);
      
      setUsers(usersData);
      setLeaderboard(leaderboardData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch stats data');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-500 mb-2">Error loading stats</div>
          <div className="text-gray-600 text-sm">{error}</div>
          <button 
            onClick={fetchStatsData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Community Stats</h1>
        <p className="text-gray-600">View member rankings and essence distribution</p>
      </div>

      {/* Timeframe Selector */}
      <div className="mb-6">
        <div className="flex space-x-2">
          {(['week', 'month', 'all'] as const).map((period) => (
            <button
              key={period}
              onClick={() => setTimeframe(period)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeframe === period
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {period === 'all' ? 'All Time' : `This ${period.charAt(0).toUpperCase() + period.slice(1)}`}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Leaderboard */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Essence Leaderboard
            <span className="text-sm font-normal text-gray-500 ml-2">
              ({timeframe === 'all' ? 'All Time' : `This ${timeframe}`})
            </span>
          </h2>
          
          <div className="space-y-3">
            {leaderboard.length > 0 ? (
              leaderboard.map((entry, index) => (
                <div
                  key={entry.user_id}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    index < 3 ? 'bg-gradient-to-r from-yellow-50 to-orange-50' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      index === 0 ? 'bg-yellow-500 text-white' :
                      index === 1 ? 'bg-gray-400 text-white' :
                      index === 2 ? 'bg-orange-600 text-white' :
                      'bg-gray-300 text-gray-700'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{entry.name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-blue-600">{entry.essence.toLocaleString()}</div>
                    <div className="text-xs text-gray-500">essence</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                No leaderboard data available
              </div>
            )}
          </div>
        </div>

        {/* All Members */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            All Members ({users.length})
          </h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {users.length > 0 ? (
              users
                .sort((a, b) => (b.essence?.overall || 0) - (a.essence?.overall || 0))
                .map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          alt={user.name}
                          className="w-8 h-8 rounded-full"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {user.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-blue-600">
                        {Math.round(user.essence?.overall || 0).toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-500">essence</div>
                    </div>
                  </div>
                ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                No members found
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="text-2xl font-bold text-blue-600">{users.length}</div>
          <div className="text-gray-600">Total Members</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="text-2xl font-bold text-green-600">
            {Math.round(users.reduce((sum, user) => sum + (user.essence?.overall || 0), 0)).toLocaleString()}
          </div>
          <div className="text-gray-600">Total Essence</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {users.length > 0 ? Math.round(users.reduce((sum, user) => sum + (user.essence?.overall || 0), 0) / users.length).toLocaleString() : 0}
          </div>
          <div className="text-gray-600">Average Essence</div>
        </div>
      </div>
    </div>
  );
};

export default Stats;