import React from 'react';
import { CgSpinner } from 'react-icons/cg';

export default function LoadingSpinner({ size = 'md', message }) {
  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-4xl',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 gap-3 text-slate-500">
      <CgSpinner className={`animate-spin text-brand-600 ${sizeClasses[size]}`} />
      {message && <p className="text-xs font-medium text-slate-500">{message}</p>}
    </div>
  );
}
