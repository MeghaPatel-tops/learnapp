import React from 'react';
import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col justify-center bg-gradient-to-br from-slate-50 via-brand-50/20 to-slate-100 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex w-12 h-12 rounded-2xl bg-brand-600 text-white items-center justify-center font-black text-2xl shadow-lg shadow-brand-500/30 mb-4">
          A
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Apex Learning Institute</h2>
        <p className="mt-1 text-xs font-medium text-slate-500">Center for Professional & Technical Excellence</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-xl shadow-slate-200/50 rounded-2xl border border-slate-200/80">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
