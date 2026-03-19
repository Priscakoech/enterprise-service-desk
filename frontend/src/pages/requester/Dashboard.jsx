import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Ticket, Plus, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../api/client';
import TicketTable from '../../components/tickets/TicketTable';

export default function RequesterDashboard() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTickets = useCallback(() => {
    api.get('/servicedesk/tickets/')
      .then((r) => setTickets(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTickets();
    const interval = setInterval(fetchTickets, 15000);
    return () => clearInterval(interval);
  }, [fetchTickets]);

  const stats = {
    total: tickets.length,
    open: tickets.filter((t) => t.status === 'new' || t.status === 'open').length,
    pending: tickets.filter((t) => t.status === 'pending' || t.status === 'on_hold').length,
    solved: tickets.filter((t) => t.status === 'solved' || t.status === 'closed').length,
  };

  const statCards = [
    { label: 'Total Tickets', value: stats.total, icon: Ticket, color: 'blue' },
    { label: 'Open', value: stats.open, icon: AlertCircle, color: 'emerald' },
    { label: 'Pending/On Hold', value: stats.pending, icon: Loader2, color: 'amber' },
    { label: 'Solved', value: stats.solved, icon: CheckCircle2, color: 'violet' },
  ];

  const colorMap = {
    blue: { bg: 'bg-blue-50 dark:bg-blue-500/10', icon: 'text-blue-600 dark:text-blue-400' },
    emerald: { bg: 'bg-emerald-50 dark:bg-emerald-500/10', icon: 'text-emerald-600 dark:text-emerald-400' },
    amber: { bg: 'bg-amber-50 dark:bg-amber-500/10', icon: 'text-amber-600 dark:text-amber-400' },
    violet: { bg: 'bg-violet-50 dark:bg-violet-500/10', icon: 'text-violet-600 dark:text-violet-400' },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Welcome, {user?.first_name || user?.username}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Here's an overview of your support tickets
          </p>
        </div>
        <Link
          to="/tickets/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> New Ticket
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s) => {
          const c = colorMap[s.color];
          return (
            <div
              key={s.label}
              className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  {s.label}
                </span>
                <div className={`w-9 h-9 rounded-lg ${c.bg} flex items-center justify-center`}>
                  <s.icon className={`w-[18px] h-[18px] ${c.icon}`} />
                </div>
              </div>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{s.value}</p>
            </div>
          );
        })}
      </div>

      {/* Recent Tickets */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Recent Tickets</h2>
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
            <TicketTable tickets={tickets.slice(0, 5)} showAgent />
          )}
        </div>
      </div>
    </div>
  );
}
