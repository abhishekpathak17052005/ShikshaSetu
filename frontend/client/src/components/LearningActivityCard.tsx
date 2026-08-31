/**
 * LearningActivityCard Component
 * Displays a learning activity with progress, status, and action buttons
 */

import React from 'react';
import { BookOpen, Play, CheckCircle2, Clock, ArrowRight } from 'lucide-react';
import { LearningActivity } from '../lib/api';

interface LearningActivityCardProps {
  activity: LearningActivity;
  onContinue?: (activity: LearningActivity) => void;
  onComplete?: (activity: LearningActivity) => void;
  onViewDetails?: (activity: LearningActivity) => void;
}

/**
 * Card component for displaying a single learning activity
 */
export function LearningActivityCard({
  activity,
  onContinue,
  onComplete,
  onViewDetails,
}: LearningActivityCardProps) {
  const isInProgress = activity.status === 'in_progress';
  const isCompleted = activity.status === 'completed';
  const notStarted = activity.status === 'not_started';

  // Format dates
  const lastAccessedDate = activity.last_accessed_at ? new Date(activity.last_accessed_at) : null;
  const completedDate = activity.completed_at ? new Date(activity.completed_at) : null;
  const startedDate = activity.started_at ? new Date(activity.started_at) : null;

  const getStatusColor = () => {
    if (isCompleted) return 'bg-teal/10 border-teal/30';
    if (isInProgress) return 'bg-orange/10 border-orange/30';
    return 'bg-slate-50 border-slate-100';
  };

  const getStatusText = () => {
    if (isCompleted) return 'Completed';
    if (isInProgress) return 'In Progress';
    return 'Not Started';
  };

  const getStatusTextColor = () => {
    if (isCompleted) return 'text-teal';
    if (isInProgress) return 'text-orange';
    return 'text-slate-500';
  };

  const getProgressBarColor = () => {
    if (isCompleted) return 'bg-teal';
    if (isInProgress) return 'bg-orange';
    return 'bg-slate-200';
  };

  return (
    <div
      className={`rounded-xl border p-5 transition ${getStatusColor()} ${
        onViewDetails ? 'cursor-pointer hover:-translate-y-0.5 hover:shadow-sm' : ''
      }`}
      onClick={() => onViewDetails?.(activity)}
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/50">
            <BookOpen size={18} className="text-teal" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-[.1em] text-slate-400">
              {activity.resource_id}
            </div>
            <div className="text-sm font-bold text-navy">
              {activity.competency_id} Competency
            </div>
          </div>
        </div>
        <div className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${getStatusTextColor()}`}>
          {getStatusText()}
        </div>
      </div>

      {/* Progress Bar */}
      {isInProgress || isCompleted ? (
        <div className="mb-4">
          <div className="mb-2 flex justify-between text-xs font-bold">
            <span className="text-slate-500">Progress</span>
            <span className="text-navy">{activity.progress_percent}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor()}`}
              style={{ width: `${activity.progress_percent}%` }}
            />
          </div>
        </div>
      ) : null}

      {/* Activity Details */}
      <div className="mb-4 grid gap-2 sm:grid-cols-2">
        {activity.duration_minutes > 0 && (
          <div className="flex items-center gap-2 text-xs">
            <Clock size={14} className="text-slate-400" />
            <span className="text-slate-600">{activity.duration_minutes} minutes</span>
          </div>
        )}
        {isCompleted && completedDate && (
          <div className="text-xs text-slate-500">
            Completed {completedDate.toLocaleDateString()}
          </div>
        )}
        {isInProgress && lastAccessedDate && (
          <div className="text-xs text-slate-500">
            Last accessed {lastAccessedDate.toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Notes */}
      {activity.notes && (
        <div className="mb-4 rounded-lg bg-white/30 px-3 py-2 text-xs text-slate-600">
          {activity.notes}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        {!isCompleted && (
          <>
            {isInProgress && onContinue && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onContinue(activity);
                }}
                className="flex flex-1 items-center justify-center gap-1 rounded-lg bg-orange px-3 py-2 text-xs font-bold text-white transition hover:-translate-y-0.5"
              >
                <Play size={13} />
                Continue
              </button>
            )}
            {notStarted && onContinue && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onContinue(activity);
                }}
                className="flex flex-1 items-center justify-center gap-1 rounded-lg bg-teal px-3 py-2 text-xs font-bold text-white transition hover:-translate-y-0.5"
              >
                <Play size={13} />
                Start Learning
              </button>
            )}
            {isInProgress && onComplete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onComplete(activity);
                }}
                className="flex flex-1 items-center justify-center gap-1 rounded-lg border border-teal bg-white px-3 py-2 text-xs font-bold text-teal transition hover:bg-teal/5"
              >
                <CheckCircle2 size={13} />
                Mark Complete
              </button>
            )}
          </>
        )}
        {isCompleted && (
          <div className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-teal/10 px-3 py-2 text-xs font-bold text-teal">
            <CheckCircle2 size={14} />
            <span>Supporting evidence recorded</span>
          </div>
        )}
      </div>

      {/* Supporting Evidence Note */}
      {isCompleted && (
        <div className="mt-3 border-t border-slate-200 pt-3">
          <div className="text-[11px] leading-4 text-slate-600">
            <strong className="text-teal">Learning evidence (confidence 0.3)</strong>
            <br />
            Complete an assessment to update your competency level.
          </div>
        </div>
      )}
    </div>
  );
}

export default LearningActivityCard;
