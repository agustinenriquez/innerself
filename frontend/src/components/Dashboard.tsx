import React, { useState, useEffect } from 'react';

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
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

  useEffect(() => {
    // Mock data - replace with API call
    const mockTeam: TeamMember[] = [
      {
        id: '1',
        name: 'Alex Chen',
        role: 'developer',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
        essence: {
          overall: 85,
          prQuality: 92,
          communicationScore: 78,
          commitActivity: 81,
          teamCollaboration: 89
        },
        isOnline: true
      },
      {
        id: '2',
        name: 'Sarah Johnson',
        role: 'pm',
        avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=32&h=32&fit=crop&crop=face',
        essence: {
          overall: 72,
          prQuality: 65,
          communicationScore: 89,
          commitActivity: 52,
          teamCollaboration: 81
        },
        isOnline: true
      }
    ];
    setTeamMembers(mockTeam);
  }, []);

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {teamMembers.map((member) => (
          <div key={member.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center space-x-4 mb-4">
              <div className="relative">
                <img
                  src={member.avatar}
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

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Overall Essence</span>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${getEssenceBadge(member.essence.overall)}`}></div>
                  <span className={`font-bold ${getEssenceColor(member.essence.overall)}`}>
                    {Math.round(member.essence.overall)}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">PR Quality</span>
                  <span className={getEssenceColor(member.essence.prQuality)}>
                    {Math.round(member.essence.prQuality)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Communication</span>
                  <span className={getEssenceColor(member.essence.communicationScore)}>
                    {Math.round(member.essence.communicationScore)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Commit Activity</span>
                  <span className={getEssenceColor(member.essence.commitActivity)}>
                    {Math.round(member.essence.commitActivity)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Team Collaboration</span>
                  <span className={getEssenceColor(member.essence.teamCollaboration)}>
                    {Math.round(member.essence.teamCollaboration)}
                  </span>
                </div>
              </div>
            </div>

            <button className="w-full mt-4 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors">
              View Profile
            </button>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Team Activity</h2>
        <div className="space-y-4">
          <div className="flex items-center space-x-3 text-sm">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-gray-600">Alex Chen merged PR #45 - "Add user authentication"</span>
            <span className="text-gray-400">2 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3 text-sm">
            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            <span className="text-gray-600">Sarah Johnson created new discussion in #general</span>
            <span className="text-gray-400">15 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3 text-sm">
            <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
            <span className="text-gray-600">Code review requested for PR #46</span>
            <span className="text-gray-400">1 hour ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;