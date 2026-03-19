import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Plus, Edit3, Trash2, X, Users, Building2, ArrowLeft } from 'lucide-react';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';

export default function TeamsPage() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', department: '', member_ids: [] });
  const [managingTeam, setManagingTeam] = useState(null);
  const [memberSearch, setMemberSearch] = useState('');

  useEffect(() => {
    fetchTeams();
    fetchDepartments();
    fetchAgents();
  }, []);

  const fetchTeams = () => {
    api.get('/teams/')
      .then((r) => setTeams(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const fetchDepartments = () => {
    api.get('/teams/departments/')
      .then((r) => setDepartments(r.data))
      .catch(() => {});
  };

  const fetchAgents = () => {
    api.get('/accounts/users/')
      .then((r) => setAgents(r.data.filter((u) => u.role === 'agent')))
      .catch(() => {});
  };

  const resetForm = () => {
    setForm({ name: '', description: '', department: '', member_ids: [] });
    setShowForm(false);
    setEditing(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      name: form.name,
      description: form.description,
      department: form.department || null,
      member_ids: form.member_ids,
    };
    try {
      if (editing) {
        await api.put(`/teams/${editing}/`, payload);
      } else {
        await api.post('/teams/', payload);
      }
      resetForm();
      fetchTeams();
    } catch {}
  };

  const handleEdit = (team) => {
    setEditing(team.id);
    setForm({
      name: team.name,
      description: team.description || '',
      department: team.department || '',
      member_ids: team.member_ids || [],
    });
    setShowForm(true);
    setManagingTeam(null);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this team?')) return;
    try {
      await api.delete(`/teams/${id}/`);
      fetchTeams();
    } catch {}
  };

  const toggleMember = (agentId) => {
    setForm((prev) => ({
      ...prev,
      member_ids: prev.member_ids.includes(agentId)
        ? prev.member_ids.filter((id) => id !== agentId)
        : [...prev.member_ids, agentId],
    }));
  };

  const toggleManageMember = (team, agentId) => {
    const currentIds = team.member_ids || [];
    const updatedIds = currentIds.includes(agentId)
      ? currentIds.filter((id) => id !== agentId)
      : [...currentIds, agentId];

    api.put(`/teams/${team.id}/`, {
      name: team.name,
      description: team.description,
      department: team.department,
      member_ids: updatedIds,
    }).then(() => fetchTeams()).catch(() => {});
  };

  const filteredAgents = agents.filter((a) => {
    // If managing a team, only show agents from the same department
    if (managingTeam && managingTeam.department) {
      if (a.department && a.department !== managingTeam.department) return false;
    }
    if (!memberSearch) return true;
    return a.username.toLowerCase().includes(memberSearch.toLowerCase()) || (a.email && a.email.toLowerCase().includes(memberSearch.toLowerCase()));
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Teams</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Manage teams and assign agents
            </p>
          </div>
        </div>
        <button
          onClick={() => { setShowForm(true); setEditing(null); setForm({ name: '', description: '', department: '', member_ids: [] }); setManagingTeam(null); }}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Team
        </button>
      </div>

      {/* Inline Form */}
      {showForm && (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              {editing ? 'Edit' : 'New'} Team
            </h2>
            <button onClick={resetForm} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Team Name
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Tier 1 Support"
                  required
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Department
                </label>
                <select
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Brief description (optional)"
                rows={2}
                className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {/* Member Selection */}
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
                Members ({form.member_ids.length} selected)
              </label>
              {agents.length === 0 ? (
                <p className="text-xs text-slate-400 dark:text-slate-500">No agents available. Create agent users first.</p>
              ) : (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg max-h-48 overflow-y-auto">
                  {agents.map((agent) => (
                    <label
                      key={agent.id}
                      className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/30 cursor-pointer border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                    >
                      <input
                        type="checkbox"
                        checked={form.member_ids.includes(agent.id)}
                        onChange={() => toggleMember(agent.id)}
                        className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500 bg-white dark:bg-slate-800"
                      />
                      <div className="flex items-center gap-2">
                        <Avatar user={agent} size="xs" />
                        <span className="text-sm text-slate-700 dark:text-slate-300">{agent.first_name && agent.last_name ? `${agent.first_name} ${agent.last_name}` : agent.username}</span>
                        {agent.email && (
                          <span className="text-xs text-slate-400">({agent.email})</span>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
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

      {/* Manage Members Modal */}
      {managingTeam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg mx-4 shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Manage Members
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {managingTeam.name} — {(managingTeam.member_ids || []).length} member{(managingTeam.member_ids || []).length !== 1 ? 's' : ''}
                </p>
              </div>
              <button
                onClick={() => { setManagingTeam(null); setMemberSearch(''); }}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-6 py-3 border-b border-slate-200 dark:border-slate-800">
              <input
                type="text"
                value={memberSearch}
                onChange={(e) => setMemberSearch(e.target.value)}
                placeholder="Search agents..."
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="max-h-80 overflow-y-auto">
              {filteredAgents.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">No agents found</div>
              ) : (
                filteredAgents.map((agent) => {
                  const isMember = (managingTeam.member_ids || []).includes(agent.id);
                  return (
                    <div
                      key={agent.id}
                      className="flex items-center justify-between px-6 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/30 border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar user={agent} size="md" />
                        <div>
                          <p className="text-sm font-medium text-slate-900 dark:text-white">{agent.first_name && agent.last_name ? `${agent.first_name} ${agent.last_name}` : agent.username}</p>
                          {agent.email && (
                            <p className="text-xs text-slate-400">{agent.email}</p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => toggleManageMember(managingTeam, agent.id)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          isMember
                            ? 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20'
                            : 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-500/20'
                        }`}
                      >
                        {isMember ? 'Remove' : 'Add'}
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => { setManagingTeam(null); setMemberSearch(''); }}
                className="px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Teams List */}
      {loading ? (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        </div>
      ) : teams.length === 0 ? (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <Users className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
            <p className="text-lg font-medium">No teams yet</p>
            <p className="text-sm mt-1">Create your first team and assign agents.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((team) => {
            const memberDetails = team.member_details || [];
            const memberCount = team.member_ids ? team.member_ids.length : memberDetails.length;
            return (
              <div
                key={team.id}
                className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
              >
                {/* Team Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{team.name}</h3>
                    {team.department_name && (
                      <div className="flex items-center gap-1.5 mt-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        <span className="text-xs text-slate-500 dark:text-slate-400">{team.department_name}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleEdit(team)}
                      className="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(team.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {team.description && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 line-clamp-2">
                    {team.description}
                  </p>
                )}

                {/* Member Avatars */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    {memberDetails.length > 0 ? (
                      <div className="flex -space-x-2">
                        {memberDetails.slice(0, 5).map((member, i) => (
                          <Avatar
                            key={member.id || i}
                            user={member}
                            size="sm"
                            className="border-2 border-white dark:border-[#0f1729]"
                          />
                        ))}
                        {memberCount > 5 && (
                          <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-[10px] font-semibold text-slate-600 dark:text-slate-300 border-2 border-white dark:border-[#0f1729]">
                            +{memberCount - 5}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <Users className="w-3.5 h-3.5" />
                        <span>{memberCount} member{memberCount !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => { setManagingTeam(team); setMemberSearch(''); }}
                    className="px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-lg transition-colors"
                  >
                    Manage Members
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
