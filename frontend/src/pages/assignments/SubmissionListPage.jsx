import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  HiOutlineClipboardDocumentCheck,
  HiOutlineDocumentArrowDown,
  HiOutlinePencilSquare,
  HiOutlineCheckCircle,
} from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDateTime } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function SubmissionListPage() {
  const [searchParams] = useSearchParams();
  const assignmentIdParam = searchParams.get('assignment_id');
  const { role } = useSelector((state) => state.auth);

  const [submissions, setSubmissions] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Evaluate Modal
  const [evaluateTarget, setEvaluateTarget] = useState(null);
  const [evalForm, setEvalForm] = useState({ marks_obtained: '', feedback_text: '' });
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState('');

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (assignmentIdParam) params.append('assignment_id', assignmentIdParam);

      const res = await api.get(`/api/submissions?${params.toString()}`);
      setSubmissions(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, [page, assignmentIdParam]);

  const handleOpenEvaluate = (sub) => {
    setEvaluateTarget(sub);
    setEvalForm({
      marks_obtained: sub.feedback?.marks_obtained || '',
      feedback_text: sub.feedback?.feedback_text || '',
    });
    setEvalError('');
  };

  const handleEvaluateSubmit = async (e) => {
    e.preventDefault();
    setEvalLoading(true);
    setEvalError('');
    try {
      await api.post(`/api/submissions/${evaluateTarget.id}/evaluate`, {
        marks_obtained: String(evalForm.marks_obtained),
        feedback_text: evalForm.feedback_text || undefined,
      });
      toast.success('Submission evaluated and marks assigned!');
      setEvaluateTarget(null);
      fetchSubmissions();
    } catch (err) {
      setEvalError(getApiErrorMessage(err));
    } finally {
      setEvalLoading(false);
    }
  };

  const handleDownloadFile = (subId) => {
    window.open(`${api.defaults.baseURL}/api/submissions/${subId}/download`, '_blank');
  };

  const columns = [
    {
      header: 'ID',
      key: 'id',
      render: (id) => <span className="font-mono text-xs font-bold text-slate-500">#{id}</span>,
    },
    {
      header: 'Student',
      key: 'student_name',
      render: (name, row) => (
        <div>
          <p className="font-semibold text-slate-900">{name || `Student #${row.student_id}`}</p>
          <p className="text-[11px] text-slate-400">Assignment #{row.assignment_id} &bull; v{row.version}</p>
        </div>
      ),
    },
    {
      header: 'Submitted Answer',
      key: 'submission_text',
      render: (text, row) => (
        <div className="max-w-xs text-xs">
          {text ? <p className="truncate text-slate-700">{text}</p> : null}
          {row.file_name ? (
            <button
              onClick={() => handleDownloadFile(row.id)}
              className="inline-flex items-center gap-1 text-brand-600 hover:text-brand-800 font-medium mt-0.5 cursor-pointer"
            >
              <HiOutlineDocumentArrowDown className="text-sm" />
              <span className="truncate">{row.file_name}</span>
            </button>
          ) : null}
        </div>
      ),
    },
    {
      header: 'Submitted At',
      key: 'submitted_at',
      render: (date, row) => (
        <div className="text-xs">
          <p className="text-slate-800">{formatDateTime(date)}</p>
          {row.is_late && (
            <span className="inline-block text-[10px] font-bold text-rose-600 uppercase">Late Submission</span>
          )}
        </div>
      ),
    },
    {
      header: 'Evaluation Status',
      key: 'status',
      render: (status) => <Badge status={status} />,
    },
    {
      header: 'Marks & Feedback',
      key: 'feedback',
      render: (fb) =>
        fb ? (
          <div className="text-xs">
            <span className="font-bold text-emerald-700">{fb.marks_obtained} Marks</span>
            {fb.feedback_text && <p className="text-slate-500 italic mt-0.5 truncate">{fb.feedback_text}</p>}
          </div>
        ) : (
          <span className="text-xs text-slate-400">Pending Evaluation</span>
        ),
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) =>
        role === ROLES.ADMIN || role === ROLES.INSTRUCTOR ? (
          <Button
            size="sm"
            variant="secondary"
            icon={HiOutlinePencilSquare}
            onClick={() => handleOpenEvaluate(row)}
          >
            Grade
          </Button>
        ) : null,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Submission Evaluation Queue</h1>
          <p className="text-xs text-slate-500 mt-0.5">Grade student project submissions, assign marks, and provide feedback</p>
        </div>
        <Link to="/assignments">
          <Button variant="secondary">View All Assignments</Button>
        </Link>
      </div>

      <DataTable
        columns={columns}
        data={submissions}
        isLoading={loading}
        emptyMessage="No submissions found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Grade / Evaluation Modal */}
      <Modal
        isOpen={!!evaluateTarget}
        onClose={() => setEvaluateTarget(null)}
        title="Grade Student Submission"
        subtitle={`Student: ${evaluateTarget?.student_name} (Assignment #${evaluateTarget?.assignment_id})`}
      >
        <ErrorAlert message={evalError} onClose={() => setEvalError('')} />
        {evaluateTarget && (
          <div className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1">
              <span className="font-bold text-slate-700">Student's Submission Content:</span>
              <p className="text-slate-600 whitespace-pre-line">{evaluateTarget.submission_text || 'No text provided.'}</p>
              {evaluateTarget.file_name && (
                <div className="pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    icon={HiOutlineDocumentArrowDown}
                    onClick={() => handleDownloadFile(evaluateTarget.id)}
                  >
                    Download {evaluateTarget.file_name}
                  </Button>
                </div>
              )}
            </div>

            <form onSubmit={handleEvaluateSubmit} className="space-y-4">
              <Input
                label="Marks Awarded *"
                type="number"
                step="0.5"
                min="0"
                value={evalForm.marks_obtained}
                onChange={(e) => setEvalForm({ ...evalForm, marks_obtained: e.target.value })}
                required
              />

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Instructor Feedback & Rubric Notes
                </label>
                <textarea
                  rows={3}
                  value={evalForm.feedback_text}
                  onChange={(e) => setEvalForm({ ...evalForm, feedback_text: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Constructive feedback for the learner..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <Button variant="secondary" onClick={() => setEvaluateTarget(null)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" isLoading={evalLoading}>
                  Save Evaluation
                </Button>
              </div>
            </form>
          </div>
        )}
      </Modal>
    </div>
  );
}
