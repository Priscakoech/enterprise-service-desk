import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Bell, Check, CheckCheck, Trash2, ArrowLeft, Search, ExternalLink } from 'lucide-react';
import api from '../../api/client';
import eventBus from '../../utils/eventBus';

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => { fetchNotifications(); }, []);

  const fetchNotifications = () => {
    api.get('/notifications/').then((r) => setNotifications(r.data)).catch(() => {}).finally(() => setLoading(false));
  };

  const markRead = async (id) => {
    // Optimistic update
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
    eventBus.emit('notifications-changed');
    try {
      await api.post(`/notifications/${id}/mark-read/`);
    } catch {
      fetchNotifications();
    }
  };

  const markAllRead = async () => {
    // Optimistic update
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    eventBus.emit('notifications-changed');
    try {
      await api.post('/notifications/mark-all-read/');
    } catch {
      fetchNotifications();
    }
  };

  const deleteNotif = async (id) => {
    // Optimistic update
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    eventBus.emit('notifications-changed');
    try {
      await api.delete(`/notifications/${id}/`);
    } catch {
      fetchNotifications();
    }
  };

  const handleNotificationClick = (n) => {
    if (!n.is_read) markRead(n.id);
    if (n.reference_type === 'ticket' && n.reference_id) {
      navigate(`/tickets/${n.reference_id}`);
    }
  };

  const hasUnread = notifications.some((n) => !n.is_read);

  const filtered = notifications.filter((n) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (n.title || '').toLowerCase().includes(q) || (n.description || '').toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Notifications</h1>
        <div className="flex-1" />
        {hasUnread && (
          <button
            onClick={markAllRead}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <CheckCheck className="w-4 h-4" /> Mark all as read
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search notifications..."
          className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-[#0f1729] text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400"><Loader2 className="w-5 h-5 animate-spin" /></div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <Bell className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-lg font-medium">{search.trim() ? 'No matching notifications' : 'No notifications'}</p>
            <p className="text-sm mt-1">{search.trim() ? 'Try a different search term.' : "You're all caught up!"}</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.map((n) => (
              <div
                key={n.id}
                onClick={() => handleNotificationClick(n)}
                className={`flex items-start gap-4 px-6 py-4 cursor-pointer ${n.is_read ? 'opacity-60' : ''} hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors`}
              >
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${n.is_read ? 'bg-slate-300 dark:bg-slate-600' : 'bg-blue-500'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-slate-900 dark:text-white">{n.title}</h3>
                    {n.reference_type === 'ticket' && n.reference_id && (
                      <ExternalLink className="w-3 h-3 text-slate-400 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{n.description}</p>
                  <p className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  {!n.is_read && (
                    <button onClick={() => markRead(n.id)} className="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded" title="Mark as read">
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button onClick={() => deleteNotif(n.id)} className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded" title="Delete">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
