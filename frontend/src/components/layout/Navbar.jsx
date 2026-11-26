import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  HiOutlineBars3,
  HiOutlineBell,
  HiOutlineArrowRightOnRectangle,
  HiOutlineUserCircle,
  HiCheck,
} from 'react-icons/hi2';
import { toggleSidebar, toggleMobileSidebar } from '../../store/uiSlice';
import { logout } from '../../store/authSlice';
import {
  setUnreadCount,
  setNotifications,
  markNotificationAsRead,
} from '../../store/notificationSlice';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDateTime } from '../../utils/formatters';

export default function Navbar() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useSelector((state) => state.auth);
  const { unreadCount, notifications } = useSelector((state) => state.notifications);

  const [showNotificationMenu, setShowNotificationMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Poll unread notifications count
  useEffect(() => {
    let isMounted = true;
    const fetchUnread = async () => {
      try {
        const res = await api.get('/api/notifications/unread-count');
        if (isMounted) {
          dispatch(setUnreadCount(res.data.unread_count || 0));
        }
      } catch {
        // silent fail on notification poll
      }
    };

    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [dispatch]);

  const loadNotifications = async () => {
    try {
      const res = await api.get('/api/notifications?page=1&page_size=5');
      dispatch(setNotifications(res.data.items || []));
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleToggleNotifications = () => {
    if (!showNotificationMenu) {
      loadNotifications();
    }
    setShowNotificationMenu(!showNotificationMenu);
    setShowUserMenu(false);
  };

  const handleMarkAsRead = async (id, e) => {
    e.stopPropagation();
    try {
      await api.patch(`/api/notifications/${id}/read`);
      dispatch(markNotificationAsRead(id));
    } catch {
      // silent
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/api/notifications/read-all');
      dispatch(setUnreadCount(0));
      loadNotifications();
      toast.success('All marked as read');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleLogout = () => {
    dispatch(logout());
    toast.success('Logged out successfully');
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/80 bg-white/95 px-4 sm:px-6 backdrop-blur-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={() => dispatch(toggleMobileSidebar())}
          className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 cursor-pointer"
        >
          <HiOutlineBars3 className="text-xl" />
        </button>
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="hidden lg:flex p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 cursor-pointer"
          title="Toggle Sidebar"
        >
          <HiOutlineBars3 className="text-xl" />
        </button>
        <div className="hidden sm:block">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Portal</span>
          <h2 className="text-sm font-bold text-slate-800 -mt-0.5">Apex Training Institute</h2>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={handleToggleNotifications}
            className="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
            title="Notifications"
          >
            <HiOutlineBell className="text-xl" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white shadow-xs animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotificationMenu && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-white shadow-xl ring-1 ring-slate-900/10 border border-slate-100 z-50 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 bg-slate-50/75 border-b border-slate-100">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-xs font-medium text-brand-600 hover:text-brand-700 cursor-pointer"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400">No recent notifications</div>
                ) : (
                  notifications.map((item) => (
                    <div
                      key={item.id}
                      className={`p-3.5 hover:bg-slate-50/80 transition-colors ${
                        !item.is_read ? 'bg-brand-50/20' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-slate-900 truncate">{item.title}</p>
                          <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{item.message}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {formatDateTime(item.created_at)}
                          </span>
                        </div>
                        {!item.is_read && (
                          <button
                            onClick={(e) => handleMarkAsRead(item.id, e)}
                            className="p-1 text-brand-600 hover:text-brand-800 rounded hover:bg-brand-50 cursor-pointer"
                            title="Mark as read"
                          >
                            <HiCheck className="text-sm" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowNotificationMenu(false);
            }}
            className="flex items-center gap-3 p-1 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-xs ring-2 ring-brand-100 shadow-sm">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="hidden md:block text-left pr-1">
              <p className="text-xs font-semibold text-slate-800 leading-tight">{user?.full_name || 'User'}</p>
              <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">{user?.role || 'Member'}</p>
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-white shadow-xl ring-1 ring-slate-900/10 border border-slate-100 py-1.5 z-50">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-900 truncate">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  navigate('/profile');
                }}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 text-left cursor-pointer"
              >
                <HiOutlineUserCircle className="text-base text-slate-400" />
                <span>My Profile & Settings</span>
              </button>
              <div className="border-t border-slate-100 my-1" />
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 text-left cursor-pointer"
              >
                <HiOutlineArrowRightOnRectangle className="text-base text-rose-500" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
