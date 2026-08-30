import React from 'react';

export default function IconButton({
  icon: Icon,
  onClick,
  title,
  variant = 'ghost',
  className = '',
  size = 'md'
}) {
  const sizeClasses = size === 'sm' ? 'p-1.5' : size === 'lg' ? 'p-3' : 'p-2';
  const iconSize = size === 'sm' ? 16 : size === 'lg' ? 22 : 18;

  let variantClass = 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]';

  if (variant === 'danger') {
    variantClass = 'text-rose-500 hover:bg-rose-500/10';
  } else if (variant === 'primary') {
    variantClass = 'text-blue-600 dark:text-blue-400 hover:bg-blue-500/10';
  } else if (variant === 'border') {
    variantClass = 'border border-[var(--border-color)] text-[var(--text-secondary)] hover:bg-[var(--bg-subtle)]';
  }

  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-label={title}
      className={`rounded-xl transition-all cursor-pointer ${sizeClasses} ${variantClass} ${className}`}
    >
      <Icon size={iconSize} />
    </button>
  );
}
