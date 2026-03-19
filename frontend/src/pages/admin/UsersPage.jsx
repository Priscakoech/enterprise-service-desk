import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Search, Edit3, X, Users, Building2, ArrowLeft, ShieldOff, ShieldCheck, UserX } from 'lucide-react';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';

export default function UsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchUsers();
    fetchDepartments();
  }, []);

  const fetchUsers = () => {
    api.get('/accounts/users/')
      .then((r) => setUsers(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const fetchDepartments = () => {
    api.get('/teams/departments/')
      .then((r) => setDepartments(r.data))
      .catch(() => {});
  };

  const handleUpdate = async () => {
    try {
      await api.patch(`/accounts/users/${editing}/`, editForm);
      setEditing(null);
      setEditForm({});
      fetchUsers();
    } catch {}
  };

  const handleCancel = () => {
    setEditing(null);
    setEditForm({});
  };

  const handleBlacklist = async (id, username) => {
    if (!confirm(`Blacklist user "${username}"? They will be logged out and unable to sign in.`)) return;
    try {
      await api.post(`/accounts/users/${id}/blacklist/`);
      fetchUsers();
    } catch {}
  };

  const handleWhitelist = async (id, username) => {
    if (!confirm(`Whitelist user "${username}"? They will be able to sign in again.`)) return;
    try {
      await api.post(`/accounts/users/${id}/whitelist/`);
      fetchUsers();
    } catch {}
  };

  const handleDelete = async (id, username) => {
    if (!confirm(`Permanently delete user "${username}"? This action cannot be undone.`)) return;
    try {
      await api.delete(`/accounts/users/${id}/`);
      fetchUsers();
    } catch {}
  };

  const filtered = users.filter((u) => {
    const matchesSearch = !search ||
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      (u.email && u.email.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'active' && u.account_status === 'active') ||
      (statusFilter === 'blacklisted' && u.account_status === 'blacklisted') ||
      (statusFilter === 'deactivated' && u.account_status === 'deactivated');
    return matchesSearch && matchesStatus;
  });

  const roleColors = {
    admin: 'bg-red-100 dark:bg-red-500/15 text-red-700 dark:text-red-400',
    manager: 'bg-violet-100 dark:bg-violet-500/15 text-violet-700 dark:text-violet-400',
    agent: 'bg-blue-100 dark:bg-blue-500/15 text-blue-700 dark:text-blue-400',
    requester: 'bg-slate-100 dark:bg-slate-500/15 text-slate-600 dark:text-slate-400',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">User Management</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Manage user roles and department assignments
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <Users className="w-4 h-4" />
          <span>{users.length} total users</span>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by username or email..."
              className="w-full pl-10 pr-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="blacklisted">Blacklisted</option>
            <option value="deactivated">Deactivated</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <p className="text-lg font-medium">
              {search ? 'No users match your search' : 'No users found'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    User
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Username
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Team
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filtered.map((u) => (
                  <tr key={u.id} className={`hover:bg-slate-50 dark:hover:bg-slate-800/30 ${u.account_status === 'blacklisted' ? 'border-l-2 border-l-red-500' : ''}`}>
                    {/* User Avatar + Name */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <Avatar user={u} size="md" />
                        <span className={`text-sm font-medium ${u.account_status === 'blacklisted' ? 'line-through text-slate-400 dark:text-slate-500' : 'text-slate-900 dark:text-white'}`}>
                          {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                        </span>
                      </div>
                    </td>

                    {/* Username */}
                    <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">
                      {u.username}
                    </td>

                    {/* Email */}
                    <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">
                      {u.email || '\u2014'}
                    </td>

                    {/* Role */}
                    <td className="py-3 px-4">
                      {editing === u.id ? (
                        <select
                          value={editForm.role || u.role}
                          onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                          className="px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="requester">Requester</option>
                          <option value="agent">Agent</option>
                          <option value="manager">Manager</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span
                          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                            roleColors[u.role] || roleColors.requester
                          }`}
                        >
                          {u.role}
                        </span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4">
                      {u.account_status === 'blacklisted' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-500/15 text-red-700 dark:text-red-400">
                          Blacklisted
                        </span>
                      ) : u.account_status === 'deactivated' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-500/15 text-slate-600 dark:text-slate-400">
                          Deactivated
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-400">
                          Active
                        </span>
                      )}
                    </td>

                    {/* Department */}
                    <td className="py-3 px-4">
                      {editing === u.id ? (
                        <select
                          value={editForm.department ?? (u.department || '')}
                          onChange={(e) => setEditForm({ ...editForm, department: e.target.value || null })}
                          className="px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">None</option>
                          {departments.map((d) => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {u.department_name ? (
                            <span className="inline-flex items-center gap-1">
                              <Building2 className="w-3 h-3 text-slate-400" />
                              {u.department_name}
                            </span>
                          ) : (
                            '\u2014'
                          )}
                        </span>
                      )}
                    </td>

                    {/* Team */}
                    <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">
                      {u.team_name ? (
                        <span className="inline-flex items-center gap-1">
                          <Users className="w-3 h-3 text-slate-400" />
                          {u.team_name}
                        </span>
                      ) : (
                        '\u2014'
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4">
                      {editing === u.id ? (
                        <div className="flex gap-1">
                          <button
                            onClick={handleUpdate}
                            className="px-2.5 py-1 text-xs rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium transition-colors"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancel}
                            className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <button
                            onClick={() => {
                              setEditing(u.id);
                              setEditForm({ role: u.role, department: u.department || '' });
                            }}
                            className="p-1 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                            title="Edit"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          {u.account_status === 'blacklisted' ? (
                            <button
                              onClick={() => handleWhitelist(u.id, u.username)}
                              className="p-1 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                              title="Whitelist"
                            >
                              <ShieldCheck className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleBlacklist(u.id, u.username)}
                              className="p-1 text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
                              title="Blacklist"
                            >
                              <ShieldOff className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(u.id, u.username)}
                            className="p-1 text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                            title="Delete"
                          >
                            <UserX className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
