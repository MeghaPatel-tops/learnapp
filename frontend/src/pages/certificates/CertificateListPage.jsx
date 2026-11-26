import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  HiOutlineCheckBadge,
  HiOutlineDocumentArrowDown,
  HiOutlinePlus,
  HiOutlineEye,
} from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Modal from '../../components/common/Modal';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function CertificateListPage() {
  const { role, user } = useSelector((state) => state.auth);

  const [certificates, setCertificates] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Generate Modal
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [genForm, setGenForm] = useState({ student_id: '', course_id: '' });
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState('');

  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/certificates?page=${page}&page_size=15`);
      setCertificates(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCertificates();
  }, [page]);

  const handleOpenGenerate = async () => {
    try {
      const [sRes, cRes] = await Promise.all([
        api.get('/api/students?page=1&page_size=100'),
        api.get('/api/courses?page=1&page_size=100'),
      ]);
      setStudents(sRes.data.items || []);
      setCourses(cRes.data.items || []);
      if (role === ROLES.STUDENT && user?.id) {
        setGenForm({ student_id: String(user.id), course_id: '' });
      }
      setIsGenerateOpen(true);
      setGenError('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleGenerateCertificate = async (e) => {
    e.preventDefault();
    if (!genForm.student_id || !genForm.course_id) return;

    setGenLoading(true);
    setGenError('');
    try {
      const res = await api.post('/api/certificates/generate', {
        student_id: parseInt(genForm.student_id),
        course_id: parseInt(genForm.course_id),
      });
      toast.success(`Certificate ${res.data.certificate_number} issued!`);
      setIsGenerateOpen(false);
      fetchCertificates();
    } catch (err) {
      setGenError(getApiErrorMessage(err));
    } finally {
      setGenLoading(false);
    }
  };

  const handleDownloadPDF = (certId) => {
    window.open(`${api.defaults.baseURL}/api/certificates/${certId}/download`, '_blank');
  };

  const columns = [
    {
      header: 'Certificate #',
      key: 'certificate_number',
      render: (num) => (
        <span className="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md">
          {num}
        </span>
      ),
    },
    {
      header: 'Student',
      key: 'student_name',
      render: (name, row) => (
        <div>
          <p className="font-semibold text-slate-900 text-xs">{name || `Student #${row.student_id}`}</p>
          <p className="text-[10px] text-slate-400 font-mono">{row.student_code}</p>
        </div>
      ),
    },
    {
      header: 'Program / Course',
      key: 'course_name',
      render: (name, row) => (
        <div>
          <p className="font-semibold text-slate-900 text-xs">{name || `Course #${row.course_id}`}</p>
          <p className="text-[10px] text-slate-400 font-mono">{row.course_code}</p>
        </div>
      ),
    },
    {
      header: 'Verification Code',
      key: 'verification_code',
      render: (code) => <span className="font-mono text-xs text-slate-600">{code}</span>,
    },
    {
      header: 'Issue Date',
      key: 'issue_date',
      render: (date) => <span className="text-xs text-slate-500">{formatDate(date)}</span>,
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
          <Link to={`/verify-certificate/${row.verification_code}`} target="_blank">
            <Button size="sm" variant="ghost" icon={HiOutlineEye}>
              Verify
            </Button>
          </Link>
          <Button
            size="sm"
            variant="secondary"
            icon={HiOutlineDocumentArrowDown}
            onClick={() => handleDownloadPDF(row.id)}
          >
            Download PDF
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Official Certificates</h1>
          <p className="text-xs text-slate-500 mt-0.5">Academic credentials, verifiable badges, and print-ready PDF certificates</p>
        </div>
        <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenGenerate}>
          Issue Certificate
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={certificates}
        isLoading={loading}
        emptyMessage="No certificates issued yet"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Generate Certificate Modal */}
      <Modal
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        title="Issue Course Certificate"
        subtitle="Verifies 100% lectures, all assignments and quizzes completed"
      >
        <ErrorAlert message={genError} onClose={() => setGenError('')} />
        <form onSubmit={handleGenerateCertificate} className="space-y-4">
          {role === ROLES.ADMIN ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Select Student *
              </label>
              <select
                value={genForm.student_id}
                onChange={(e) => setGenForm({ ...genForm, student_id: e.target.value })}
                className="w-full rounded-lg border border-slate-300 text-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
              >
                <option value="">Select a student...</option>
                {students.map((st) => (
                  <option key={st.user_id} value={st.user_id}>
                    {st.student_code} - {st.full_name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-600">
              Generating certificate for authenticated student: <strong>{user?.full_name}</strong>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Completed Course *
            </label>
            <select
              value={genForm.course_id}
              onChange={(e) => setGenForm({ ...genForm, course_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose course...</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.course_code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsGenerateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={genLoading}>
              Verify & Issue Certificate
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
