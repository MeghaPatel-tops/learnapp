import React from 'react';
import { HiExclamationCircle } from 'react-icons/hi2';

export default function ErrorAlert({ message, onClose }) {
  if (!message) return null;

  return (
    <div className="rounded-lg bg-rose-50 border border-rose-200 p-4 mb-4 flex items-start gap-3">
      <HiExclamationCircle className="text-rose-500 text-lg shrink-0 mt-0.5" />
      <div className="flex-1 text-xs font-medium text-rose-800">{message}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-rose-400 hover:text-rose-600 text-sm font-semibold cursor-pointer"
        >
          &times;
        </button>
      )}
    </div>
  );
}
