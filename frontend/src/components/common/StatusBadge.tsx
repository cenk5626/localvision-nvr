import React from 'react';
import { CameraStatus, CAMERA_STATUS_LABELS } from '../../constants';

interface StatusBadgeProps {
  status: CameraStatus;
  showPulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, showPulse = true }) => {
  const config = CAMERA_STATUS_LABELS[status] || CAMERA_STATUS_LABELS[CameraStatus.OFFLINE];
  const isOnline = status === CameraStatus.ONLINE;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}>
      {showPulse && (
        <span className="relative flex h-2 w-2">
          {isOnline && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${isOnline ? 'bg-emerald-500' : 'bg-current opacity-60'}`}></span>
        </span>
      )}
      {config.text}
    </span>
  );
};
