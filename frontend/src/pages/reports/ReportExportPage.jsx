import React, { useState, useEffect } from 'react';
import {
  HiOutlineChartBar,
  HiOutlineDocumentArrowDown,
  HiOutlineTableCells,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Select from '../../components/common/Select';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';

export default function ReportExportPage() {
  const [selectedReport, setSelectedReport] = useState('students');
  const [selectedFormat, setSelectedFormat] = useState('pdf');
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [courses, setCourses] = useState([]);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await api.get('/api/courses?page=1&page_size=50');
        setCourses(res.data.items || []);
      } catch {
        // silent
      }
    };
    fetchCourses();
  }, []);

  const reportTypes = [
    {
      id: 'students',
      title: 'Students Master Directory',
      description: 'Comprehensive roster of student profiles, registration codes, guardian contact info, and active statuses.',
    },
    {
      id: 'enrollments',
      title: 'Course Admissions & Enrollments',
      description: 'Complete breakdown of all student-to-course enrollments, dates of enrollment, and completion milestones.',
    },
    {
      id: 'payments',
      title: 'Fee Payments & Outstanding Balances',
      description: 'Financial ledger report showing tuition fees, amounts received, receipt numbers, and balances.',
    },
    {
      id: 'attendance',
      title: 'Attendance Sessions Register',
      description: 'Session-by-session attendance logs with timestamps and status distribution.',
    },
    {
      id: 'course-progress',
      title: 'Academic Completion Progress',
      description: 'Progress evaluation percentages, lecture completion counts, assignment grades, and quiz benchmarks.',
    },
  ];

  const handleExport = async (formatOverride) => {
    const format = formatOverride || selectedFormat;
    setIsExporting(true);

    try {
      const params = new URLSearchParams({ format });
      if (selectedCourseId) params.append('course_id', selectedCourseId);

      const downloadUrl = `${api.defaults.baseURL}/api/reports/${selectedReport}?${params.toString()}`;
      
      // Request as blob through axios to ensure authorization token is passed
      const res = await api.get(`/api/reports/${selectedReport}?${params.toString()}`, {
        responseType: 'blob',
      });

      // Trigger browser download
      const blob = new Blob([res.data], { type: res.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedReport}-report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`${selectedReport} report generated (${format.toUpperCase()})!`);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Reports & Analytics Export</h1>
        <p className="text-xs text-slate-500 mt-0.5">Generate institutional reports in printable PDF, Excel (XLSX), or CSV formats</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Report Types Selector */}
        <div className="md:col-span-2 space-y-3">
          {reportTypes.map((item) => {
            const isSelected = selectedReport === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setSelectedReport(item.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-brand-500 bg-brand-50/20 ring-1 ring-brand-500 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 text-sm">{item.title}</h3>
                  <span className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                    isSelected ? 'border-brand-600 bg-brand-600' : 'border-slate-300'
                  }`}>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{item.description}</p>
              </div>
            );
          })}
        </div>

        {/* Right: Export Controls Panel */}
        <div className="md:col-span-1">
          <Card title="Export Settings" className="sticky top-24">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Filter by Course (Optional)
                </label>
                <select
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 text-xs py-2 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">All Courses</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.course_code} - {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Preferred Format
                </label>
                <Select
                  value={selectedFormat}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  options={[
                    { value: 'pdf', label: 'PDF Document (.pdf)' },
                    { value: 'xlsx', label: 'Excel Spreadsheet (.xlsx)' },
                    { value: 'csv', label: 'Comma-Separated Values (.csv)' },
                  ]}
                />
              </div>

              <div className="pt-2 space-y-2">
                <Button
                  variant="primary"
                  className="w-full"
                  icon={HiOutlineDocumentArrowDown}
                  onClick={() => handleExport(selectedFormat)}
                  isLoading={isExporting}
                >
                  Download {selectedFormat.toUpperCase()} Report
                </Button>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleExport('xlsx')}
                    disabled={isExporting}
                  >
                    Quick Excel
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleExport('csv')}
                    disabled={isExporting}
                  >
                    Quick CSV
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
