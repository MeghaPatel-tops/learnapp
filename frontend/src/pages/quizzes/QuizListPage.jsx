import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  HiOutlineCheckBadge,
  HiOutlinePlus,
  HiOutlineClock,
  HiOutlinePlay,
  HiOutlineQuestionMarkCircle,
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

export default function QuizListPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseIdParam = searchParams.get('course_id');
  const { role } = useSelector((state) => state.auth);

  const [quizzes, setQuizzes] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Create Quiz Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [courses, setCourses] = useState([]);
  const [createForm, setCreateForm] = useState({
    course_id: courseIdParam || '',
    title: '',
    description: '',
    total_marks: '10.00',
    passing_marks: '6.00',
    duration_minutes: 30,
    available_from: '',
    available_until: '',
    allow_retakes: false,
    max_attempts: 1,
    show_correct_answers: true,
    is_published: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Add Question Modal
  const [questionTargetQuiz, setQuestionTargetQuiz] = useState(null);
  const [questionText, setQuestionText] = useState('');
  const [questionMarks, setQuestionMarks] = useState('2.00');
  const [options, setOptions] = useState([
    { option_text: '', is_correct: true, sequence_order: 1 },
    { option_text: '', is_correct: false, sequence_order: 2 },
    { option_text: '', is_correct: false, sequence_order: 3 },
    { option_text: '', is_correct: false, sequence_order: 4 },
  ]);
  const [questionLoading, setQuestionLoading] = useState(false);
  const [questionError, setQuestionError] = useState('');

  const fetchQuizzes = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (courseIdParam) params.append('course_id', courseIdParam);

      const res = await api.get(`/api/quizzes?${params.toString()}`);
      setQuizzes(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuizzes();
  }, [page, courseIdParam]);

  const handleOpenCreate = async () => {
    try {
      const res = await api.get('/api/courses?page=1&page_size=50');
      setCourses(res.data.items || []);
      // Set default dates
      const now = new Date();
      const nextMonth = new Date();
      nextMonth.setMonth(nextMonth.getMonth() + 1);
      setCreateForm((prev) => ({
        ...prev,
        available_from: now.toISOString().slice(0, 16),
        available_until: nextMonth.toISOString().slice(0, 16),
      }));
      setIsCreateOpen(true);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateQuiz = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/quizzes', {
        ...createForm,
        course_id: parseInt(createForm.course_id),
        total_marks: String(createForm.total_marks),
        passing_marks: String(createForm.passing_marks),
        duration_minutes: parseInt(createForm.duration_minutes) || 30,
        max_attempts: parseInt(createForm.max_attempts) || 1,
        available_from: new Date(createForm.available_from).toISOString(),
        available_until: new Date(createForm.available_until).toISOString(),
      });
      toast.success('Quiz created successfully!');
      setIsCreateOpen(false);
      fetchQuizzes();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    const correctCount = options.filter((o) => o.is_correct).length;
    if (correctCount !== 1) {
      setQuestionError('Exactly one option must be marked as correct.');
      return;
    }
    setQuestionLoading(true);
    setQuestionError('');
    try {
      await api.post(`/api/quizzes/${questionTargetQuiz.id}/questions`, {
        question_text: questionText,
        marks: String(questionMarks),
        sequence_order: (questionTargetQuiz.question_count || 0) + 1,
        options: options.map((opt, i) => ({
          option_text: opt.option_text,
          is_correct: opt.is_correct,
          sequence_order: i + 1,
        })),
      });
      toast.success('Question added to quiz!');
      setQuestionTargetQuiz(null);
      setQuestionText('');
      fetchQuizzes();
    } catch (err) {
      setQuestionError(getApiErrorMessage(err));
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleStartQuiz = async (quizId) => {
    try {
      const res = await api.post(`/api/quizzes/${quizId}/start`);
      toast.success('Quiz attempt started! Good luck.');
      navigate(`/quizzes/${quizId}/runner/${res.data.id}`);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const columns = [
    {
      header: 'Quiz Title',
      key: 'title',
      render: (_, row) => (
        <div>
          <p className="font-bold text-slate-900 leading-tight">{row.title}</p>
          <p className="text-xs text-slate-500 line-clamp-1">{row.description || 'No description'}</p>
        </div>
      ),
    },
    {
      header: 'Duration',
      key: 'duration_minutes',
      render: (mins) => (
        <span className="inline-flex items-center gap-1 text-xs text-slate-700 font-medium">
          <HiOutlineClock className="text-slate-400" />
          {mins} mins
        </span>
      ),
    },
    {
      header: 'Marks',
      key: 'total_marks',
      render: (_, row) => (
        <span className="text-xs font-semibold text-slate-800">
          Pass: {row.passing_marks} / Total: {row.total_marks}
        </span>
      ),
    },
    {
      header: 'Questions',
      key: 'question_count',
      render: (count) => (
        <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
          {count || 0} MCQs
        </span>
      ),
    },
    {
      header: 'Available Window',
      key: 'available_until',
      render: (_, row) => (
        <div className="text-xs text-slate-500">
          <p>Until: {formatDateTime(row.available_until)}</p>
        </div>
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
              icon={HiOutlinePlay}
              onClick={() => handleStartQuiz(row.id)}
            >
              Start Attempt
            </Button>
          )}

          {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
            <Button
              size="sm"
              variant="secondary"
              icon={HiOutlineQuestionMarkCircle}
              onClick={() => {
                setQuestionTargetQuiz(row);
                setQuestionError('');
              }}
            >
              Add Question
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Quizzes & Assessments</h1>
          <p className="text-xs text-slate-500 mt-0.5">Automated multiple-choice tests, passing criteria, and evaluations</p>
        </div>
        {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenCreate}>
            Create Quiz
          </Button>
        )}
      </div>

      <DataTable
        columns={columns}
        data={quizzes}
        isLoading={loading}
        emptyMessage="No quizzes found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Create Quiz Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create MCQ Quiz"
        subtitle="Configure duration, passing thresholds, and availability window"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreateQuiz} className="space-y-4">
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
            label="Quiz Title"
            value={createForm.title}
            onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
            placeholder="e.g. Midterm Assessment: React Core Concepts"
            required
          />

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Duration (Min)"
              type="number"
              min="1"
              value={createForm.duration_minutes}
              onChange={(e) => setCreateForm({ ...createForm, duration_minutes: e.target.value })}
              required
            />
            <Input
              label="Total Marks"
              type="number"
              value={createForm.total_marks}
              onChange={(e) => setCreateForm({ ...createForm, total_marks: e.target.value })}
              required
            />
            <Input
              label="Passing Marks"
              type="number"
              value={createForm.passing_marks}
              onChange={(e) => setCreateForm({ ...createForm, passing_marks: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Available From"
              type="datetime-local"
              value={createForm.available_from}
              onChange={(e) => setCreateForm({ ...createForm, available_from: e.target.value })}
              required
            />
            <Input
              label="Available Until"
              type="datetime-local"
              value={createForm.available_until}
              onChange={(e) => setCreateForm({ ...createForm, available_until: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Save & Create Quiz
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Question Modal */}
      <Modal
        isOpen={!!questionTargetQuiz}
        onClose={() => setQuestionTargetQuiz(null)}
        title="Add MCQ Question"
        subtitle={`Adding question to: ${questionTargetQuiz?.title}`}
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={questionError} onClose={() => setQuestionError('')} />
        <form onSubmit={handleAddQuestion} className="space-y-4">
          <Input
            label="Question Text *"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            placeholder="e.g. What is the virtual DOM in React?"
            required
          />
          <Input
            label="Question Marks"
            type="number"
            value={questionMarks}
            onChange={(e) => setQuestionMarks(e.target.value)}
            required
          />

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Answer Options (Select the one correct answer) *
            </label>
            {options.map((opt, i) => (
              <div key={i} className="flex items-center gap-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <input
                  type="radio"
                  name="correct_option"
                  checked={opt.is_correct}
                  onChange={() => {
                    const next = options.map((o, idx) => ({ ...o, is_correct: idx === i }));
                    setOptions(next);
                  }}
                  className="w-4 h-4 text-brand-600 focus:ring-brand-500 cursor-pointer"
                />
                <input
                  type="text"
                  value={opt.option_text}
                  onChange={(e) => {
                    const next = [...options];
                    next[i].option_text = e.target.value;
                    setOptions(next);
                  }}
                  placeholder={`Option ${i + 1}`}
                  className="flex-1 bg-white border border-slate-200 text-xs rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  required
                />
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setQuestionTargetQuiz(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={questionLoading}>
              Add Question
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
