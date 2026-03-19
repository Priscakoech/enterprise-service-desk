import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Plus, Trash2, X, ChevronUp, ChevronDown, Edit3,
  Shield, Loader2, CheckCircle2, AlertTriangle, Clock,
  ToggleLeft, ToggleRight,
} from 'lucide-react';
import api from '../../api/client';

const METRICS = [
  { key: 'first_reply_time', label: 'First Reply Time' },
  { key: 'next_reply_time', label: 'Next Reply Time' },
  { key: 'pausable_update_time', label: 'Pausable Update Time' },
  { key: 'requester_wait_time', label: 'Requester Wait Time' },
  { key: 'agent_work_time', label: 'Agent Work Time' },
  { key: 'total_resolution_time', label: 'Total Resolution Time' },
];

const PRIORITIES = [
  { key: 'urgent', label: 'Urgent', color: 'red' },
  { key: 'high', label: 'High', color: 'orange' },
  { key: 'normal', label: 'Normal', color: 'yellow' },
  { key: 'low', label: 'Low', color: 'green' },
];

const PRIORITY_BADGE_CLASSES = {
  urgent: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400',
  high: 'bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400',
  normal: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400',
  low: 'bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400',
};

const DEFAULT_TARGETS = () =>
  PRIORITIES.reduce((acc, p) => {
    acc[p.key] = METRICS.reduce((m, metric) => {
      m[metric.key] = '';
      return m;
    }, {});
    return acc;
  }, {});

const EMPTY_FORM = {
  name: '',
  description: '',
  is_active: true,
  is_default: false,
  team: '',
  department: '',
  schedule: '',
  conditions: { priorities: [], department: '' },
  targets: DEFAULT_TARGETS(),
};

