import React from 'react';

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200/80 bg-white py-4 px-6 text-center text-xs text-slate-400">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
        <p>&copy; {new Date().getFullYear()} Apex Training Institute. All rights reserved.</p>
        <div className="flex items-center gap-4 text-slate-500">
          <a href="/verify-certificate" className="hover:text-brand-600 transition-colors">
            Verify Certificate
          </a>
          <span>&bull;</span>
          <span>Version 1.0.0</span>
        </div>
      </div>
    </footer>
  );
}
