import React from 'react';

interface EssenceMetrics {
  overall: number;
  prQuality: number;
  communicationScore: number;
  commitActivity: number;
  teamCollaboration: number;
}

interface EssenceChartProps {
  essence: EssenceMetrics;
  role: string;
  size?: 'small' | 'medium' | 'large';
}

const EssenceChart: React.FC<EssenceChartProps> = ({ essence, role, size = 'medium' }) => {
  const getEssenceColor = (score: number) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 40) return '#3b82f6'; // blue
    if (score >= 10) return '#f59e0b'; // yellow
    return '#6b7280'; // gray
  };

  const getEssenceLevel = (score: number) => {
    if (score >= 100) return 'Legendary';
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    if (score >= 20) return 'Below Average';
    return 'Poor';
  };

  const chartSize = {
    small: { width: 120, height: 120, strokeWidth: 6 },
    medium: { width: 160, height: 160, strokeWidth: 8 },
    large: { width: 200, height: 200, strokeWidth: 10 }
  }[size];

  const center = chartSize.width / 2;
  const radius = (chartSize.width - chartSize.strokeWidth) / 2 - 10;
  const circumference = 2 * Math.PI * radius;

  // Role-specific metric weights
  const roleWeights = {
    developer: { prQuality: 0.35, commitActivity: 0.30, teamCollaboration: 0.20, communicationScore: 0.15 },
    pm: { communicationScore: 0.40, teamCollaboration: 0.35, prQuality: 0.15, commitActivity: 0.10 },
    qa: { teamCollaboration: 0.30, communicationScore: 0.30, prQuality: 0.25, commitActivity: 0.15 },
    designer: { teamCollaboration: 0.35, communicationScore: 0.30, prQuality: 0.20, commitActivity: 0.15 },
    admin: { teamCollaboration: 0.30, communicationScore: 0.25, prQuality: 0.25, commitActivity: 0.20 }
  };

  const weights = roleWeights[role.toLowerCase() as keyof typeof roleWeights] || roleWeights.developer;

  // Calculate segments for the ring chart
  const segments = [
    { name: 'PR Quality', value: essence.prQuality, weight: weights.prQuality, color: '#8b5cf6' },
    { name: 'Communication', value: essence.communicationScore, weight: weights.communicationScore, color: '#06b6d4' },
    { name: 'Commit Activity', value: essence.commitActivity, weight: weights.commitActivity, color: '#84cc16' },
    { name: 'Team Collaboration', value: essence.teamCollaboration, weight: weights.teamCollaboration, color: '#f59e0b' }
  ];

  let accumulatedLength = 0;
  const segmentPaths = segments.map((segment, index) => {
    const segmentLength = (segment.weight * circumference);
    const strokeDasharray = `${segmentLength} ${circumference}`;
    const strokeDashoffset = -accumulatedLength;
    
    accumulatedLength += segmentLength;
    
    // Opacity based on value (higher value = more opaque)
    const opacity = Math.max(0.3, segment.value / 100);
    
    return (
      <circle
        key={index}
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke={segment.color}
        strokeWidth={chartSize.strokeWidth}
        strokeDasharray={strokeDasharray}
        strokeDashoffset={strokeDashoffset}
        strokeOpacity={opacity}
        className="transition-all duration-500"
        transform={`rotate(-90 ${center} ${center})`}
      />
    );
  });

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg width={chartSize.width} height={chartSize.height}>
          {/* Background circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={chartSize.strokeWidth}
          />
          
          {/* Essence segments */}
          {segmentPaths}
        </svg>
        
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div 
            className="text-2xl font-bold"
            style={{ color: getEssenceColor(essence.overall) }}
          >
            {Math.round(essence.overall)}
          </div>
          <div className="text-xs text-gray-500 text-center">
            {getEssenceLevel(essence.overall)}
          </div>
        </div>
      </div>
      
      {/* Legend */}
      {size !== 'small' && (
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: segment.color, opacity: Math.max(0.3, segment.value / 100) }}
              ></div>
              <span className="text-gray-700">{segment.name}</span>
              <span className="font-semibold" style={{ color: getEssenceColor(segment.value) }}>
                {Math.round(segment.value)}
              </span>
            </div>
          ))}
        </div>
      )}
      
      {/* Role indicator */}
      <div className="mt-2 text-xs text-gray-500 capitalize">
        {role} Profile
      </div>
    </div>
  );
};

export default EssenceChart;