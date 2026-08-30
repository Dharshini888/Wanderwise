import React from 'react';
import TravelCard from './TravelCard';
import PrimaryButton from './PrimaryButton';

export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <TravelCard padding="p-10" hover={false} className="text-center max-w-md mx-auto my-6 border-dashed">
      {Icon && (
        <div className="w-16 h-16 mx-auto mb-4 rounded-3xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
          <Icon size={32} />
        </div>
      )}
      <h4 className="text-base font-bold text-[var(--text-primary)] font-heading mb-1">{title}</h4>
      {description && <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-5">{description}</p>}
      {actionLabel && onAction && (
        <PrimaryButton onClick={onAction} size="sm" className="mx-auto">
          {actionLabel}
        </PrimaryButton>
      )}
    </TravelCard>
  );
}
