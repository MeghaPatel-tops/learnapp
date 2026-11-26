import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import {
  HiOutlineMegaphone,
  HiOutlinePlus,
  HiOutlineTrash,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Select from '../../components/common/Select';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDateTime } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function AnnouncementListPage() {
  const { role } = useSelector((state) => state.auth);

  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [courses, setCourses] = useState([]);
  const [createForm, setCreateForm] = useState({
    title: '',
    content: '',
    target_role: 'all',
    course_id: '',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchAnnouncements = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/announcements?page=1&page_size=50');
      setAnnouncements(res.data.items || []);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const handleOpenCreate = async () => {
    try {
      const res = await api.get('/api/courses?page=1&page_size=50');
      setCourses(res.data.items || []);
      setIsCreateOpen(true);
      setCreateError('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateAnnouncement = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/announcements', {
        ...createForm,
        course_id: createForm.course_id ? parseInt(createForm.course_id) : undefined,
      });
      toast.success('Announcement broadcast successfully!');
      setIsCreateOpen(false);
      setCreateForm({ title: '', content: '', target_role: 'all', course_id: '' });
      fetchAnnouncements();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this broadcast announcement?')) return;
    try {
      await api.delete(`/api/announcements/${id}`);
      toast.success('Announcement deleted');
      fetchAnnouncements();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Institute Announcements</h1>
          <p className="text-xs text-slate-500 mt-0.5">Campus notices, course schedule updates, and system broadcasts</p>
        </div>
        {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenCreate}>
            Publish Notice
          </Button>
        )}
      </div>

      {loading ? (
        <LoadingSpinner message="Fetching campus announcements..." />
      ) : announcements.length === 0 ? (
        <Card className="p-8 text-center text-xs text-slate-400 italic">
          No active announcements found.
        </Card>
      ) : (
        <div className="space-y-4">
          {announcements.map((item) => (
            <Card key={item.id} className="p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center text-xl shrink-0 mt-0.5">
                    <HiOutlineMegaphone />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-slate-900 text-base">{item.title}</h3>
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                        Target: {item.target_role || 'All'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Published: {formatDateTime(item.published_at || item.created_at)}
                      {item.course_id ? ` &bull; Course #${item.course_id}` : ''}
                    </p>
                  </div>
                </div>

                {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded cursor-pointer"
                    title="Delete Announcement"
                  >
                    <HiOutlineTrash className="text-base" />
                  </button>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                {item.content}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Announcement Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Broadcast Announcement"
        subtitle="Publish institutional notices across roles or cohorts"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreateAnnouncement} className="space-y-4">
          <Input
            label="Announcement Title *"
            value={createForm.title}
            onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
            placeholder="e.g. Schedule Change: Winter Examination Period"
            required
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Notice Content *
            </label>
            <textarea
              rows={4}
              value={createForm.content}
              onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Announcement text to broadcast..."
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Recipient Audience"
              value={createForm.target_role}
              onChange={(e) => setCreateForm({ ...createForm, target_role: e.target.value })}
              options={[
                { value: 'all', label: 'Everyone (All Users)' },
                { value: 'student', label: 'Students Only' },
                { value: 'instructor', label: 'Instructors Only' },
                { value: 'admin', label: 'Administrators Only' },
              ]}
            />

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Specific Course (Optional)
              </label>
              <select
                value={createForm.course_id}
                onChange={(e) => setCreateForm({ ...createForm, course_id: e.target.value })}
                className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">Institute-wide (No Course Filter)</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code} - {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Publish Announcement
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
