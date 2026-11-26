import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  HiOutlineUserGroup,
  HiOutlineCalendar,
  HiOutlineClock,
  HiOutlineUserPlus,
  HiOutlineTrash,
  HiOutlineArrowLeft,
  HiOutlineClipboardDocumentList,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function BatchDetailPage() {
  const { id } = useParams();
  const { role } = useSelector((state) => state.auth);

  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Add Student Modal
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [addStudentLoading, setAddStudentLoading] = useState(false);
  const [addStudentError, setAddStudentError] = useState('');

  const fetchBatchDetail = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/batches/${id}`);
      setBatch(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatchDetail();
  }, [id]);

  const handleOpenAddStudent = async () => {
    try {
      const res = await api.get('/api/students?page=1&page_size=100');
      setStudents(res.data.items || []);
      setIsAddStudentOpen(true);
      setAddStudentError('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    if (!selectedStudentId) return;

    setAddStudentLoading(true);
    setAddStudentError('');
    try {
      await api.post(`/api/batches/${id}/students`, {
        student_id: parseInt(selectedStudentId),
      });
      toast.success('Student added to batch roster!');
      setIsAddStudentOpen(false);
      setSelectedStudentId('');
      fetchBatchDetail();
    } catch (err) {
      setAddStudentError(getApiErrorMessage(err));
    } finally {
      setAddStudentLoading(false);
    }
  };

  const handleRemoveStudent = async (studentId) => {
    if (!window.confirm('Remove student from this batch roster?')) return;
    try {
      await api.delete(`/api/batches/${id}/students/${studentId}`);
      toast.success('Student removed from batch roster');
      fetchBatchDetail();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleBatchStatus = async (action) => {
    try {
      await api.post(`/api/batches/${id}/${action}`);
      toast.success(`Batch successfully ${action}d!`);
      fetchBatchDetail();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  if (loading) return <LoadingSpinner size="lg" message="Loading batch details and roster..." />;
  if (error || !batch) return <ErrorAlert message={error || 'Batch not found'} />;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/batches"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <HiOutlineArrowLeft className="text-lg" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-500 uppercase">{batch.batch_code}</span>
              <Badge status={batch.status} />
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-0.5">{batch.name}</h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/attendance?batch_id=${id}`}>
            <Button size="sm" variant="secondary" icon={HiOutlineClipboardDocumentList}>
              Attendance Sheet
            </Button>
          </Link>
          {role === ROLES.ADMIN && (
            <>
              {batch.status === 'upcoming' || batch.status === 'active' ? (
                <Button size="sm" variant="ghost" onClick={() => handleBatchStatus('close')}>
                  Close Admissions
                </Button>
              ) : null}
              {batch.status !== 'archived' && (
                <Button size="sm" variant="ghost" onClick={() => handleBatchStatus('archive')}>
                  Archive Batch
                </Button>
              )}
              <Button size="sm" variant="primary" icon={HiOutlineUserPlus} onClick={handleOpenAddStudent}>
                Add Student to Roster
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Meta Specs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Target Curriculum</span>
          <p className="text-sm font-bold text-slate-900 mt-0.5">{batch.course_name || `Course #${batch.course_id}`}</p>
        </Card>
        <Card className="p-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Lead Faculty</span>
          <p className="text-sm font-bold text-slate-900 mt-0.5">{batch.instructor_name || `Instructor #${batch.instructor_id}`}</p>
        </Card>
        <Card className="p-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Class Timings</span>
          <p className="text-sm font-bold text-slate-900 mt-0.5">{batch.class_days}</p>
          <p className="text-xs text-slate-500">{batch.class_timing}</p>
        </Card>
        <Card className="p-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Duration & Seats</span>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            {formatDate(batch.start_date)} - {formatDate(batch.end_date)}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {batch.enrolled_count || 0} / {batch.capacity} seats taken
          </p>
        </Card>
      </div>

      {/* Roster Table */}
      <Card
        title={`Student Roster (${batch.roster?.length || 0})`}
        subtitle="Students assigned to this active batch cohort"
        action={
          role === ROLES.ADMIN && (
            <Button size="sm" variant="outline" icon={HiOutlineUserPlus} onClick={handleOpenAddStudent}>
              Add Student
            </Button>
          )
        }
      >
        {(!batch.roster || batch.roster.length === 0) ? (
          <div className="p-8 text-center text-xs text-slate-400 italic">
            No students currently enrolled in this batch roster.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
              <thead className="bg-slate-50/75">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Student Code</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Student Name</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Email</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Status</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Joined Date</th>
                  {role === ROLES.ADMIN && (
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 text-right">Actions</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {batch.roster.map((s) => (
                  <tr key={s.student_id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3.5 font-mono text-xs font-bold text-slate-700">{s.student_code}</td>
                    <td className="px-4 py-3.5 font-semibold text-slate-900">{s.full_name}</td>
                    <td className="px-4 py-3.5 text-xs text-slate-500">{s.email}</td>
                    <td className="px-4 py-3.5">
                      <Badge status={s.status} />
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-500">{formatDate(s.joined_at)}</td>
                    {role === ROLES.ADMIN && (
                      <td className="px-4 py-3.5 text-right">
                        <button
                          onClick={() => handleRemoveStudent(s.student_id)}
                          className="text-xs text-rose-500 hover:text-rose-700 font-semibold cursor-pointer"
                        >
                          Remove
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add Student to Roster Modal */}
      <Modal
        isOpen={isAddStudentOpen}
        onClose={() => setIsAddStudentOpen(false)}
        title="Add Student to Batch Roster"
        subtitle={`Enrolling into ${batch.name} (Validates course enrollment & capacity)`}
      >
        <ErrorAlert message={addStudentError} onClose={() => setAddStudentError('')} />
        <form onSubmit={handleAddStudent} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Enrolled Student *
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose a student...</option>
              {students.map((st) => (
                <option key={st.user_id} value={st.user_id}>
                  {st.student_code} - {st.full_name} ({st.email})
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsAddStudentOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={addStudentLoading}>
              Add to Batch
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
