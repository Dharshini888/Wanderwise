import React from 'react';

export default function SecondaryButton({
  children,
  onClick,
  disabled,
  icon: Icon,
  type = 'button',
  className = '',
  size = 'md'
}) {
  const sizeClasses = size === 'sm' 
    ? 'px-3 py-1.5 text-xs' 
    : size === 'lg' 
    ? 'px-5 py-3 text-base' 
    : 'px-4 py-2 text-sm';

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn-secondary flex items-center justify-center gap-2 font-bold cursor-pointer disabled:opacity-50 transition-all ${sizeClasses} ${className}`}
    >
      {Icon && <Icon size={16} className="shrink-0 text-[var(--text-muted)]" />}
      <span>{children}</span>
    </button>
  );
}
