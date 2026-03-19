import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  Users,
  Shield,
  Loader2,
  Building2,
  Activity,
  UsersRound,
} from 'lucide-react';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [slaCount, setSlaCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(() => {
    api.post('/servicedesk/auto-assign/').catch(() => {});
    Promise.all([
      api.get('/accounts/users/'),
      api.get('/teams/'),
      api.get('/teams/departments/'),
      api.get('/servicedesk/sla-policies/').catch(() => ({ data: [] })),
    ])
      .then(([uRes, tRes, dRes, sRes]) => {
        setUsers(uRes.data);
        setTeams(Array.isArray(tRes.data) ? tRes.data : tRes.data.results || []);
        setDepartments(Array.isArray(dRes.data) ? dRes.data : dRes.data.results || []);
        setSlaCount(Array.isArray(sRes.data) ? sRes.data.length : 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const stats = {
    totalUsers: users.length,
    totalDepartments: departments.length,
    totalTeams: teams.length,
    activeSLA: slaCount,
  };

  const statCards = [
    {
      label: 'Total Users',
      value: stats.totalUsers,
      icon: Users,
      color: 'bg-violet-50 dark:bg-violet-500/10',
      iconColor: 'text-violet-600 dark:text-violet-400',
    },
    {
      label: 'Departments',
      value: stats.totalDepartments,
      icon: Building2,
      color: 'bg-amber-50 dark:bg-amber-500/10',
      iconColor: 'text-amber-600 dark:text-amber-400',
    },
    {
      label: 'Teams',
      value: stats.totalTeams,
      icon: UsersRound,
      color: 'bg-emerald-50 dark:bg-emerald-500/10',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
    },
    {
      label: 'Active SLA Policies',
      value: stats.activeSLA,
      icon: Shield,
      color: 'bg-blue-50 dark:bg-blue-500/10',
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
  ];

  const quickLinks = [
    { to: '/users', label: 'Manage Users', icon: Users, desc: `${stats.totalUsers} users` },
    {
      to: '/departments',
      label: 'Departments',
      icon: Building2,
      desc: `${stats.totalDepartments} departments`,
    },
    {
      to: '/teams',
      label: 'Teams',
      icon: UsersRound,
      desc: `${teams.length} teams`,
    },
    { to: '/sla', label: 'SLA Policies', icon: Shield, desc: 'Manage SLAs' },
  ];

  // Build recent activity from user data
  const recentUsers = [...users]
    .sort((a, b) => new Date(b.date_joined || 0) - new Date(a.date_joined || 0))
    .slice(0, 5);

  const roleBreakdown = {
    admins: users.filter((u) => u.role === 'admin').length,
    managers: users.filter((u) => u.role === 'manager').length,
    agents: users.filter((u) => u.role === 'agent').length,
    requesters: users.filter((u) => u.role === 'requester').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          System overview and configuration
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s) => (
          <div
            key={s.label}
            className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                {s.label}
              </span>
              <div className={`w-9 h-9 rounded-lg ${s.color} flex items-center justify-center`}>
                <s.icon className={`w-[18px] h-[18px] ${s.iconColor}`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickLinks.map((ql) => (
          <Link
            key={ql.to}
            to={ql.to}
            className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:border-blue-300 dark:hover:border-blue-500/30 transition-colors group"
          >
            <ql.icon className="w-8 h-8 text-slate-400 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors mb-3" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{ql.label}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{ql.desc}</p>
          </Link>
        ))}
      </div>

      {/* System Info Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Role Breakdown */}
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Users by Role</h2>
          </div>
          <div className="p-6 space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-8 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : (
              Object.entries(roleBreakdown).map(([role, count]) => {
                const maxRole = Math.max(...Object.values(roleBreakdown), 1);
                return (
                  <div key={role}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize text-slate-600 dark:text-slate-400">{role}</span>
                      <span className="font-medium text-slate-900 dark:text-white">{count}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${(count / maxRole) * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Recent Users</h2>
          </div>
          <div className="p-4">
            {loading ? (
              <div className="flex items-center justify-center py-8 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : recentUsers.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-4">No users found</p>
            ) : (
              <div className="space-y-3">
                {recentUsers.map((u) => (
                  <div key={u.id} className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <Avatar user={u} size="md" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                        {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{u.role}</p>
                    </div>
                    {u.date_joined && (
                      <span className="text-xs text-slate-400 dark:text-slate-500 shrink-0">
                        {new Date(u.date_joined).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
