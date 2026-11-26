import React from 'react';

export default function SkeletonLoader({ rows = 5, cols = 4 }) {
  return (
    <div className="w-full animate-pulse space-y-4">
      {/* Header mock */}
      <div className="h-10 bg-slate-200/70 rounded-lg w-full" />
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rIdx) => (
        <div key={rIdx} className="flex gap-4">
          {Array.from({ length: cols }).map((_, cIdx) => (
            <div
              key={cIdx}
              className="h-12 bg-slate-100 rounded-lg"
              style={{ width: `${100 / cols}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
