/**
 * Learning Page - Real API Integration
 * Displays learning activities from real backend API
 */

import React, { useState } from 'react';
import { toast } from 'sonner';
import { BookOpen, ArrowRight, Check, Clock } from 'lucide-react';
import { useLearningActivities } from '../hooks/useLearningActivities';

// Import UI components from Home.tsx context
const Eyebrow = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">{children}</div>
);

const PageHead = ({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) => (
  <div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end">
    <div>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h1 className="font-display text-[36px] leading-[1.1] tracking-[-.04em] text-navy md:text-[44px]">{title}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{subtitle}</p>
    </div>
    {action}
  </div>
);

const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <section
    className={`rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-[0_7px_24px_rgba(18,48,87,.04)] md:p-7 ${className}`}
  >
    {children}
  </section>
);

const Pill = ({ children, tone = 'teal' }: { children: React.ReactNode; tone?: string }) => (
  <span
    className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${
      tone === 'orange'
        ? 'bg-[#fff0e6] text-[#d96b27]'
        : tone === 'violet'
          ? 'bg-[#f0edfc] text-violet'
          : tone === 'navy'
            ? 'bg-[#eaf0f8] text-navy'
            : 'bg-[#e8f6f3] text-teal'
    }`}
  >
    {children}
  </span>
);

const ProgressBar = ({ value, color = 'bg-teal' }: { value: number; color?: string }) => (
  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
    <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${value}%` }} />
  </div>
);

