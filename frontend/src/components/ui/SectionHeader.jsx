import React from 'react';
import { Link } from 'react-router-dom';
import { IconChevronRight } from '@tabler/icons-react';

export default function SectionHeader({ title, description, icon: Icon, actionLabel, actionTo, onAction }) {
  return (
    <div className="flex items-center justify-between gap-4 mb-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-2.5 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Icon size={20} />
          </div>
        )}
        <div>
          <h3 className="text-base font-bold text-[var(--text-primary)] font-heading">
            {title}
          </h3>
          {description && (
            <p className="text-xs text-[var(--text-muted)] font-normal">{description}</p>
          )}
        </div>
      </div>

      {actionLabel && (
        actionTo ? (
          <Link
            to={actionTo}
            className="flex items-center gap-1 text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
          >
            <span>{actionLabel}</span>
            <IconChevronRight size={14} />
          </Link>
        ) : (
          <button
            type="button"
            onClick={onAction}
            className="flex items-center gap-1 text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
          >
            <span>{actionLabel}</span>
            <IconChevronRight size={14} />
          </button>
        )
      )}
    </div>
  );
}
