import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Ticket, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../api/client';
import TicketTable from '../../components/tickets/TicketTable';

export default function AgentDashboard() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('assigned');

  const fetchTickets = useCallback(() => {
    api.post('/servicedesk/auto-assign/').catch(() => {});
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

  const assignedTickets = tickets.filter((t) => Number(t.agent) === Number(user?.id));
  const myRequests = tickets.filter((t) => Number(t.requester) === Number(user?.id) && Number(t.agent) !== Number(user?.id));
  const displayTickets = view === 'assigned' ? assignedTickets : myRequests;

  const stats = {
    total: assignedTickets.length,
    open: assignedTickets.filter((t) => t.status === 'new' || t.status === 'open').length,
    pending: assignedTickets.filter((t) => t.status === 'pending' || t.status === 'on_hold').length,
    solved: assignedTickets.filter((t) => t.status === 'solved' || t.status === 'closed').length,
  };

  const statCards = [
    {
      label: 'Assigned to Me',
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
  ];

  const urgentTickets = assignedTickets.filter(
    (t) => (t.priority === 'urgent' || t.priority === 'high') && t.status !== 'solved' && t.status !== 'closed'
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Agent Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Welcome back, {user?.first_name || user?.username}. Here are your assigned tickets.
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

      {/* Urgent / High Priority Tickets */}
      {urgentTickets.length > 0 && (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border-2 border-red-300 dark:border-red-500/30">
          <div className="px-6 py-4 border-b border-red-200 dark:border-red-500/20 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <h2 className="text-sm font-semibold text-red-600 dark:text-red-400">
              Urgent Tickets ({urgentTickets.length})
            </h2>
          </div>
          <div className="p-2">
            <TicketTable tickets={urgentTickets} showRequester />
          </div>
        </div>
      )}

      {/* Ticket View Toggle + Table */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-4">
          <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
            <button
              onClick={() => setView('assigned')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                view === 'assigned'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              Assigned to Me ({assignedTickets.length})
            </button>
            <button
              onClick={() => setView('my_requests')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                view === 'my_requests'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              My Requests ({myRequests.length})
            </button>
          </div>
        </div>
        <div className="p-2">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-slate-400">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          ) : (
            <TicketTable tickets={displayTickets} showRequester={view === 'assigned'} showAgent={view === 'my_requests'} />
          )}
        </div>
      </div>
    </div>
  );
}