export default function SLAPage() {
  const navigate = useNavigate();

  // Data state
  const [policies, setPolicies] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [dashboard, setDashboard] = useState(null);

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM, targets: DEFAULT_TARGETS() });
  const [activeTargetTab, setActiveTargetTab] = useState('urgent');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = () => {
    setLoading(true);
    Promise.all([
      api.get('/servicedesk/sla-policies/').catch(() => ({ data: [] })),
      api.get('/servicedesk/business-schedules/').catch(() => ({ data: [] })),
      api.get('/teams/departments/').catch(() => ({ data: [] })),
      api.get('/servicedesk/sla-dashboard/').catch(() => ({ data: null })),
      api.get('/teams/').catch(() => ({ data: [] })),
    ]).then(([policiesRes, schedulesRes, deptsRes, dashRes, teamsRes]) => {
      setPolicies(Array.isArray(policiesRes.data) ? policiesRes.data : policiesRes.data.results || []);
      setSchedules(Array.isArray(schedulesRes.data) ? schedulesRes.data : schedulesRes.data.results || []);
      setDepartments(Array.isArray(deptsRes.data) ? deptsRes.data : deptsRes.data.results || []);
      setDashboard(dashRes.data);
      setTeams(Array.isArray(teamsRes.data) ? teamsRes.data : teamsRes.data.results || []);
    }).finally(() => setLoading(false));
  };

  const fetchPolicies = () => {
    api.get('/servicedesk/sla-policies/')
      .then((r) => setPolicies(Array.isArray(r.data) ? r.data : r.data.results || []))
      .catch(() => {});
  };

  const fetchDashboard = () => {
    api.get('/servicedesk/sla-dashboard/')
      .then((r) => setDashboard(r.data))
      .catch(() => {});
  };

  // --- Form helpers ---

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, targets: DEFAULT_TARGETS() });
    setShowForm(false);
    setEditing(null);
    setActiveTargetTab('urgent');
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, targets: DEFAULT_TARGETS() });
    setShowForm(true);
    setActiveTargetTab('urgent');
  };

  const openEdit = async (policy) => {
    setEditing(policy.id);
    setActiveTargetTab('urgent');

    // Build conditions from policy data
    const conditions = {
      priorities: policy.conditions?.priorities || [],
      department: policy.conditions?.department || '',
    };

    // Build targets map from existing targets
    const targets = DEFAULT_TARGETS();
    try {
      const res = await api.get(`/servicedesk/sla-policies/${policy.id}/targets/`);
      const targetList = Array.isArray(res.data) ? res.data : res.data.results || [];
      targetList.forEach((t) => {
        if (targets[t.priority] && targets[t.priority][t.metric] !== undefined) {
          targets[t.priority][t.metric] = t.target_minutes ?? '';
        }
      });
    } catch {
      // If targets fetch fails, use empty defaults
    }

    setForm({
      name: policy.name || '',
      description: policy.description || '',
      is_active: policy.is_active !== false,
      is_default: policy.is_default || false,
      team: policy.team || '',
      department: policy.department || '',
      schedule: policy.schedule || '',
      conditions,
      targets,
    });
    setShowForm(true);
  };

  // --- CRUD ---

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      name: form.name,
      description: form.description,
      is_active: form.is_active,
      is_default: form.is_default,
      team: form.team || null,
      department: form.department || null,
      schedule: form.schedule || null,
      conditions: {
        priorities: form.conditions.priorities,
        department: form.conditions.department || null,
      },
    };

    try {
      let policyId;
      if (editing) {
        await api.put(`/servicedesk/sla-policies/${editing}/`, payload);
        policyId = editing;
      } else {
        const res = await api.post('/servicedesk/sla-policies/', payload);
        policyId = res.data.id;
      }

      // Save targets - first delete existing targets if editing
      if (editing) {
        try {
          const existingRes = await api.get(`/servicedesk/sla-policies/${policyId}/targets/`);
          const existing = Array.isArray(existingRes.data) ? existingRes.data : existingRes.data.results || [];
          await Promise.all(existing.map((t) => api.delete(`/servicedesk/sla-targets/${t.id}/`).catch(() => {})));
        } catch {
          // Continue even if cleanup fails
        }
      }

      // Create new targets for every non-empty value
      const targetPromises = [];
      for (const priority of PRIORITIES) {
        for (const metric of METRICS) {
          const val = form.targets[priority.key]?.[metric.key];
          if (val !== '' && val !== null && val !== undefined) {
            const minutes = parseInt(val, 10);
            if (!isNaN(minutes) && minutes > 0) {
              targetPromises.push(
                api.post(`/servicedesk/sla-policies/${policyId}/targets/`, {
                  priority: priority.key,
                  metric: metric.key,
                  target_minutes: minutes,
                }).catch(() => {})
              );
            }
          }
        }
      }
      await Promise.all(targetPromises);

      resetForm();
      fetchPolicies();
      fetchDashboard();
    } catch {
      // Error handled silently
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this SLA policy? This cannot be undone.')) return;
    try {
      await api.delete(`/servicedesk/sla-policies/${id}/`);
      fetchPolicies();
      fetchDashboard();
    } catch {}
  };

  const handleToggleActive = async (policy) => {
    try {
      await api.patch(`/servicedesk/sla-policies/${policy.id}/`, {
        is_active: !policy.is_active,
      });
      fetchPolicies();
    } catch {}
  };

  const handleReorder = async (policyId, direction) => {
    const idx = policies.findIndex((p) => p.id === policyId);
    if (idx < 0) return;
    const newIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (newIdx < 0 || newIdx >= policies.length) return;

    // Optimistic reorder
    const reordered = [...policies];
    [reordered[idx], reordered[newIdx]] = [reordered[newIdx], reordered[idx]];
    setPolicies(reordered);

    try {
      await api.post('/servicedesk/sla-policies/reorder/', {
        ordered_ids: reordered.map((p) => p.id),
      });
      fetchPolicies();
    } catch {
      fetchPolicies(); // Revert on failure
    }
  };

  // --- Condition helpers ---

  const togglePriorityCondition = (priorityKey) => {
    setForm((prev) => {
      const current = prev.conditions.priorities || [];
      const updated = current.includes(priorityKey)
        ? current.filter((p) => p !== priorityKey)
        : [...current, priorityKey];
      return { ...prev, conditions: { ...prev.conditions, priorities: updated } };
    });
  };

  // --- Target helpers ---

  const setTargetValue = (priority, metric, value) => {
    setForm((prev) => ({
      ...prev,
      targets: {
        ...prev.targets,
        [priority]: {
          ...prev.targets[priority],
          [metric]: value,
        },
      },
    }));
  };

  const countTargets = (policy) => {
    return policy.target_count ?? policy.targets_count ?? 0;
  };

  // --- Sorting ---

  const sortedPolicies = [...policies].sort((a, b) => (a.position ?? 0) - (b.position ?? 0));

  // --- Render ---

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">SLA Policies</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Define service level targets and track compliance
            </p>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Policy
        </button>
      </div>

      {/* Dashboard Stats */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DashboardCard
            icon={<Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
            label="Compliance Rate"
            value={dashboard.compliance_rate != null ? `${Math.round(dashboard.compliance_rate)}%` : '--'}
            bgClass="bg-blue-50 dark:bg-blue-500/10"
          />
          <DashboardCard
            icon={<CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />}
            label="Fulfilled"
            value={dashboard.fulfilled_count ?? dashboard.fulfilled ?? 0}
            bgClass="bg-green-50 dark:bg-green-500/10"
          />
          <DashboardCard
            icon={<AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />}
            label="Breached"
            value={dashboard.breached_count ?? dashboard.breached ?? 0}
            bgClass="bg-red-50 dark:bg-red-500/10"
          />
          <DashboardCard
            icon={<Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />}
            label="Active Instances"
            value={dashboard.active_count ?? dashboard.active ?? 0}
            bgClass="bg-amber-50 dark:bg-amber-500/10"
          />
        </div>
      )}

      {/* Create/Edit Form */}
      {showForm && (
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              {editing ? 'Edit' : 'New'} SLA Policy
            </h2>
            <button onClick={resetForm} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Policy Name
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Critical Incident SLA"
                  required
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Business Schedule
                </label>
                <select
                  value={form.schedule}
                  onChange={(e) => setForm({ ...form, schedule: e.target.value })}
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No schedule (24/7)</option>
                  {schedules.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
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
                placeholder="Describe when this SLA policy applies and its purpose"
                rows={2}
                className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {/* Active Toggle */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setForm({ ...form, is_active: !form.is_active })}
                className="text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                {form.is_active ? (
                  <ToggleRight className="w-8 h-5 text-blue-600 dark:text-blue-400" />
                ) : (
                  <ToggleLeft className="w-8 h-5" />
                )}
              </button>
              <span className="text-sm text-slate-700 dark:text-slate-300">
                {form.is_active ? 'Active' : 'Inactive'} -- policy will {form.is_active ? '' : 'not '}be evaluated on new tickets
              </span>
            </div>

            {/* Team / Department Mapping + Default Policy */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Team (auto-apply to tickets in this team)
                </label>
                <select
                  value={form.team}
                  onChange={(e) => setForm({ ...form, team: e.target.value })}
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No specific team</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}{t.department_name ? ` (${t.department_name})` : ''}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Department (auto-apply to tickets in this department)
                </label>
                <select
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No specific department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, is_default: !form.is_default })}
                    className="text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    {form.is_default ? (
                      <ToggleRight className="w-8 h-5 text-amber-600 dark:text-amber-400" />
                    ) : (
                      <ToggleLeft className="w-8 h-5" />
                    )}
                  </button>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Default Policy -- used when no other policy matches
                  </span>
                </div>
              </div>
            </div>

            {/* Conditions */}
            <div>
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
                Conditions
              </h3>
              <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 space-y-4 bg-slate-50/50 dark:bg-slate-800/20">
                {/* Priority Filter */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
                    Priority Filter (apply to selected priorities, or all if none selected)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {PRIORITIES.map((p) => {
                      const selected = form.conditions.priorities.includes(p.key);
                      return (
                        <button
                          key={p.key}
                          type="button"
                          onClick={() => togglePriorityCondition(p.key)}
                          className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                            selected
                              ? `${PRIORITY_BADGE_CLASSES[p.key]} border-current`
                              : 'border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600'
                          }`}
                        >
                          {selected && <CheckCircle2 className="w-3 h-3 mr-1.5" />}
                          {p.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Department Filter */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Department Filter
                  </label>
                  <select
                    value={form.conditions.department}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        conditions: { ...form.conditions, department: e.target.value },
                      })
                    }
                    className="w-full max-w-sm px-4 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All departments</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Targets */}
            <div>
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
                SLA Targets (minutes)
              </h3>

              {/* Priority Tabs */}
              <div className="flex border-b border-slate-200 dark:border-slate-700 mb-4">
                {PRIORITIES.map((p) => {
                  const isActive = activeTargetTab === p.key;
                  const hasValues = METRICS.some(
                    (m) => form.targets[p.key]?.[m.key] !== '' && form.targets[p.key]?.[m.key] != null
                  );
                  return (
                    <button
                      key={p.key}
                      type="button"
                      onClick={() => setActiveTargetTab(p.key)}
                      className={`relative px-4 py-2.5 text-xs font-medium transition-colors ${
                        isActive
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                    >
                      {p.label}
                      {hasValues && (
                        <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-blue-500" />
                      )}
                      {isActive && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-t" />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Metric Inputs for Active Tab */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {METRICS.map((metric) => (
                  <div key={metric.key}>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      {metric.label}
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        min="0"
                        value={form.targets[activeTargetTab]?.[metric.key] ?? ''}
                        onChange={(e) => setTargetValue(activeTargetTab, metric.key, e.target.value)}
                        placeholder="--"
                        className="w-full px-4 py-2.5 pr-16 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 dark:text-slate-500 pointer-events-none">
                        minutes
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                {editing ? 'Update Policy' : 'Create Policy'}
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

      {/* Policies List */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        ) : sortedPolicies.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <Shield className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
            <p className="text-lg font-medium">No SLA policies yet</p>
            <p className="text-sm mt-1">Create your first SLA policy to start tracking service level targets.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {sortedPolicies.map((policy, idx) => (
              <div
                key={policy.id}
                className={`flex items-center gap-4 px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors ${
                  !policy.is_active ? 'opacity-60' : ''
                }`}
              >
                {/* Reorder Arrows */}
                <div className="flex flex-col gap-0.5">
                  <button
                    onClick={() => handleReorder(policy.id, 'up')}
                    disabled={idx === 0}
                    className="p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-colors"
                    title="Move up"
                  >
                    <ChevronUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleReorder(policy.id, 'down')}
                    disabled={idx === sortedPolicies.length - 1}
                    className="p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-colors"
                    title="Move down"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>

                {/* Policy Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {policy.name}
                    </h3>
                    {!policy.is_active && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">
                        Inactive
                      </span>
                    )}
                    {policy.is_default && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400">
                        Default
                      </span>
                    )}
                    {policy.team_name && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400">
                        {policy.team_name}
                      </span>
                    )}
                    {policy.department_name && !policy.team_name && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-violet-50 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400">
                        {policy.department_name}
                      </span>
                    )}
                    {policy.conditions?.priorities?.length > 0 && (
                      <div className="flex gap-1">
                        {policy.conditions.priorities.map((pk) => {
                          const pri = PRIORITIES.find((p) => p.key === pk);
                          if (!pri) return null;
                          return (
                            <span
                              key={pk}
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${PRIORITY_BADGE_CLASSES[pk]}`}
                            >
                              {pri.label}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  {policy.description && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                      {policy.description}
                    </p>
                  )}
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-[11px] text-slate-400 dark:text-slate-500">
                      {countTargets(policy)} target{countTargets(policy) !== 1 ? 's' : ''} defined
                    </span>
                    {policy.schedule_name && (
                      <span className="text-[11px] text-slate-400 dark:text-slate-500">
                        Schedule: {policy.schedule_name}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleToggleActive(policy)}
                    className="p-1.5 rounded transition-colors"
                    title={policy.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {policy.is_active ? (
                      <ToggleRight className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
                    )}
                  </button>
                  <button
                    onClick={() => openEdit(policy)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded transition-colors"
                    title="Edit policy"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(policy.id)}
                    className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded transition-colors"
                    title="Delete policy"
                  >
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

// --- Dashboard Stat Card ---

function DashboardCard({ icon, label, value, bgClass }) {
  return (
    <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${bgClass} flex items-center justify-center`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
          <p className="text-lg font-semibold text-slate-900 dark:text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}
