import React, { useEffect, useState, useRef } from "react";

/**
 * NumberReveal
 * Smoothly interpolates numeric values on initial load or data arrival.
 * If the value is non-numeric, null, or "Not assessed", it renders immediately with fade-in.
 */
interface NumberRevealProps {
  value: number | string | null | undefined;
  duration?: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  className?: string;
  fallback?: string;
}

export function NumberReveal({
  value,
  duration = 650,
  decimals = 0,
  suffix = "",
  prefix = "",
  className = "",
  fallback = "—",
}: NumberRevealProps) {
  const [displayValue, setDisplayValue] = useState<number | null>(() => {
    const num = typeof value === "number" ? value : parseFloat(String(value));
    return isNaN(num) ? null : 0;
  });

  const prevTargetRef = useRef<number | null>(null);

  const isNumeric = typeof value === "number" || (!isNaN(parseFloat(String(value))) && isFinite(Number(value)));
  const targetNum = isNumeric ? (typeof value === "number" ? value : parseFloat(String(value))) : null;

  useEffect(() => {
    // If not numeric (e.g. "Not assessed", null, undefined)
    if (targetNum === null) {
      setDisplayValue(null);
      return;
    }

    // Check prefers-reduced-motion
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplayValue(targetNum);
      return;
    }

    const startNum = prevTargetRef.current !== null ? prevTargetRef.current : 0;
    const endNum = targetNum;
    prevTargetRef.current = endNum;

    if (startNum === endNum) {
      setDisplayValue(endNum);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const easeOutQuad = (t: number) => t * (2 - t);

    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const easedProgress = easeOutQuad(progress);
      const current = startNum + (endNum - startNum) * easedProgress;

      setDisplayValue(current);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step);
      } else {
        setDisplayValue(endNum);
      }
    };

    animationFrameId = requestAnimationFrame(step);

    return () => cancelAnimationFrame(animationFrameId);
  }, [targetNum, duration]);

  if (targetNum === null) {
    return <span className={`anim-fade-in inline-block ${className}`}>{value !== null && value !== undefined ? String(value) : fallback}</span>;
  }

  const formatted =
    displayValue !== null
      ? decimals > 0
        ? displayValue.toFixed(decimals)
        : Math.round(displayValue).toString()
      : targetNum.toFixed(decimals);

  return (
    <span className={`anim-fade-in inline-block font-mono tracking-tight ${className}`}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
}

/**
 * ProgressBarFill
 * Hardware-accelerated CSS animated progress fill.
 */
interface ProgressBarFillProps {
  percent?: number;
  percentage?: number;
  value?: number;
  className?: string;
  fillClassName?: string;
  colorClass?: string;
  heightClass?: string;
  durationMs?: number;
}

export function ProgressBarFill({
  percent,
  percentage,
  value,
  className,
  fillClassName,
  colorClass = "bg-[#0f9f92]",
  heightClass = "h-2",
  durationMs = 600,
}: ProgressBarFillProps) {
  const actualPercent = percent ?? percentage ?? value ?? 0;
  const clamped = Math.max(0, Math.min(100, actualPercent || 0));

  const wrapperClass = className ?? `${heightClass} w-full rounded-full bg-slate-100 overflow-hidden`;
  const innerClass = fillClassName ?? `h-full rounded-full ${colorClass}`;

  return (
    <div className={wrapperClass}>
      <div
        className={innerClass}
        style={{
          width: `${clamped}%`,
          transition: `width ${durationMs}ms cubic-bezier(0.16, 1, 0.3, 1)`,
        }}
      />
    </div>
  );
}

/**
 * useScrollReveal
 * Viewport IntersectionObserver hook with once: true and reduced motion support.
 */
export function useScrollReveal<T extends HTMLElement = HTMLDivElement>(
  threshold = 0.1,
  rootMargin = "0px 0px -40px 0px"
) {
  const ref = useRef<T | null>(null);
  const [isVisible, setIsVisible] = useState(() => {
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return true;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIsVisible(true);
      return;
    }

    if (!ref.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold, rootMargin }
    );

    observer.observe(ref.current);

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin]);

  return { ref, isVisible };
}

/**
 * AnimatedSection
 * Reusable container that triggers progressive reveal when scrolled into view.
 */
