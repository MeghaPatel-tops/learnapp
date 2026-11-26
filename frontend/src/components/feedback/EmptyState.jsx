import React from 'react';
import { HiOutlineInbox } from 'react-icons/hi2';
import Button from '../common/Button';

export default function EmptyState({
  icon: Icon = HiOutlineInbox,
  title = 'No records found',
  description = 'There is currently no data matching your criteria.',
  actionText,
  onAction,
}) {
  return (
    <div className="text-center py-12 px-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
      <div className="mx-auto w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
        <Icon className="text-2xl" />
      </div>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">{description}</p>
      {actionText && onAction && (
        <div className="mt-4">
          <Button size="sm" onClick={onAction}>
            {actionText}
          </Button>
        </div>
      )}
    </div>
  );
}
