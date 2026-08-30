import React from 'react';
import { IconLoader2 } from '@tabler/icons-react';

export default function PrimaryButton({
  children,
  onClick,
  disabled,
  loading,
  icon: Icon,
  type = 'button',
  className = '',
  size = 'md'
}) {
  const sizeClasses = size === 'sm' 
    ? 'px-3.5 py-2 text-xs' 
    : size === 'lg' 
    ? 'px-6 py-3.5 text-base' 
    : 'px-5 py-2.5 text-sm';

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`btn-primary flex items-center justify-center gap-2 font-bold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all ${sizeClasses} ${className}`}
    >
      {loading ? (
        <IconLoader2 size={18} className="animate-spin" />
      ) : Icon ? (
        <Icon size={18} className="shrink-0" />
      ) : null}
      <span>{children}</span>
    </button>
  );
}
