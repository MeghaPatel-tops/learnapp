export const ROLES = {
  ADMIN: 'admin',
  INSTRUCTOR: 'instructor',
  STUDENT: 'student',
};

export const COURSE_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  ARCHIVED: 'archived',
};

export const BATCH_STATUS = {
  UPCOMING: 'upcoming',
  ACTIVE: 'active',
  CLOSED: 'closed',
  ARCHIVED: 'archived',
};

export const ENROLLMENT_STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  DROPPED: 'dropped',
};

export const ATTENDANCE_STATUS = {
  PRESENT: 'present',
  ABSENT: 'absent',
  CANCELLED: 'cancelled',
  HOLIDAY: 'holiday',
  APPROVED_LEAVE: 'approved_leave',
};

export const PAYMENT_METHODS = [
  { value: 'cash', label: 'Cash' },
  { value: 'card', label: 'Credit/Debit Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'upi', label: 'UPI / QR' },
  { value: 'online', label: 'Online Payment Gateway' },
  { value: 'other', label: 'Other' },
];

export const PAYMENT_STATUS = {
  PAID: 'paid',
  PARTIALLY_PAID: 'partially_paid',
  PENDING: 'pending',
  REFUNDED: 'refunded',
  FAILED: 'failed',
};
