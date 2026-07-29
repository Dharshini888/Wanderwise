export default function AvatarBadge({ user, size = 'md', className = '' }) {
  const name = user?.name || 'Traveler';
  const avatarUrl = user?.avatar_url || user?.profile_picture;

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-lg',
    xl: 'w-20 h-20 text-2xl',
  }[size] || 'w-10 h-10 text-sm';

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name}
        className={`${sizeClasses} rounded-xl object-cover border border-[var(--border-color)] shadow-sm ${className}`}
      />
    );
  }

  return (
    <div
      className={`${sizeClasses} rounded-xl bg-gradient-to-br from-[var(--color-primary-500)] to-indigo-700 text-white font-bold flex items-center justify-center shadow-md select-none ${className}`}
    >
      {initials}
    </div>
  );
}
