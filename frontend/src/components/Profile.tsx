import React from 'react';

const Profile: React.FC = () => {
  // Mock data - replace with API call
  const profile = {
    name: 'Alex Chen',
    role: 'Senior Developer',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=128&h=128&fit=crop&crop=face',
    joinDate: 'January 2024',
    github: 'alexchen',
    essence: {
      overall: 85,
      prQuality: 92,
      communicationScore: 78,
      commitActivity: 81,
      teamCollaboration: 89
    },
    stats: {
      totalPRs: 47,
      mergedPRs: 44,
      averageReviewTime: '2.3 hours',
      codeReviewsGiven: 89,
      messagesThisWeek: 23,
      commitStreak: 12
    },
    recentActivity: [
      {
        type: 'pr_merged',
        description: 'Merged PR #45: Add user authentication',
        impact: '+2 essence',
        timestamp: '2 hours ago'
      },
      {
        type: 'code_review',
        description: 'Reviewed PR #44: Update dashboard styling',
        impact: '+1 essence',
        timestamp: '5 hours ago'
      },
      {
        type: 'helpful_message',
        description: 'Provided technical guidance in #dev-help',
        impact: '+1 essence',
        timestamp: '1 day ago'
      }
    ]
  };

  const getEssenceColor = (score: number) => {
    if (score >= 80) return 'text-essence-high';
    if (score >= 40) return 'text-essence-medium';
    if (score >= 10) return 'text-essence-low';
    return 'text-essence-zero';
  };

  const getEssenceBg = (score: number) => {
    if (score >= 80) return 'bg-essence-high';
    if (score >= 40) return 'bg-essence-medium';
    if (score >= 10) return 'bg-essence-zero';
    return 'bg-essence-zero';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-6">
          <img
            src={profile.avatar}
            alt={profile.name}
            className="w-24 h-24 rounded-full object-cover"
          />
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{profile.name}</h1>
            <p className="text-gray-600">{profile.role}</p>
            <p className="text-sm text-gray-500">Joined {profile.joinDate}</p>
            <div className="flex items-center space-x-2 mt-2">
              <span className="text-sm text-gray-600">GitHub:</span>
              <a href={`https://github.com/${profile.github}`} className="text-primary-500 hover:text-primary-600">
                @{profile.github}
              </a>
            </div>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getEssenceColor(profile.essence.overall)}`}>
              {Math.round(profile.essence.overall)}
            </div>
            <div className="text-sm text-gray-500">Overall Essence</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reputation Breakdown */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Essence Breakdown</h2>
          <div className="space-y-4">
            {Object.entries(profile.essence).map(([key, value]) => {
              if (key === 'overall') return null;
              const label = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
              return (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-gray-700">{label}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getEssenceBg(value)}`}
                        style={{ width: `${Math.min((value / 100) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className={`font-semibold ${getEssenceColor(value)}`}>
                      {Math.round(value)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stats */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Statistics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-primary-600">{profile.stats.totalPRs}</div>
              <div className="text-sm text-gray-600">Total PRs</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Math.round((profile.stats.mergedPRs / profile.stats.totalPRs) * 100)}%
              </div>
              <div className="text-sm text-gray-600">Merge Rate</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{profile.stats.averageReviewTime}</div>
              <div className="text-sm text-gray-600">Avg Review Time</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{profile.stats.codeReviewsGiven}</div>
              <div className="text-sm text-gray-600">Reviews Given</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{profile.stats.messagesThisWeek}</div>
              <div className="text-sm text-gray-600">Messages This Week</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{profile.stats.commitStreak}</div>
              <div className="text-sm text-gray-600">Day Streak</div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {profile.recentActivity.map((activity, index) => (
            <div key={index} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                activity.type === 'pr_merged' ? 'bg-green-400' :
                activity.type === 'code_review' ? 'bg-blue-400' :
                'bg-purple-400'
              }`}></div>
              <div className="flex-1">
                <p className="text-gray-900">{activity.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{activity.timestamp}</span>
                  <span className="text-green-600">{activity.impact}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Profile;