import React from "react";

export function PageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse p-2">
      {/* Top Banner Skeleton */}
      <div className="h-32 w-full rounded-3xl bg-slate-200/80" />

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="h-24 rounded-2xl bg-slate-200/70" />
        <div className="h-24 rounded-2xl bg-slate-200/70" />
        <div className="h-24 rounded-2xl bg-slate-200/70" />
        <div className="h-24 rounded-2xl bg-slate-200/70" />
      </div>

      {/* Main Content Skeleton */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="h-64 rounded-3xl bg-slate-200/60 md:col-span-2" />
        <div className="h-64 rounded-3xl bg-slate-200/60" />
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm animate-pulse space-y-4">
      <div className="h-6 w-1/3 rounded bg-slate-200" />
      <div className="h-4 w-full rounded bg-slate-100" />
      <div className="h-4 w-2/3 rounded bg-slate-100" />
    </div>
  );
}
