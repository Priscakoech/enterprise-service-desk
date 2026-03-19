const statusMap = {
  new: { bg: 'bg-sky-100 dark:bg-sky-500/15', text: 'text-sky-700 dark:text-sky-400', dot: 'bg-sky-500' },
  open: { bg: 'bg-emerald-100 dark:bg-emerald-500/15', text: 'text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-500' },
  pending: { bg: 'bg-amber-100 dark:bg-amber-500/15', text: 'text-amber-700 dark:text-amber-400', dot: 'bg-amber-500' },
  on_hold: { bg: 'bg-orange-100 dark:bg-orange-500/15', text: 'text-orange-700 dark:text-orange-400', dot: 'bg-orange-500' },
  solved: { bg: 'bg-violet-100 dark:bg-violet-500/15', text: 'text-violet-700 dark:text-violet-400', dot: 'bg-violet-500' },
  closed: { bg: 'bg-slate-100 dark:bg-slate-500/15', text: 'text-slate-600 dark:text-slate-400', dot: 'bg-slate-400' },
};

const priorityMap = {
  urgent: { bg: 'bg-red-100 dark:bg-red-500/15', text: 'text-red-700 dark:text-red-400' },
  high: { bg: 'bg-orange-100 dark:bg-orange-500/15', text: 'text-orange-700 dark:text-orange-400' },
  normal: { bg: 'bg-yellow-100 dark:bg-yellow-500/15', text: 'text-yellow-700 dark:text-yellow-400' },
  low: { bg: 'bg-green-100 dark:bg-green-500/15', text: 'text-green-700 dark:text-green-400' },
};

export function StatusBadge({ status }) {
  const s = statusMap[status] || statusMap.open;
  const label = (status || 'open').replace(/_/g, ' ');
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium capitalize ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {label}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  const p = priorityMap[priority] || priorityMap.normal;
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${p.bg} ${p.text}`}>
      {priority || 'normal'}
    </span>
  );
}