const Action = ({
  children,
  onClick,
  secondary = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  secondary?: boolean;
}) => (
  <button
    onClick={onClick}
    className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-xs font-bold transition duration-200 active:scale-[.98] ${
      secondary
        ? 'border border-slate-200 bg-white text-navy hover:bg-slate-50'
        : 'bg-orange text-white shadow-[0_8px_18px_rgba(239,126,55,.2)] hover:-translate-y-0.5 hover:bg-[#f38b4e]'
    }`}
  >
    {children}
  </button>
);

interface LearningPageProps {
  go?: (page: string) => void;
}

export function LearningPage({ go = () => {} }: LearningPageProps) {
  const { activities, currentActivity, loading, updateProgress, completeActivity } =
    useLearningActivities(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [completionScore, setCompletionScore] = useState<number | undefined>(undefined);

  // Get current activity
  const active = currentActivity || activities.find((a) => a.status === 'in_progress') || activities[0];

  const remainingTime = active
    ? Math.max(0, active.progress_percent < 100 ? 120 - Math.floor((active.progress_percent / 100) * 120) : 0)
    : 0;

  const handleProgress = async (percent: number) => {
    if (!active) return;
    await updateProgress(active.activity_id, percent, Math.floor((percent / 100) * 120));
  };

  const handleComplete = async () => {
    if (!active) return;
    const result = await completeActivity(active.activity_id, completionScore, 'Learning module completed');
    if (result) {
      setShowCompleteModal(false);
      setCompletionScore(undefined);
      toast(
        'Learning activity completed! Supporting evidence recorded. Next: Take an assessment to update competency.'
      );
    }
  };

  if (loading && !active) {
    return (
      <>
        <PageHead eyebrow="Focused learning" title="Learning" subtitle="Loading your learning activity..." />
        <Card className="p-8 text-center">
          <div className="text-slate-500">Loading...</div>
        </Card>
      </>
    );
  }

  if (!active) {
    return (
      <>
        <PageHead
          eyebrow="Focused learning"
          title="Learning"
          subtitle="No active learning activities. Start one from Recommendations."
        />
        <Card className="text-center p-8">
          <div className="text-slate-500 mb-4">You don't have an active learning activity yet.</div>
          <Action onClick={() => go('Recommendations')}>
            Browse recommendations <ArrowRight size={14} />
          </Action>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHead
        eyebrow="Focused learning"
        title="Learning"
        subtitle="A distraction-free path to improve the competency that matters next."
        action={<Pill tone="navy">{active.resource_id}</Pill>}
      />
      <div className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]">
        <Card>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <Eyebrow>Current resource</Eyebrow>
              <h2 className="text-2xl font-bold text-navy">{active.resource_id}</h2>
              <p className="mt-2 text-xs text-slate-500">Competency: {active.competency_id}</p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#e7f6f3] text-teal">
              <BookOpen size={24} />
            </div>
          </div>
          <ProgressBar value={active.progress_percent} />
          <div className="mt-2 flex justify-between text-xs font-bold text-slate-400">
            <span>{active.progress_percent}% complete</span>
            <span>{remainingTime}m remaining</span>
          </div>
          <div className="mt-8 flex border-b border-slate-100">
            {['Overview', 'Learning material', 'Practice', 'Assessment'].map((x, i) => (
              <button
                key={x}
                onClick={() => setSelectedTab(i)}
                className={`border-b-2 px-4 py-3 text-xs font-bold ${
                  selectedTab === i ? 'border-teal text-teal' : 'border-transparent text-slate-400'
                }`}
              >
                {x}
              </button>
            ))}
          </div>
          <div className="mt-7 rounded-xl bg-[#f7fafc] p-5">
            <Eyebrow>Learning objective</Eyebrow>
            <p className="text-sm leading-6 text-navy">
              Master {active.competency_id} competency through structured learning and practice.
            </p>
          </div>
          <div className="mt-6 space-y-3">
            {active.status === 'in_progress' && (
              <div className="flex gap-2">
                <Action onClick={() => handleProgress(Math.min(100, active.progress_percent + 10))}>
                  Update progress <ArrowRight size={14} />
                </Action>
                <button
                  onClick={() => setShowCompleteModal(true)}
                  className="flex items-center gap-2 rounded-xl border border-teal bg-white px-4 py-3 text-xs font-bold text-teal transition hover:bg-teal/5"
                >
                  Mark complete
                </button>
              </div>
            )}
            {active.status === 'completed' && (
              <div className="flex items-center gap-2 rounded-xl bg-teal/10 px-4 py-3 text-xs font-bold text-teal">
                <Check size={16} />
                Learning completed
              </div>
            )}
            <button onClick={() => go('Quiz Studio')} className="w-full text-xs font-bold text-teal">
              Generate practice quiz
            </button>
          </div>
        </Card>

        <Card>
          <Eyebrow>Capability status</Eyebrow>
          <div className="mt-4 space-y-5">
            <div>
              <div className="mb-2 flex justify-between text-xs font-bold">
                <span className="text-slate-500">Current level</span>
                <span className="text-navy">2.5</span>
              </div>
              <ProgressBar value={50} color="bg-orange" />
            </div>
            <div>
              <div className="mb-2 flex justify-between text-xs font-bold">
                <span className="text-slate-500">Target level</span>
                <span className="text-navy">4.0</span>
              </div>
              <ProgressBar value={80} color="bg-teal" />
            </div>
          </div>
          <div className="mt-8 border-t border-slate-100 pt-6 rounded-xl bg-[#f4fbf9] p-4 text-xs leading-5 text-teal">
            <b>Supporting evidence</b>
            <br />
            Learning completion records evidence (confidence 0.3). Assessment evidence is needed to update competency.
          </div>
        </Card>
      </div>

      {showCompleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy/30 p-4">
          <Card className="max-w-sm">
            <Eyebrow>Complete learning activity</Eyebrow>
            <h2 className="text-xl font-bold text-navy">Mark as complete</h2>
            <p className="mt-2 text-sm text-slate-500">
              Learning evidence will be recorded. Next step: take an assessment to demonstrate competency.
            </p>
            <div className="mt-6">
              <label className="text-xs font-bold text-navy">
                Final learning score (optional)
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={completionScore ?? ''}
                  onChange={(e) => setCompletionScore(e.target.value ? parseInt(e.target.value) : undefined)}
                  className="form-input mt-1"
                  placeholder="0-100"
                />
              </label>
            </div>
            <div className="mt-6 flex gap-2">
              <button
                onClick={() => setShowCompleteModal(false)}
                className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-xs font-bold text-navy transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <Action onClick={handleComplete}>Complete</Action>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}

export default LearningPage;
