export const formatDate = (dateString, options = {}) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...options,
    });
  } catch {
    return '-';
  }
};

export const formatDateTime = (dateString) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '-';
  }
};

export const formatCurrency = (amount) => {
  const num = parseFloat(amount || 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(num);
};

export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

export const getStatusBadgeClass = (status) => {
  const s = String(status).toLowerCase();
  switch (s) {
    case 'active':
    case 'published':
    case 'present':
    case 'paid':
    case 'completed':
    case 'evaluated':
      return 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20';
    case 'upcoming':
    case 'partially_paid':
    case 'under_review':
    case 'submitted':
    case 'draft':
      return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20';
    case 'archived':
    case 'closed':
    case 'cancelled':
    case 'holiday':
    case 'approved_leave':
      return 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-600/10';
    case 'dropped':
    case 'absent':
    case 'refunded':
    case 'failed':
      return 'bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-600/20';
    default:
      return 'bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-600/20';
  }
};
