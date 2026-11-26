import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useSearchParams, Link } from 'react-router-dom';
import {
  HiOutlineDocumentText,
  HiOutlinePlus,
  HiOutlineClock,
  HiOutlineArrowUpTray,
  HiOutlineEye,
  HiOutlineTrash,
} from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDateTime, formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function AssignmentListPage() {
  const [searchParams] = useSearchParams();
  const courseIdParam = searchParams.get('course_id');
  const { role } = useSelector((state) => state.auth);

  const [assignments, setAssignments] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Create Assignment Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [courses, setCourses] = useState([]);
  const [createForm, setCreateForm] = useState({
    course_id: courseIdParam || '',
    title: '',
    instructions: '',
    max_marks: '100.00',
    passing_marks: '50.00',
    due_date: '',
    allow_late: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Submit Modal (Student)
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [submissionText, setSubmissionText] = useState('');
  const [submissionFile, setSubmissionFile] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const fetchAssignments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (courseIdParam) params.append('course_id', courseIdParam);

      const res = await api.get(`/api/assignments?${params.toString()}`);
      setAssignments(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, [page, courseIdParam]);

  const handleOpenCreate = async () => {
    try {
      const res = await api.get('/api/courses?page=1&page_size=50');
      setCourses(res.data.items || []);
      setIsCreateOpen(true);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/assignments', {
        ...createForm,
        course_id: parseInt(createForm.course_id),
        max_marks: String(createForm.max_marks),
        passing_marks: String(createForm.passing_marks),
        due_date: new Date(createForm.due_date).toISOString(),
      });
      toast.success('Assignment created!');
      setIsCreateOpen(false);
      fetchAssignments();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleSubmitAssignment = async (e) => {
    e.preventDefault();
    if (!submissionText && !submissionFile) {
      setSubmitError('Please provide text or an attachment file for your submission.');
      return;
    }
    setSubmitLoading(true);
    setSubmitError('');

    const formData = new FormData();
    formData.append('assignment_id', selectedAssignment.id);
    if (submissionText) formData.append('submission_text', submissionText);
    if (submissionFile) formData.append('file', submissionFile);

    try {
      await api.post('/api/submissions', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Assignment submitted successfully!');
      setSelectedAssignment(null);
      setSubmissionText('');
      setSubmissionFile(null);
    } catch (err) {
      setSubmitError(getApiErrorMessage(err));
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDeleteAssignment = async (id) => {
    if (!window.confirm('Delete this assignment?')) return;
    try {
      await api.delete(`/api/assignments/${id}`);
      toast.success('Assignment deleted');
      fetchAssignments();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const columns = [
    {
      header: 'Title & Instructions',
      key: 'title',
      render: (_, row) => (
        <div>
          <p className="font-bold text-slate-900 leading-tight">{row.title}</p>
          <p className="text-xs text-slate-500 line-clamp-1 mt-0.5">{row.instructions}</p>
        </div>
      ),
    },
    {
      header: 'Course',
      key: 'course_id',
      render: (cId) => <span className="font-mono text-xs text-slate-600">Course #{cId}</span>,
    },
    {
      header: 'Marks',
      key: 'max_marks',
      render: (_, row) => (
        <span className="text-xs font-semibold text-slate-800">
          Pass: {row.passing_marks} / Max: {row.max_marks}
        </span>
      ),
    },
    {
      header: 'Deadline',
      key: 'due_date',
      render: (date) => (
        <div className="text-xs">
          <p className="font-semibold text-slate-800">{formatDateTime(date)}</p>
        </div>
      ),
    },
    {
      header: 'Late Allowed',
      key: 'allow_late',
      render: (late) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            late ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
          }`}
        >
          {late ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
          {role === ROLES.STUDENT && (
            <Button
              size="sm"
              variant="primary"
              icon={HiOutlineArrowUpTray}
              onClick={() => {
                setSelectedAssignment(row);
                setSubmitError('');
              }}
            >
              Submit Solution
            </Button>
          )}

          {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
            <>
              <Link to={`/submissions?assignment_id=${row.id}`}>
                <Button size="sm" variant="secondary" icon={HiOutlineEye}>
                  Submissions
                </Button>
              </Link>
              <button
                onClick={() => handleDeleteAssignment(row.id)}
                className="p-1.5 text-slate-400 hover:text-rose-600 rounded cursor-pointer"
                title="Delete Assignment"
              >
                <HiOutlineTrash className="text-base" />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Assignments & Projects</h1>
          <p className="text-xs text-slate-500 mt-0.5">Submit homework, review evaluations, and track deadlines</p>
        </div>
        {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenCreate}>
            Create Assignment
          </Button>
        )}
      </div>

      <DataTable
        columns={columns}
        data={assignments}
        isLoading={loading}
        emptyMessage="No assignments found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Student Submit Modal */}
      <Modal
        isOpen={!!selectedAssignment}
        onClose={() => setSelectedAssignment(null)}
        title="Submit Assignment"
        subtitle={`Submitting for: ${selectedAssignment?.title}`}
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={submitError} onClose={() => setSubmitError('')} />
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs mb-4">
          <p className="font-semibold text-slate-800">Instructions:</p>
          <p className="text-slate-600 mt-1 whitespace-pre-line">{selectedAssignment?.instructions}</p>
          <div className="mt-2 pt-2 border-t border-slate-200/60 flex justify-between text-slate-500">
            <span>Due Date: {formatDateTime(selectedAssignment?.due_date)}</span>
            <span>Max Marks: {selectedAssignment?.max_marks}</span>
          </div>
        </div>

        <form onSubmit={handleSubmitAssignment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Solution Notes / Written Answer
            </label>
            <textarea
              rows={4}
              value={submissionText}
              onChange={(e) => setSubmissionText(e.target.value)}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Paste code links, git repository URLs, or written explanations..."
            />
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center">
            <input
              type="file"
              onChange={(e) => setSubmissionFile(e.target.files[0])}
              className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
            <p className="text-[11px] text-slate-400 mt-2">Attach archive, PDF, or document (Max 25MB)</p>
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setSelectedAssignment(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitLoading}>
              Confirm Submission
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Assignment Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Assignment"
        subtitle="Specify guidelines, marks distribution, and deadlines"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreateAssignment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Course *
            </label>
            <select
              value={createForm.course_id}
              onChange={(e) => setCreateForm({ ...createForm, course_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Select course...</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.course_code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <Input
            label="Assignment Title"
            value={createForm.title}
            onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
            placeholder="e.g. Build an E-Commerce API with FastAPI"
            required
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Detailed Instructions *
            </label>
            <textarea
              rows={3}
              value={createForm.instructions}
              onChange={(e) => setCreateForm({ ...createForm, instructions: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Requirements, acceptance criteria, submission format..."
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Maximum Marks"
              type="number"
              step="1"
              value={createForm.max_marks}
              onChange={(e) => setCreateForm({ ...createForm, max_marks: e.target.value })}
              required
            />
            <Input
              label="Passing Marks"
              type="number"
              step="1"
              value={createForm.passing_marks}
              onChange={(e) => setCreateForm({ ...createForm, passing_marks: e.target.value })}
              required
            />
          </div>

          <Input
            label="Submission Due Date & Time"
            type="datetime-local"
            value={createForm.due_date}
            onChange={(e) => setCreateForm({ ...createForm, due_date: e.target.value })}
            required
          />

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Publish Assignment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
