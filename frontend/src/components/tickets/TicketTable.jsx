import { Link } from 'react-router-dom';
import { StatusBadge, PriorityBadge } from '../shared/Badges';
import { Clock, User } from 'lucide-react';

export default function TicketTable({ tickets, showRequester = false, showAgent = false }) {
  if (!tickets.length) {
    return (
      <div className="text-center py-12 text-slate-500 dark:text-slate-400">
        <p className="text-lg font-medium">No tickets found</p>
        <p className="text-sm mt-1">Tickets will appear here once created.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Ref ID</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Title</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Priority</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Team</th>
            {showRequester && <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Requester</th>}
            {showAgent && <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Agent</th>}
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {tickets.map((t) => (
            <tr key={t.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
              <td className="py-3 px-4">
                <Link to={`/tickets/${t.id}`} className="text-xs font-mono text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap">
                  {t.reference_id || `#${t.id}`}
                </Link>
              </td>
              <td className="py-3 px-4">
                <Link to={`/tickets/${t.id}`} className="text-sm font-medium text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors block max-w-[200px] truncate">
                  {t.title}
                </Link>
              </td>
              <td className="py-3 px-4"><StatusBadge status={t.status} /></td>
              <td className="py-3 px-4"><PriorityBadge priority={t.priority} /></td>
              <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">{t.team_name || '—'}</td>
              {showRequester && (
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400">
                    <User className="w-3.5 h-3.5" />
                    {t.requester_name || `User #${t.requester}`}
                  </span>
                </td>
              )}
              {showAgent && (
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400">
                    <User className="w-3.5 h-3.5" />
                    {t.agent_name || (t.agent ? `Agent #${t.agent}` : 'Unassigned')}
                  </span>
                </td>
              )}
              <td className="py-3 px-4">
                <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                  <Clock className="w-3.5 h-3.5" />
                  {new Date(t.created_at).toLocaleDateString()}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
