import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Plus, Edit3, Trash2, X, Building2, Users, ArrowLeft, UsersRound } from 'lucide-react';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';

export default function DepartmentsPage() {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState([]);
  const [managers, setManagers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [allTeams, setAllTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', manager: '' });

  // Dialog state
  const [dialog, setDialog] = useState(null); // { type: 'agents' | 'teams', dept }

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = () => {
    setLoading(true);
    Promise.all([
      api.get('/teams/departments/'),
      api.get('/accounts/users/'),
      api.get('/teams/'),
    ])
      .then(([dRes, uRes, tRes]) => {
        setDepartments(Array.isArray(dRes.data) ? dRes.data : dRes.data.results || []);
        const users = Array.isArray(uRes.data) ? uRes.data : uRes.data.results || [];
        setAllUsers(users);
        setManagers(users.filter((u) => u.role === 'manager'));
        setAllTeams(Array.isArray(tRes.data) ? tRes.data : tRes.data.results || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const fetchDepartments = () => {
    api.get('/teams/departments/')
      .then((r) => setDepartments(Array.isArray(r.data) ? r.data : r.data.results || []))
      .catch(() => {});
  };

  const resetForm = () => {
    setForm({ name: '', description: '', manager: '' });
    setShowForm(false);
    setEditing(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      name: form.name,
      description: form.description,
      manager: form.manager || null,
    };
    try {
      if (editing) {
        await api.put(`/teams/departments/${editing}/`, payload);
      } else {
        await api.post('/teams/departments/', payload);
      }
      resetForm();
      fetchAll();
    } catch {}
  };

  const handleEdit = (dept) => {
    setEditing(dept.id);
    setForm({
      name: dept.name,
      description: dept.description || '',
      manager: dept.manager || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this department? All associated teams will be affected.')) return;
    try {
      await api.delete(`/teams/departments/${id}/`);
      fetchAll();
    } catch {}
  };

  // Get agents and teams for a specific department
  const getDeptAgents = (deptId) => allUsers.filter((u) => u.role === 'agent' && u.department === deptId);
  const getDeptTeams = (deptId) => allTeams.filter((t) => t.department === deptId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Departments</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Manage organizational departments and their managers
            </p>
          </div>
        </div>
        <button
          onClick={() => { setShowForm(true); setEditing(null); setForm({ name: '', description: '', manager: '' }); }}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Department
        </button>
      </div>

      {/* Inline Form */}
      {showForm && (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              {editing ? 'Edit' : 'New'} Department
            </h2>
            <button onClick={resetForm} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Department Name
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. IT Support"
                required
                className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Brief description of the department (optional)"
                rows={2}
                className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Manager
              </label>
              <select
                value={form.manager}
                onChange={(e) => setForm({ ...form, manager: e.target.value })}
                className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No manager assigned</option>
                {managers.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.first_name && m.last_name ? `${m.first_name} ${m.last_name}` : m.username} ({m.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
              >
                {editing ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Agents / Teams Dialog */}
      {dialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-md mx-4 shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                {dialog.type === 'agents' ? (
                  <Users className="w-4 h-4 text-blue-500" />
                ) : (
                  <UsersRound className="w-4 h-4 text-emerald-500" />
                )}
                <div>
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                    {dialog.type === 'agents' ? 'Agents' : 'Teams'} in {dialog.dept.name}
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {dialog.type === 'agents'
                      ? `${getDeptAgents(dialog.dept.id).length} agent${getDeptAgents(dialog.dept.id).length !== 1 ? 's' : ''}`
                      : `${getDeptTeams(dialog.dept.id).length} team${getDeptTeams(dialog.dept.id).length !== 1 ? 's' : ''}`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setDialog(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto">
              {dialog.type === 'agents' ? (
                getDeptAgents(dialog.dept.id).length === 0 ? (
                  <div className="text-center py-10 text-slate-400 text-sm">
                    No agents in this department
                  </div>
                ) : (
                  getDeptAgents(dialog.dept.id).map((agent) => (
                    <div
                      key={agent.id}
                      className="flex items-center gap-3 px-6 py-3 border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                    >
                      <Avatar user={agent} size="md" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {agent.first_name && agent.last_name ? `${agent.first_name} ${agent.last_name}` : agent.username}
                        </p>
                        {agent.email && (
                          <p className="text-xs text-slate-400 truncate">{agent.email}</p>
                        )}
                      </div>
                      {agent.team_name && (
                        <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md shrink-0">
                          {agent.team_name}
                        </span>
                      )}
                    </div>
                  ))
                )
              ) : (
                getDeptTeams(dialog.dept.id).length === 0 ? (
                  <div className="text-center py-10 text-slate-400 text-sm">
                    No teams in this department
                  </div>
                ) : (
                  getDeptTeams(dialog.dept.id).map((team) => {
                    const memberCount = team.member_ids ? team.member_ids.length : (team.member_details || []).length;
                    return (
                      <div
                        key={team.id}
                        className="flex items-center gap-3 px-6 py-3 border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                      >
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center shrink-0">
                          <UsersRound className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                            {team.name}
                          </p>
                          {team.description && (
                            <p className="text-xs text-slate-400 truncate">{team.description}</p>
                          )}
                        </div>
                        <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md shrink-0">
                          {memberCount} member{memberCount !== 1 ? 's' : ''}
                        </span>
                      </div>
                    );
                  })
                )
              )}
            </div>

            <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setDialog(null)}
                className="px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Department Cards */}
      {loading ? (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        </div>
      ) : departments.length === 0 ? (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <Building2 className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
            <p className="text-lg font-medium">No departments yet</p>
            <p className="text-sm mt-1">Create your first department to organize teams and agents.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((dept) => (
            <div
              key={dept.id}
              className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-50 dark:bg-violet-500/10 flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-violet-600 dark:text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{dept.name}</h3>
                    {dept.manager_name && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Managed by {dept.manager_name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(dept)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(dept.id)}
                    className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {dept.description && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 line-clamp-2">
                  {dept.description}
                </p>
              )}

              <div className="flex items-center gap-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  onClick={() => setDialog({ type: 'agents', dept })}
                  className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
                >
                  <Users className="w-3.5 h-3.5" />
                  <span className="underline decoration-dotted underline-offset-2">{dept.agent_count ?? 0} agent{dept.agent_count !== 1 ? 's' : ''}</span>
                </button>
                <button
                  onClick={() => setDialog({ type: 'teams', dept })}
                  className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors cursor-pointer"
                >
                  <UsersRound className="w-3.5 h-3.5" />
                  <span className="underline decoration-dotted underline-offset-2">{dept.team_count ?? 0} team{dept.team_count !== 1 ? 's' : ''}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
