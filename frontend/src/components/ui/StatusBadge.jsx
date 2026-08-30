import React from 'react';
import { IconCheck, IconAlertTriangle, IconX, IconRoute, IconHelp } from '@tabler/icons-react';

export default function StatusBadge({ status, label, icon: CustomIcon, size = 'sm' }) {
  let colorClass = 'badge-gray';
  let IconComponent = IconHelp;
  let text = label || status || 'Unavailable';

  const normalized = (status || label || '').toString().toUpperCase();

  if (
    normalized.includes('VERIFIED') ||
    normalized.includes('ACTIVE') ||
    normalized.includes('CONFIRMED') ||
    normalized.includes('GREEN') ||
    normalized === 'VALID'
  ) {
    colorClass = 'badge-green';
    IconComponent = IconCheck;
  } else if (
    normalized.includes('EXPIRING') ||
    normalized.includes('WARNING') ||
    normalized.includes('TIGHT') ||
    normalized.includes('ESTIMATED') ||
    normalized.includes('LIMITED') ||
    normalized.includes('AMBER')
  ) {
    colorClass = 'badge-amber';
    IconComponent = IconAlertTriangle;
  } else if (
    normalized.includes('EXPIRED') ||
    normalized.includes('FAILED') ||
    normalized.includes('IMPOSSIBLE') ||
    normalized.includes('CRITICAL') ||
    normalized.includes('RED')
  ) {
    colorClass = 'badge-red';
    IconComponent = IconX;
  } else if (
    normalized.includes('CALCULATED') ||
    normalized.includes('INFO') ||
    normalized.includes('BLUE')
  ) {
    colorClass = 'badge-blue';
    IconComponent = IconRoute;
  } else if (
    normalized.includes('UNAVAILABLE') ||
    normalized.includes('NONE') ||
    normalized.includes('GRAY')
  ) {
    colorClass = 'badge-gray';
    IconComponent = IconHelp;
  }

  const DisplayIcon = CustomIcon || IconComponent;

  const sizeClasses = size === 'xs' 
    ? 'px-2 py-0.5 text-[10px]' 
    : size === 'md' 
    ? 'px-3.5 py-1.5 text-xs' 
    : 'px-2.5 py-1 text-[11px]';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-bold rounded-full transition-all ${colorClass} ${sizeClasses}`}
    >
      <DisplayIcon size={size === 'xs' ? 12 : size === 'md' ? 16 : 14} className="shrink-0" />
      <span className="truncate">{text}</span>
    </span>
  );
}
