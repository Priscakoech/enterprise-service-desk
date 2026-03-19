import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Ticket, Users, BarChart3, CheckCircle2, AlertCircle, Loader2, Building2 } from 'lucide-react';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';
import TicketTable from '../../components/tickets/TicketTable';

export default function ManagerDashboard() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('department');

  const fetchData = useCallback(() => {
    api.post('/servicedesk/auto-assign/').catch(() => {});
    Promise.all([
      api.get('/servicedesk/tickets/'),
      api.get('/accounts/users/'),
    ])
      .then(([tRes, uRes]) => {
        setTickets(tRes.data);
        setUsers(uRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Agents in the manager's department
  const departmentAgents = users.filter(
    (u) => u.role === 'agent' && u.department === user?.department
  );

  const myTickets = tickets.filter((t) => Number(t.requester) === Number(user?.id));
  const displayTickets = view === 'department' ? tickets : myTickets;

  const stats = {
    total: tickets.length,
    open: tickets.filter((t) => t.status === 'new' || t.status === 'open').length,
    pending: tickets.filter((t) => t.status === 'pending' || t.status === 'on_hold').length,
    solved: tickets.filter((t) => t.status === 'solved' || t.status === 'closed').length,
    unassigned: tickets.filter((t) => !t.agent).length,
    agents: departmentAgents.length,
  };

  const statCards = [
    {
      label: 'Total Tickets',
      value: stats.total,
      icon: Ticket,
      color: 'bg-blue-50 dark:bg-blue-500/10',
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Open',
      value: stats.open,
      icon: AlertCircle,
      color: 'bg-emerald-50 dark:bg-emerald-500/10',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
    },
    {
      label: 'Pending/On Hold',
      value: stats.pending,
      icon: Loader2,
      color: 'bg-amber-50 dark:bg-amber-500/10',
      iconColor: 'text-amber-600 dark:text-amber-400',
    },
    {
      label: 'Solved',
      value: stats.solved,
      icon: CheckCircle2,
      color: 'bg-violet-50 dark:bg-violet-500/10',
      iconColor: 'text-violet-600 dark:text-violet-400',
    },
    {
      label: 'Unassigned',
      value: stats.unassigned,
      icon: AlertCircle,
      color: 'bg-red-50 dark:bg-red-500/10',
      iconColor: 'text-red-600 dark:text-red-400',
    },
    {
      label: 'Active Agents',
      value: stats.agents,
      icon: Users,
      color: 'bg-indigo-50 dark:bg-indigo-500/10',
      iconColor: 'text-indigo-600 dark:text-indigo-400',
    },
  ];

  // Agent workload: count tickets per department agent
  const agentWorkload = departmentAgents
    .map((a) => ({
      ...a,
      ticketCount: tickets.filter((t) => t.agent === a.id).length,
    }))
    .sort((a, b) => b.ticketCount - a.ticketCount);

  const maxTickets = Math.max(...agentWorkload.map((a) => a.ticketCount), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Manager Dashboard</h1>
            {user?.department_name && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                <Building2 className="w-3.5 h-3.5" />
                {user.department_name}
              </span>
            )}
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Department overview and ticket analytics
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/analytics"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <BarChart3 className="w-4 h-4" /> Analytics
          </Link>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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

      {/* Main Content: Agent Workload Sidebar + Tickets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Workload Sidebar */}
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Agent Workload
            </h2>
          </div>
          <div className="p-4 space-y-3">
            {agentWorkload.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-4">
                No agents in this department
              </p>
            )}
            {agentWorkload.map((a) => (
              <div key={a.id} className="flex items-center gap-3">
                <Avatar user={a} size="md" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {a.first_name && a.last_name
                      ? `${a.first_name} ${a.last_name}`
                      : a.username}
                  </p>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-1">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${(a.ticketCount / maxTickets) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm font-semibold text-slate-900 dark:text-white tabular-nums">
                  {a.ticketCount}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Tickets with Toggle */}
        <div className="lg:col-span-2 bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <button
                onClick={() => setView('department')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  view === 'department'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                Department Tickets ({tickets.length})
              </button>
              <button
                onClick={() => setView('my_tickets')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  view === 'my_tickets'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                My Tickets ({myTickets.length})
              </button>
            </div>
            <Link
              to="/tickets"
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              View all
            </Link>
          </div>
          <div className="p-2">
            {loading ? (
              <div className="flex items-center justify-center py-12 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : (
              <TicketTable tickets={displayTickets.slice(0, 8)} showRequester showAgent />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
