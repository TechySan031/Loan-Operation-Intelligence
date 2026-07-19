'use client';

import React from 'react';

interface ChartCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  headerAction?: React.ReactNode;
}

export default function ChartCard({
  title,
  description,
  children,
  headerAction,
}: ChartCardProps) {
  return (
    <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 backdrop-blur-md transition-all duration-300 shadow-2xl flex flex-col h-full min-h-[350px] glass-panel">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-extrabold text-neutral-800 dark:text-neutral-200 tracking-tight">{title}</h3>
          {description && <p className="text-[11px] text-neutral-500 dark:text-neutral-450 mt-0.5">{description}</p>}
        </div>
        {headerAction && <div>{headerAction}</div>}
      </div>
      <div className="flex-1 w-full relative min-h-[220px]">
        {children}
      </div>
    </div>
  );
}
