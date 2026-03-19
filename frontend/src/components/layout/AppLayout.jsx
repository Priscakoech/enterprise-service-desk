import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Ticket, Plus, Users, Settings, BarChart3, Bell,
  Shield, LogOut, Sun, Moon, Menu, X, Building2, UsersRound, KeyRound
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import api from '../../api/client';
import eventBus from '../../utils/eventBus';
import Avatar from '../ui/Avatar';

const navByRole = {
  requester: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/tickets', icon: Ticket, label: 'My Tickets' },
    { to: '/tickets/new', icon: Plus, label: 'New Ticket' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
  agent: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/tickets', icon: Ticket, label: 'Assigned Tickets' },
    { to: '/tickets/new', icon: Plus, label: 'New Ticket' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
  manager: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/tickets', icon: Ticket, label: 'Department Tickets' },
    { to: '/tickets/new', icon: Plus, label: 'New Ticket' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/teams', icon: Users, label: 'Teams' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
  admin: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/departments', icon: Building2, label: 'Departments' },
    { to: '/teams', icon: UsersRound, label: 'Teams' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/sla', icon: Shield, label: 'SLA Policies' },
    { to: '/signup-code', icon: KeyRound, label: 'Auth Codes' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
};

const roleLabels = {
  requester: 'Requester',
  agent: 'Agent',
  manager: 'Manager',
  admin: 'Administrator',
};

export default function AppLayout() {
  const { dark, toggle } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchUnreadCount = useCallback(() => {
    api.get('/notifications/unread-count/')
      .then((res) => setUnreadCount(res.data.unread_count || 0))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 15000);
    const unsub = eventBus.on('notifications-changed', fetchUnreadCount);
    return () => { clearInterval(interval); unsub(); };
  }, [fetchUnreadCount]);

  const role = user?.role || 'requester';
  const links = navByRole[role] || navByRole.requester;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-30 w-64 flex flex-col
        bg-white dark:bg-[#0b1120] border-r border-slate-200 dark:border-slate-800
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-200 dark:border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Ticket className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-900 dark:text-white leading-tight">Enterprise</h1>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Service Desk</p>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="ml-auto lg:hidden text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <p className="px-3 mb-2 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Menu
          </p>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-slate-200'
                }
              `}
            >
              <link.icon className="w-[18px] h-[18px]" />
              {link.label}
              {link.to === '/notifications' && unreadCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-red-500 ml-auto flex-shrink-0" />
              )}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-slate-200 dark:border-slate-800 p-3">
          <div className="flex items-center gap-3 px-2 py-2">
            <Avatar user={user} size="md" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username}
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">{roleLabels[role]}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 flex items-center gap-4 px-6 bg-white dark:bg-[#0f1729] border-b border-slate-200 dark:border-slate-800">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          <button
            onClick={() => navigate('/notifications')}
            className="relative p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>
          <button
            onClick={toggle}
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-[#070d1a] p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
