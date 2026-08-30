import React from 'react';

export default function PageHeader({ title, description, badge, actions, children }) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div className="space-y-1">
        {badge && <div className="mb-1.5">{badge}</div>}
        <h1 className="text-2xl md:text-3xl font-black tracking-tight text-[var(--text-primary)] font-heading">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-[var(--text-muted)] max-w-2xl font-normal leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {(actions || children) && (
        <div className="flex items-center gap-3 shrink-0">
          {actions}
          {children}
        </div>
      )}
    </div>
  );
}
