import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, ChevronDown, Search } from 'lucide-react';
import api from '../../api/client';

export default function NewTicketPage() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [form, setForm] = useState({
    team: '',
    title: '',
    description: '',
    priority: 'normal',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef(null);

  useEffect(() => {
    api.get('/teams/?all=true')
      .then((r) => setTeams(r.data))
      .catch(() => {});
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setDropdownOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Group teams by department_name
  const grouped = teams.reduce((acc, team) => {
    const dept = team.department_name || 'Other';
    if (!acc[dept]) acc[dept] = [];
    acc[dept].push(team);
    return acc;
  }, {});

  // Filter by search
  const filteredGrouped = Object.entries(grouped).reduce((acc, [dept, deptTeams]) => {
    const q = searchQuery.toLowerCase();
    const filtered = deptTeams.filter(
      (t) => t.name.toLowerCase().includes(q) || dept.toLowerCase().includes(q)
    );
    if (filtered.length > 0) acc[dept] = filtered;
    return acc;
  }, {});

  // Find the selected team object for the routing message
  const selectedTeam = teams.find((t) => String(t.id) === form.team);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const res = await api.post('/servicedesk/tickets/', {
        title: form.title,
        description: form.description,
        team: parseInt(form.team),
        priority: form.priority,
      });
      navigate(`/tickets/${res.data.id}`);
    } catch (err) {
      const data = err.response?.data;
      setError(
        typeof data === 'object'
          ? Object.values(data).flat().join(', ')
          : 'Failed to create ticket'
      );
    }
    setSubmitting(false);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header with back button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Create New Ticket</h1>
      </div>

      {/* Form card */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Service Team */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Service Team
            </label>
            <div ref={dropdownRef} className="relative">
              <button
                type="button"
                onClick={() => { setDropdownOpen(!dropdownOpen); setSearchQuery(''); }}
                className="w-full flex items-center justify-between px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <span className={selectedTeam ? '' : 'text-slate-400'}>
                  {selectedTeam
                    ? `${selectedTeam.department_name} — ${selectedTeam.name}`
                    : 'Select a team'}
                </span>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {dropdownOpen && (
                <div className="absolute z-50 mt-1 w-full max-h-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg flex flex-col overflow-hidden">
                  {/* Search */}
                  <div className="p-2 border-b border-slate-100 dark:border-slate-700">
                    <div className="relative">
                      <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search teams..."
                        className="w-full pl-8 pr-3 py-2 text-sm rounded-md border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        autoFocus
                      />
                    </div>
                  </div>

                  {/* Options list */}
                  <div className="flex-1 min-h-0 overflow-y-auto py-1">
                    {Object.keys(filteredGrouped).length === 0 ? (
                      <p className="px-4 py-3 text-sm text-slate-400 text-center">No teams found</p>
                    ) : (
                      Object.entries(filteredGrouped).map(([deptName, deptTeams]) => (
                        <div key={deptName}>
                          <div className="px-3 py-1.5 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider bg-slate-50 dark:bg-slate-700/50">
                            {deptName}
                          </div>
                          {deptTeams.map((team) => (
                            <button
                              key={team.id}
                              type="button"
                              onClick={() => {
                                setForm({ ...form, team: String(team.id) });
                                setDropdownOpen(false);
                              }}
                              className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                                String(team.id) === form.team
                                  ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium'
                                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                              }`}
                            >
                              {team.name}
                            </button>
                          ))}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            {selectedTeam && (
              <p className="mt-2 text-sm text-blue-600 dark:text-blue-400">
                This will be routed to the {selectedTeam.department_name} department and auto-assigned to an available agent.
              </p>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Title
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief summary of the issue"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={5}
              className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Describe the issue in detail..."
              required
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Priority
            </label>
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          {/* Action buttons */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2.5 text-sm font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
              {submitting ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
