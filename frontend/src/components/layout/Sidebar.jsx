import React from 'react';
import { NavLink } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  HiOutlineSquares2X2,
  HiOutlineAcademicCap,
  HiOutlineUserGroup,
  HiOutlineDocumentText,
  HiOutlineClipboardDocumentList,
  HiOutlineCheckBadge,
  HiOutlineCreditCard,
  HiOutlineMegaphone,
  HiOutlineChartBar,
  HiOutlineUsers,
  HiOutlineBookOpen,
  HiOutlineIdentification,
  HiXMark,
} from 'react-icons/hi2';
import { setMobileSidebarOpen } from '../../store/uiSlice';
import { ROLES } from '../../utils/constants';

export default function Sidebar() {
  const dispatch = useDispatch();
  const { sidebarOpen, mobileSidebarOpen } = useSelector((state) => state.ui);
  const { role } = useSelector((state) => state.auth);

  const getNavLinks = () => {
    switch (role) {
      case ROLES.ADMIN:
        return [
          { to: '/dashboard', label: 'Dashboard', icon: HiOutlineSquares2X2 },
          { to: '/courses', label: 'Courses & Curriculum', icon: HiOutlineAcademicCap },
          { to: '/batches', label: 'Batches & Rosters', icon: HiOutlineUserGroup },
          { to: '/enrollments', label: 'Enrollments', icon: HiOutlineBookOpen },
          { to: '/users', label: 'User Directory', icon: HiOutlineUsers },
          { to: '/students', label: 'Students', icon: HiOutlineIdentification },
          { to: '/instructors', label: 'Instructors', icon: HiOutlineUserGroup },
          { to: '/attendance', label: 'Attendance', icon: HiOutlineClipboardDocumentList },
          { to: '/payments', label: 'Fee Payments', icon: HiOutlineCreditCard },
          { to: '/certificates', label: 'Certificates', icon: HiOutlineCheckBadge },
          { to: '/announcements', label: 'Announcements', icon: HiOutlineMegaphone },
          { to: '/reports', label: 'Reports & Export', icon: HiOutlineChartBar },
        ];
      case ROLES.INSTRUCTOR:
        return [
          { to: '/dashboard', label: 'Dashboard', icon: HiOutlineSquares2X2 },
          { to: '/courses', label: 'My Assigned Courses', icon: HiOutlineAcademicCap },
          { to: '/batches', label: 'My Batches', icon: HiOutlineUserGroup },
          { to: '/students', label: 'Students Roster', icon: HiOutlineIdentification },
          { to: '/assignments', label: 'Assignments', icon: HiOutlineDocumentText },
          { to: '/submissions', label: 'Grade Submissions', icon: HiOutlineClipboardDocumentList },
          { to: '/quizzes', label: 'Quizzes & MCQs', icon: HiOutlineCheckBadge },
          { to: '/attendance', label: 'Mark Attendance', icon: HiOutlineClipboardDocumentList },
          { to: '/announcements', label: 'Announcements', icon: HiOutlineMegaphone },
          { to: '/reports', label: 'Course Reports', icon: HiOutlineChartBar },
        ];
      case ROLES.STUDENT:
      default:
        return [
          { to: '/dashboard', label: 'Dashboard', icon: HiOutlineSquares2X2 },
          { to: '/courses', label: 'My Courses & Lectures', icon: HiOutlineAcademicCap },
          { to: '/batches', label: 'My Batches', icon: HiOutlineUserGroup },
          { to: '/assignments', label: 'My Assignments', icon: HiOutlineDocumentText },
          { to: '/quizzes', label: 'My Quizzes', icon: HiOutlineCheckBadge },
          { to: '/attendance', label: 'My Attendance', icon: HiOutlineClipboardDocumentList },
          { to: '/certificates', label: 'My Certificates', icon: HiOutlineCheckBadge },
          { to: '/payments', label: 'Fee Invoices', icon: HiOutlineCreditCard },
          { to: '/announcements', label: 'Announcements', icon: HiOutlineMegaphone },
        ];
    }
  };

  const navLinks = getNavLinks();

  const renderNavContent = () => (
    <div className="flex h-full flex-col justify-between">
      <div>
        {/* Brand header */}
        <div className="flex h-16 items-center justify-between px-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 text-white flex items-center justify-center font-black text-lg shadow-md shadow-brand-500/25">
              A
            </div>
            {sidebarOpen && (
              <div className="truncate">
                <h1 className="text-sm font-bold text-slate-900 tracking-tight">Apex Academy</h1>
                <p className="text-[10px] font-semibold text-brand-600 uppercase tracking-widest">
                  LMS Enterprise
                </p>
              </div>
            )}
          </div>
          {/* Mobile close */}
          <button
            onClick={() => dispatch(setMobileSidebarOpen(false))}
            className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 cursor-pointer"
          >
            <HiXMark className="text-xl" />
          </button>
        </div>

        {/* Navigation list */}
        <nav className="p-3 space-y-1">
          {navLinks.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => dispatch(setMobileSidebarOpen(false))}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/20'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`
                }
                title={!sidebarOpen ? item.label : undefined}
              >
                <Icon className="text-lg shrink-0" />
                {sidebarOpen && <span className="truncate">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Role tag footer */}
      {sidebarOpen && (
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 m-3 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Signed In Role</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-100 text-brand-700">
              {role || 'Guest'}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden lg:block shrink-0 bg-white border-r border-slate-200/80 transition-all duration-200 ease-in-out ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <div className="sticky top-0 h-screen">{renderNavContent()}</div>
      </aside>

      {/* Mobile drawer backdrop */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => dispatch(setMobileSidebarOpen(false))}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-2xl transition-transform duration-200 ease-in-out lg:hidden ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {renderNavContent()}
      </aside>
    </>
  );
}
