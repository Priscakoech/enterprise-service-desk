import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, TrendingUp, Shield, AlertTriangle, CheckCircle2, Clock, X } from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import api from '../../api/client';
import Avatar from '../../components/ui/Avatar';
import { useAuth } from '../../contexts/AuthContext';

const STATUS_COLORS = {
  new: '#0ea5e9',
  open: '#10b981',
  pending: '#f59e0b',
  on_hold: '#f97316',
  solved: '#8b5cf6',
  closed: '#94a3b8',
};

const PRIORITY_COLORS = {
  urgent: '#ef4444',
  high: '#f97316',
  normal: '#eab308',
  low: '#22c55e',
};

const SLA_COLORS = {
  fulfilled: '#10b981',
  breached: '#ef4444',
  active: '#3b82f6',
  paused: '#f59e0b',
};

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4', '#ec4899'];

const renderPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function AnalyticsPage() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const isManager = currentUser?.role === 'manager';
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [drilldownType, setDrilldownType] = useState(null);

  useEffect(() => {
    api.get('/servicedesk/sla-analytics/')
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-slate-500 dark:text-slate-400">
        <p>Unable to load analytics data.</p>
      </div>
    );
  }

  const {
    status_distribution = [],
    priority_distribution = [],
    team_sla_compliance = [],
    department_sla_compliance = [],
    agent_performance = [],
    sla_summary = {},
    sla_agent_drilldown = {},
    total_tickets = 0,
  } = data;

  const activeAgentDrilldown = Array.isArray(sla_agent_drilldown.active) ? sla_agent_drilldown.active : [];
  const breachedAgentDrilldown = Array.isArray(sla_agent_drilldown.breached) ? sla_agent_drilldown.breached : [];

  // Prepare chart data
  const statusData = status_distribution
    .map((s) => ({ name: (s.status || '').replace(/_/g, ' '), value: s.count, fill: STATUS_COLORS[s.status] || '#94a3b8' }))
    .filter((s) => s.value > 0);

  const priorityData = priority_distribution
    .map((p) => ({ name: p.priority, value: p.count, fill: PRIORITY_COLORS[p.priority] || '#94a3b8' }))
    .filter((p) => p.value > 0);

  const slaPieData = [
    { name: 'Fulfilled', value: sla_summary.fulfilled || 0, fill: SLA_COLORS.fulfilled },
    {
      name: 'Breached',
      value: sla_summary.breached_tickets ?? sla_summary.breached ?? 0,
      fill: SLA_COLORS.breached,
    },
    {
      name: 'Active Policies',
      value: sla_summary.active_policies ?? sla_summary.active ?? 0,
      fill: SLA_COLORS.active,
    },
  ].filter((d) => d.value > 0);

  const teamComplianceData = team_sla_compliance.map((t) => ({
    name: t.team_name || 'Unknown',
    fulfilled: t.fulfilled || 0,
    breached: t.breached || 0,
    active: t.active || 0,
    rate: t.total > 0 ? Math.round((t.fulfilled / t.total) * 100) : 0,
  }));

  const deptComplianceData = department_sla_compliance.map((d) => ({
    name: d.department_name || 'Unknown',
    fulfilled: d.fulfilled || 0,
    breached: d.breached || 0,
    active: d.active || 0,
    rate: d.total > 0 ? Math.round((d.fulfilled / d.total) * 100) : 0,
  }));

  // Best/worst teams
  const sortedTeams = [...teamComplianceData].sort((a, b) => b.rate - a.rate);
  const bestTeam = sortedTeams[0];
  const worstTeam = sortedTeams.length > 1 ? sortedTeams[sortedTeams.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          {isManager ? 'Department Analytics' : 'Analytics'}
        </h1>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard
          icon={<TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
          label="Total Tickets"
          value={total_tickets}
          bgClass="bg-blue-50 dark:bg-blue-500/10"
        />
        <SummaryCard
          icon={<Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />}
          label="SLA Compliance"
          value={sla_summary.compliance_rate != null ? `${Math.round(sla_summary.compliance_rate)}%` : '--'}
          bgClass="bg-emerald-50 dark:bg-emerald-500/10"
        />
        <SummaryCard
          icon={<Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
          label="Active SLA"
          value={sla_summary.active_policies ?? sla_summary.active ?? 0}
          bgClass="bg-blue-50 dark:bg-blue-500/10"
          clickable
          onClick={() => setDrilldownType('active')}
          helperText="Tap to view mapped agents"
        />
        <SummaryCard
          icon={<AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />}
          label="SLA Breached"
          value={sla_summary.breached_tickets ?? sla_summary.breached ?? 0}
          bgClass="bg-red-50 dark:bg-red-500/10"
          clickable
          onClick={() => setDrilldownType('breached')}
          helperText="Tap to view impacted agents"
        />
      </div>

      {drilldownType && (
        <SLADrilldownModal
          type={drilldownType}
          agents={drilldownType === 'active' ? activeAgentDrilldown : breachedAgentDrilldown}
          onClose={() => setDrilldownType(null)}
        />
      )}

      {/* Charts Row 1: Status + Priority + SLA Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard title="Tickets by Status">
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="45%" outerRadius={70} labelLine={false} label={renderPieLabel}>
                  {statusData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard title="Tickets by Priority">
          {priorityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={priorityData} dataKey="value" nameKey="name" cx="50%" cy="45%" outerRadius={70} labelLine={false} label={renderPieLabel}>
                  {priorityData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard title="SLA Distribution">
          {slaPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={slaPieData} dataKey="value" nameKey="name" cx="50%" cy="45%" outerRadius={70} labelLine={false} label={renderPieLabel}>
                  {slaPieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </ChartCard>
      </div>

      {/* Charts Row 2: Team + Department SLA Compliance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Team SLA Compliance">
          {teamComplianceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={teamComplianceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={35} />
                <Tooltip cursor={false} contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
                <Bar dataKey="fulfilled" name="Fulfilled" fill={SLA_COLORS.fulfilled} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="breached" name="Breached" fill={SLA_COLORS.breached} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="active" name="Active" fill={SLA_COLORS.active} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard title="Department SLA Compliance">
          {deptComplianceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={deptComplianceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={35} />
                <Tooltip cursor={false} contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
                <Bar dataKey="fulfilled" name="Fulfilled" fill={SLA_COLORS.fulfilled} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="breached" name="Breached" fill={SLA_COLORS.breached} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="active" name="Active" fill={SLA_COLORS.active} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </ChartCard>
      </div>

      {/* Best / Worst Team */}
      {sortedTeams.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bestTeam && (
            <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Best Performing Team</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{bestTeam.name}</p>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400">{bestTeam.rate}% SLA compliance</p>
                </div>
              </div>
            </div>
          )}
          {worstTeam && worstTeam.name !== bestTeam?.name && (
            <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Needs Improvement</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{worstTeam.name}</p>
                  <p className="text-xs text-red-600 dark:text-red-400">{worstTeam.rate}% SLA compliance</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agent Performance Table */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">Agent Performance</h2>
        {agent_performance.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-4">No agents found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-2 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Agent</th>
                  <th className="text-left py-2 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Assigned</th>
                  <th className="text-left py-2 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Resolved</th>
                  <th className="text-left py-2 px-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Resolution Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {agent_performance.map((a) => (
                  <tr key={a.id}>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <Avatar user={{ profile_picture: a.profile_picture, first_name: a.name?.split(' ')[0], last_name: a.name?.split(' ').slice(1).join(' ') }} size="md" />
                        <div>
                          <p className="text-sm font-medium text-slate-900 dark:text-white">{a.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{a.email}</p>
                          {a.department && <p className="text-xs text-slate-400 dark:text-slate-500">{a.department}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">{a.total_tickets}</td>
                    <td className="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">{a.resolved_tickets}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 dark:bg-slate-800 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full transition-all ${a.resolution_rate >= 80 ? 'bg-emerald-500' : a.resolution_rate >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                            style={{ width: `${a.resolution_rate}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          {a.resolution_rate}%
                        </span>
                      </div>
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

function SummaryCard({ icon, label, value, bgClass, clickable = false, onClick, helperText }) {
  const cardClasses = clickable
    ? 'bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-4 text-left hover:border-blue-300 dark:hover:border-blue-500/40 hover:shadow-sm transition-all cursor-pointer'
    : 'bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-4';

  const CardTag = clickable ? 'button' : 'div';

  return (
    <CardTag className={cardClasses} onClick={clickable ? onClick : undefined}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${bgClass} flex items-center justify-center`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
          <p className="text-lg font-semibold text-slate-900 dark:text-white">{value}</p>
          {helperText && <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{helperText}</p>}
        </div>
      </div>
    </CardTag>
  );
}

function SLADrilldownModal({ type, agents, onClose }) {
  const isBreached = type === 'breached';
  const title = isBreached ? 'Breached SLA Agents' : 'Active SLA Agents';
  const emptyText = isBreached
    ? 'No agents currently have breached SLA instances.'
    : 'No agents are currently mapped to active SLA instances.';

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center px-4">
      <div className="w-full max-w-3xl max-h-[85vh] overflow-hidden bg-white dark:bg-[#0f1729] rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto max-h-[calc(85vh-65px)]">
          {agents.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">{emptyText}</p>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => {
                const instanceCount = isBreached ? agent.breached_instances : agent.active_instances;
                const ticketCount = isBreached ? agent.breached_tickets : agent.active_tickets;
                const metrics = Array.isArray(agent.metric_breakdown) ? agent.metric_breakdown : [];

                return (
                  <div key={agent.id} className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 bg-slate-50/60 dark:bg-slate-900/30">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-3 min-w-0">
                        <Avatar
                          user={{
                            profile_picture: agent.profile_picture,
                            first_name: agent.name?.split(' ')[0],
                            last_name: agent.name?.split(' ').slice(1).join(' '),
                          }}
                          size="md"
                        />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{agent.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{agent.email}</p>
                          {agent.department && (
                            <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">{agent.department}</p>
                          )}
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <p className={`text-lg font-bold ${isBreached ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}`}>
                          {instanceCount}
                        </p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400">
                          {isBreached ? 'breached instances' : 'active instances'}
                        </p>
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                          {ticketCount} ticket{ticketCount === 1 ? '' : 's'}
                        </p>
                      </div>
                    </div>

                    {metrics.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {metrics.map((m) => (
                          <span
                            key={`${agent.id}-${m.metric}-${m.count}`}
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${isBreached ? 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'}`}
                          >
                            {m.metric_label}: {m.count}
                          </span>
                        ))}
                      </div>
                    )}

                    {isBreached && agent.latest_breached_at && (
                      <p className="mt-2 text-[11px] text-slate-400 dark:text-slate-500">
                        Latest breach: {new Date(agent.latest_breached_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6 text-xs">
      <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">{title}</h2>
      {children}
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex items-center justify-center h-[220px] text-slate-400 dark:text-slate-500">
      <p className="text-sm">No data available</p>
    </div>
  );
}
