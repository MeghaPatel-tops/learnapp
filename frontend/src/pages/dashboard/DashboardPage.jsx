import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  HiOutlineAcademicCap,
  HiOutlineUserGroup,
  HiOutlineIdentification,
  HiOutlineCreditCard,
  HiOutlineClipboardDocumentCheck,
  HiOutlineClock,
  HiOutlineCheckCircle,
  HiOutlineArrowTrendingUp,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function DashboardPage() {
  const { user, role } = useSelector((state) => state.auth);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await api.get('/api/dashboard');
        setData(res.data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [role]);

  if (loading) {
    return <LoadingSpinner size="lg" message="Loading dashboard metrics..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  // Metric Card Helper
  const Metric = ({ title, value, icon: Icon, color = 'brand', subtext }) => {
    const colorStyles = {
      brand: 'bg-brand-50 text-brand-600',
      emerald: 'bg-emerald-50 text-emerald-600',
      amber: 'bg-amber-50 text-amber-600',
      sky: 'bg-sky-50 text-sky-600',
      rose: 'bg-rose-50 text-rose-600',
    };

    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</span>
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl ${colorStyles[color] || colorStyles.brand}`}>
            <Icon />
          </div>
        </div>
        <p className="mt-2 text-2xl font-black text-slate-900 tracking-tight">{value}</p>
        {subtext && <p className="mt-1 text-xs text-slate-400">{subtext}</p>}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-900 via-brand-800 to-indigo-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg shadow-brand-950/10">
        <div className="max-w-2xl">
          <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/10 text-white backdrop-blur-xs mb-3">
            {role} Portal
          </span>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-brand-100">
            {role === ROLES.ADMIN && 'Here is your institute overview, financials, enrollment metrics, and operational performance.'}
            {role === ROLES.INSTRUCTOR && 'Review your assigned classes, scheduled lectures, and student submission grading backlog.'}
            {role === ROLES.STUDENT && 'Track your course completions, upcoming assignment deadlines, and attendance.'}
          </p>
        </div>
      </div>

      {/* ADMIN METRICS */}
      {role === ROLES.ADMIN && data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Metric title="Total Students" value={data.total_students ?? 0} icon={HiOutlineIdentification} color="brand" subtext="Enrolled learners" />
            <Metric title="Total Instructors" value={data.total_instructors ?? 0} icon={HiOutlineUserGroup} color="sky" subtext="Teaching staff" />
            <Metric title="Active Courses" value={data.active_courses ?? 0} icon={HiOutlineAcademicCap} color="emerald" subtext={`${data.total_courses || 0} total curriculum offerings`} />
            <Metric title="Active Batches" value={data.active_batches ?? 0} icon={HiOutlineClock} color="amber" subtext="Current ongoing cohorts" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Metric title="Total Revenue Collected" value={formatCurrency(data.total_revenue || 0)} icon={HiOutlineArrowTrendingUp} color="emerald" subtext="Settled fee payments" />
            <Metric title="Pending Receivables" value={formatCurrency(data.pending_fees || 0)} icon={HiOutlineCreditCard} color="rose" subtext="Outstanding student balances" />
          </div>

          {/* Recent enrollments */}
          {data.recent_enrollments && data.recent_enrollments.length > 0 && (
            <Card title="Recent Course Enrollments" subtitle="Latest student course admissions">
              <div className="divide-y divide-slate-100">
                {data.recent_enrollments.map((enr) => (
                  <div key={enr.id} className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{enr.student_name || `Student #${enr.student_id}`}</p>
                      <p className="text-xs text-slate-500">{enr.course_name || `Course #${enr.course_id}`}</p>
                    </div>
                    <div className="text-right">
                      <Badge status={enr.status} />
                      <p className="text-[10px] text-slate-400 mt-0.5">{formatDate(enr.enrolled_at || enr.created_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* INSTRUCTOR METRICS */}
      {role === ROLES.INSTRUCTOR && data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Metric title="Assigned Courses" value={data.assigned_courses_count ?? 0} icon={HiOutlineAcademicCap} color="brand" />
            <Metric title="Active Batches" value={data.assigned_batches_count ?? 0} icon={HiOutlineUserGroup} color="sky" />
            <Metric title="Submissions to Grade" value={data.pending_submissions_count ?? 0} icon={HiOutlineClipboardDocumentCheck} color={data.pending_submissions_count > 0 ? 'amber' : 'emerald'} subtext="Awaiting instructor rubric evaluation" />
          </div>

          {data.recent_submissions && data.recent_submissions.length > 0 && (
            <Card title="Recent Submissions" subtitle="Latest student submissions requiring grading" action={<Link to="/submissions" className="text-xs font-semibold text-brand-600 hover:text-brand-700">View All Submissions &rarr;</Link>}>
              <div className="divide-y divide-slate-100">
                {data.recent_submissions.map((sub) => (
                  <div key={sub.id} className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{sub.student_name}</p>
                      <p className="text-xs text-slate-500">Assignment #{sub.assignment_id} &bull; v{sub.version}</p>
                    </div>
                    <div className="text-right">
                      <Badge status={sub.status} />
                      <p className="text-[10px] text-slate-400 mt-0.5">{formatDate(sub.submitted_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* STUDENT METRICS */}
      {role === ROLES.STUDENT && data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Metric title="Enrolled Courses" value={data.enrolled_courses_count ?? 0} icon={HiOutlineAcademicCap} color="brand" subtext="Current academic programs" />
            <Metric title="Attendance Record" value={`${data.attendance_percentage ?? 0}%`} icon={HiOutlineClock} color={(data.attendance_percentage || 0) >= 75 ? 'emerald' : 'rose'} subtext="Overall attendance percentage" />
            <Metric title="Pending Assignments" value={data.pending_assignments_count ?? 0} icon={HiOutlineClipboardDocumentCheck} color="amber" subtext="Upcoming assessment deadlines" />
          </div>

          {/* Enrolled course cards with progress */}
          {data.enrolled_courses && data.enrolled_courses.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">My Ongoing Courses</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.enrolled_courses.map((c) => (
                  <Card key={c.course_id} className="p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">{c.category || 'Curriculum'}</span>
                        <h4 className="text-base font-bold text-slate-900 mt-0.5">{c.name}</h4>
                      </div>
                      <Badge status={c.status} />
                    </div>
                    <div className="mt-4">
                      <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                        <span>Course Completion</span>
                        <span>{Math.round(c.progress_pct || 0)}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-brand-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, c.progress_pct || 0)}%` }}
                        />
                      </div>
                    </div>
                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-400">Duration: {c.duration_hours || 0} Hours</span>
                      <Link to={`/courses/${c.course_id}`} className="font-semibold text-brand-600 hover:text-brand-700">
                        Continue Learning &rarr;
                      </Link>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
