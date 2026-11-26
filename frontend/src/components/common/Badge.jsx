import React from 'react';
import { getStatusBadgeClass } from '../../utils/formatters';

export default function Badge({ children, status, className = '' }) {
  const badgeStyle = status ? getStatusBadgeClass(status) : 'bg-slate-100 text-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize tracking-wide ${badgeStyle} ${className}`}
    >
      {children || status}
    </span>
  );
}
