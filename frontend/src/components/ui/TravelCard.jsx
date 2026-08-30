import React from 'react';

export default function TravelCard({ children, className = '', hover = true, onClick, padding = 'p-6' }) {
  return (
    <div
      onClick={onClick}
      className={`travel-card ${hover ? 'travel-card-hover cursor-pointer' : ''} ${padding} ${className}`}
    >
      {children}
    </div>
  );
}
