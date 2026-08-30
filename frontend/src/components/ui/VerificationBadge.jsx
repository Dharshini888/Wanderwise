import React from 'react';
import StatusBadge from './StatusBadge';

export default function VerificationBadge({ status = 'Provider Verified', size = 'sm' }) {
  return <StatusBadge status={status} size={size} />;
}