interface AnimatedSectionProps {
  children: React.ReactNode;
  className?: string;
  animationClass?: string;
  delayMs?: number;
}

export function AnimatedSection({
  children,
  className = "",
  animationClass = "anim-fade-up",
  delayMs = 0,
}: AnimatedSectionProps) {
  const { ref, isVisible } = useScrollReveal();

  return (
    <div
      ref={ref}
      className={`${className} ${isVisible ? animationClass : "opacity-0"}`}
      style={delayMs > 0 && isVisible ? { animationDelay: `${delayMs}ms` } : undefined}
    >
      {children}
    </div>
  );
}

/**
 * AnimatedSignalBar
 * Comparative capability visualizer showing Current Level vs Required Target Level.
 */
interface AnimatedSignalBarProps {
  currentLevel: number | null | undefined;
  requiredLevel: number;
  maxLevel?: number;
  className?: string;
  showLabels?: boolean;
}

export function AnimatedSignalBar({
  currentLevel,
  requiredLevel,
  maxLevel = 5.0,
  className = "",
  showLabels = true,
}: AnimatedSignalBarProps) {
  const { ref, isVisible } = useScrollReveal();

  const current = currentLevel != null ? Math.max(0, Math.min(maxLevel, currentLevel)) : 0;
  const required = Math.max(0, Math.min(maxLevel, requiredLevel));

  const currentPct = (current / maxLevel) * 100;
  const requiredPct = (required / maxLevel) * 100;
  const gap = Math.max(0, required - current);

  return (
    <div ref={ref} className={`signal-wrap space-y-1.5 ${className}`}>
      <div className="signal-track relative h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
        {/* Background track indicator */}
        <div className="absolute inset-0 bg-gradient-to-r from-slate-100 to-slate-200" />

        {/* Current progress fill */}
        <div
          className="signal-fill absolute left-0 top-0 h-full rounded-full bg-[#087f76]"
          style={{
            width: isVisible ? `${currentPct}%` : "0%",
            transition: "width 650ms cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        />

        {/* Required benchmark indicator marker */}
        <div
          className="signal-required absolute top-0 bottom-0 w-1 bg-[#123057] z-10"
          style={{
            left: `${requiredPct}%`,
            transition: "left 650ms cubic-bezier(0.16, 1, 0.3, 1)",
          }}
          title={`Required Benchmark: Level ${required.toFixed(1)}`}
        />
      </div>

      {showLabels && (
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 pt-0.5">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#087f76] inline-block" />
            <span>Current: <strong>{currentLevel != null ? current.toFixed(1) : "Not Assessed"}</strong></span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#123057] inline-block" />
            <span>Target: <strong>{required.toFixed(1)}</strong></span>
            {gap > 0 && (
              <span className="ml-1 rounded bg-orange-100 px-1.5 py-0.2 text-[10px] font-bold text-orange-800">
                Gap: {gap.toFixed(1)}
              </span>
            )}
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * StatusTransition
 * Animated status pill badge transitioning between operational states.
 */
interface StatusTransitionProps {
  status: string;
  variant?: "teal" | "orange" | "purple" | "emerald" | "slate" | "amber";
  className?: string;
  icon?: React.ReactNode;
}

export function StatusTransition({
  status,
  variant = "teal",
  className = "",
  icon,
}: StatusTransitionProps) {
  const variantStyles = {
    teal: "bg-teal-50 text-teal-800 border-teal-200",
    orange: "bg-orange-50 text-orange-800 border-orange-200",
    purple: "bg-purple-50 text-[#4b36a8] border-purple-200",
    emerald: "bg-emerald-50 text-emerald-800 border-emerald-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
  };

  return (
    <span
      key={status}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider border anim-badge-pop ${variantStyles[variant]} ${className}`}
    >
      {icon}
      <span>{status}</span>
    </span>
  );
}

/**
 * ThinkingIndicator
 * Dynamic 3-dot pulse for live pending AI requests.
 */
export function ThinkingIndicator({ label = "Thinking..." }: { label?: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-2xl bg-[#f8fafc] border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-600 anim-fade-in">
      <div className="flex items-center gap-1 text-[#087f76]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#087f76] thinking-dot-1" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#087f76] thinking-dot-2" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#087f76] thinking-dot-3" />
      </div>
      <span className="text-slate-500">{label}</span>
    </div>
  );
}
