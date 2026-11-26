import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  HiOutlineAcademicCap,
  HiOutlineClock,
  HiOutlineCurrencyDollar,
  HiOutlineUserGroup,
  HiOutlinePlus,
  HiOutlineTrash,
  HiOutlinePlayCircle,
  HiOutlineDocumentArrowDown,
  HiOutlineCheckCircle,
  HiOutlineArrowLeft,
  HiOutlineArrowUpTray,
  HiOutlineSparkles,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatCurrency, formatFileSize } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function CourseDetailPage() {
  const { id } = useParams();
  const { role, user } = useSelector((state) => state.auth);

  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Course Progress (Student)
  const [progress, setProgress] = useState(null);

  // Module modal
  const [isModuleModalOpen, setIsModuleModalOpen] = useState(false);
  const [moduleForm, setModuleForm] = useState({ title: '', description: '', sequence_order: 1 });
  const [moduleLoading, setModuleLoading] = useState(false);

  // Lecture modal
  const [isLectureModalOpen, setIsLectureModalOpen] = useState(false);
  const [selectedModuleId, setSelectedModuleId] = useState(null);
  const [lectureForm, setLectureForm] = useState({
    title: '',
    description: '',
    duration_minutes: 30,
    video_url: '',
    sequence_order: 1,
    is_published: true,
  });
  const [lectureLoading, setLectureLoading] = useState(false);

  // Video Upload modal
  const [videoUploadLecture, setVideoUploadLecture] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoUploadLoading, setVideoUploadLoading] = useState(false);

  // Active Video Player Modal
  const [activeVideoLecture, setActiveVideoLecture] = useState(null);

  // Study Material modal
  const [isMaterialModalOpen, setIsMaterialModalOpen] = useState(false);
  const [materialForm, setMaterialForm] = useState({ title: '', description: '', file: null });
  const [materialLoading, setMaterialLoading] = useState(false);

  // Co-Instructor modal
  const [isInstructorModalOpen, setIsInstructorModalOpen] = useState(false);
  const [allInstructors, setAllInstructors] = useState([]);
  const [selectedInstructorId, setSelectedInstructorId] = useState('');
  const [instructorLoading, setInstructorLoading] = useState(false);

  // Lectures map by module_id
  const [moduleLectures, setModuleLectures] = useState({});
  const [moduleMaterials, setModuleMaterials] = useState({});

  const fetchCourseData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/courses/${id}`);
      setCourse(res.data);

      // Fetch lectures and materials for this course
      const [lecRes, matRes] = await Promise.all([
        api.get(`/api/lectures?course_id=${id}&page=1&page_size=100`),
        api.get(`/api/materials?course_id=${id}&page=1&page_size=100`),
      ]);

      // Group lectures by module_id
      const lMap = {};
      (lecRes.data.items || []).forEach((lec) => {
        if (!lMap[lec.module_id]) lMap[lec.module_id] = [];
        lMap[lec.module_id].push(lec);
      });
      setModuleLectures(lMap);

      // Group materials by module_id
      const mMap = {};
      (matRes.data.items || []).forEach((mat) => {
        const mId = mat.module_id || 0;
        if (!mMap[mId]) mMap[mId] = [];
        mMap[mId].push(mat);
      });
      setModuleMaterials(mMap);

      // If student, fetch progress
      if (role === ROLES.STUDENT && user?.id) {
        try {
          const progRes = await api.get(`/api/progress/courses/${id}/students/${user.id}`);
          setProgress(progRes.data);
        } catch {
          // ignore if student is not yet enrolled
        }
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourseData();
  }, [id, role]);

  const handleStatusChange = async (action) => {
    try {
      await api.post(`/api/courses/${id}/${action}`);
      toast.success(`Course successfully ${action}d!`);
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateModule = async (e) => {
    e.preventDefault();
    setModuleLoading(true);
    try {
      await api.post(`/api/courses/${id}/modules`, {
        ...moduleForm,
        sequence_order: parseInt(moduleForm.sequence_order) || 1,
      });
      toast.success('Module added!');
      setIsModuleModalOpen(false);
      setModuleForm({ title: '', description: '', sequence_order: 1 });
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setModuleLoading(false);
    }
  };

  const handleDeleteModule = async (moduleId) => {
    if (!window.confirm('Are you sure you want to delete this module?')) return;
    try {
      await api.delete(`/api/courses/${id}/modules/${moduleId}`);
      toast.success('Module deleted');
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateLecture = async (e) => {
    e.preventDefault();
    setLectureLoading(true);
    try {
      await api.post('/api/lectures', {
        ...lectureForm,
        course_id: parseInt(id),
        module_id: selectedModuleId,
        duration_minutes: parseInt(lectureForm.duration_minutes) || 0,
        sequence_order: parseInt(lectureForm.sequence_order) || 1,
      });
      toast.success('Lecture created!');
      setIsLectureModalOpen(false);
      setLectureForm({
        title: '',
        description: '',
        duration_minutes: 30,
        video_url: '',
        sequence_order: 1,
        is_published: true,
      });
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLectureLoading(false);
    }
  };

  const handleCompleteLecture = async (lectureId) => {
    try {
      await api.post(`/api/lectures/${lectureId}/complete`);
      toast.success('Lecture marked as completed!');
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleUploadVideo = async (e) => {
    e.preventDefault();
    if (!videoFile || !videoUploadLecture) return;

    setVideoUploadLoading(true);
    const formData = new FormData();
    formData.append('file', videoFile);

    try {
      await api.post(`/api/lectures/${videoUploadLecture.id}/upload-video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Lecture video uploaded successfully!');
      setVideoUploadLecture(null);
      setVideoFile(null);
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setVideoUploadLoading(false);
    }
  };

  const handleUploadMaterial = async (e) => {
    e.preventDefault();
    if (!materialForm.file) {
      toast.error('Please choose a file to upload');
      return;
    }
    setMaterialLoading(true);
    const formData = new FormData();
    formData.append('course_id', id);
    formData.append('title', materialForm.title);
    if (materialForm.description) formData.append('description', materialForm.description);
    if (selectedModuleId) formData.append('module_id', selectedModuleId);
    formData.append('file', materialForm.file);

    try {
      await api.post('/api/materials', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Study material uploaded!');
      setIsMaterialModalOpen(false);
      setMaterialForm({ title: '', description: '', file: null });
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setMaterialLoading(false);
    }
  };

  const handleDownloadMaterial = (matId) => {
    window.open(`${api.defaults.baseURL}/api/materials/${matId}/download`, '_blank');
  };

  const handleOpenAssignInstructor = async () => {
    try {
      const res = await api.get('/api/instructors?page=1&page_size=50');
      setAllInstructors(res.data.items || []);
      setIsInstructorModalOpen(true);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleAssignInstructor = async (e) => {
    e.preventDefault();
    if (!selectedInstructorId) return;
    setInstructorLoading(true);
    try {
      await api.post(`/api/courses/${id}/instructors`, {
        instructor_id: parseInt(selectedInstructorId),
      });
      toast.success('Instructor assigned to course!');
      setIsInstructorModalOpen(false);
      setSelectedInstructorId('');
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setInstructorLoading(false);
    }
  };

  const handleRemoveInstructor = async (instId) => {
    if (!window.confirm('Remove instructor from this course?')) return;
    try {
      await api.delete(`/api/courses/${id}/instructors/${instId}`);
      toast.success('Instructor removed');
      fetchCourseData();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  if (loading) return <LoadingSpinner size="lg" message="Loading course curriculum..." />;
  if (error || !course) return <ErrorAlert message={error || 'Course not found'} />;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/courses"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <HiOutlineArrowLeft className="text-lg" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-500 uppercase">{course.course_code}</span>
              <Badge status={course.status} />
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-0.5">{course.name}</h1>
          </div>
        </div>

        {/* Admin Lifecycle controls */}
        {role === ROLES.ADMIN && (
          <div className="flex flex-wrap items-center gap-2">
            {course.status === 'draft' && (
              <Button size="sm" variant="success" onClick={() => handleStatusChange('publish')}>
                Publish Course
              </Button>
            )}
            {course.status === 'published' && (
              <Button size="sm" variant="secondary" onClick={() => handleStatusChange('unpublish')}>
                Revert to Draft
              </Button>
            )}
            {course.status !== 'archived' && (
              <Button size="sm" variant="ghost" onClick={() => handleStatusChange('archive')}>
                Archive
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              icon={HiOutlineUserGroup}
              onClick={handleOpenAssignInstructor}
            >
              Assign Co-Instructor
            </Button>
            <Button
              size="sm"
              variant="primary"
              icon={HiOutlinePlus}
              onClick={() => setIsModuleModalOpen(true)}
            >
              Add Module
            </Button>
          </div>
        )}
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Description & Instructors */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Course Overview">
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{course.description}</p>
            <div className="mt-6 pt-4 border-t border-slate-100 flex flex-wrap gap-6 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <HiOutlineAcademicCap className="text-lg text-slate-400" />
                <span>Category: <strong className="text-slate-800">{course.category}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <HiOutlineClock className="text-lg text-slate-400" />
                <span>Duration: <strong className="text-slate-800">{course.duration_hours} Hours</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <HiOutlineCurrencyDollar className="text-lg text-slate-400" />
                <span>Tuition: <strong className="text-slate-800">{formatCurrency(course.fee)}</strong></span>
              </div>
            </div>
          </Card>

          {/* Assigned Faculty */}
          <Card title="Instructional Faculty" subtitle="Assigned course instructors">
            {(!course.assigned_instructors || course.assigned_instructors.length === 0) ? (
              <p className="text-xs text-slate-400">No instructors assigned yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {course.assigned_instructors.map((inst) => (
                  <div key={inst.instructor_id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{inst.full_name}</p>
                      <p className="text-[11px] text-slate-400 font-mono">{inst.employee_code}</p>
                    </div>
                    {role === ROLES.ADMIN && (
                      <button
                        onClick={() => handleRemoveInstructor(inst.instructor_id)}
                        className="text-xs text-rose-500 hover:text-rose-700 font-medium cursor-pointer"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right: Student Progress Tracker if applicable */}
        <div className="lg:col-span-1 space-y-6">
          {progress && (
            <Card title="My Course Progress" subtitle="Academic Completion Tracker">
              <div className="text-center py-2">
                <div className="text-3xl font-black text-brand-600">
                  {Math.round(progress.overall_progress_pct || 0)}%
                </div>
                <p className="text-xs text-slate-500 mt-1">Overall Completion</p>
                <div className="w-full bg-slate-100 rounded-full h-2 mt-3 overflow-hidden">
                  <div
                    className="bg-brand-600 h-2 rounded-full transition-all"
                    style={{ width: `${progress.overall_progress_pct || 0}%` }}
                  />
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Lectures Completed:</span>
                  <span className="font-semibold text-slate-800">
                    {progress.completed_lectures} / {progress.total_lectures}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Assignments Passed:</span>
                  <span className="font-semibold text-slate-800">
                    {progress.assignments_passed} / {progress.total_assignments}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Quizzes Passed:</span>
                  <span className="font-semibold text-slate-800">
                    {progress.quizzes_passed} / {progress.total_quizzes}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Attendance Percentage:</span>
                  <span className="font-semibold text-slate-800">
                    {progress.attendance_percentage}%
                  </span>
                </div>
                <div className="pt-2">
                  {progress.is_course_completed ? (
                    <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-800 text-center font-bold">
                      Course Completed! Certificate Eligible
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-400 text-center italic">
                      Complete 100% of lectures, assignments, and quizzes to earn certificate.
                    </p>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Quick links */}
          <Card title="Assessment Links">
            <div className="space-y-2 text-xs">
              <Link
                to={`/assignments?course_id=${id}`}
                className="block p-3 rounded-lg border border-slate-100 hover:bg-slate-50 font-semibold text-slate-800 transition-colors"
              >
                View Course Assignments &rarr;
              </Link>
              <Link
                to={`/quizzes?course_id=${id}`}
                className="block p-3 rounded-lg border border-slate-100 hover:bg-slate-50 font-semibold text-slate-800 transition-colors"
              >
                View Course Quizzes &rarr;
              </Link>
            </div>
          </Card>
        </div>
      </div>

      {/* Curriculum & Modules */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Curriculum Syllabus & Modules</h2>
          {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
            <Button
              size="sm"
              variant="secondary"
              icon={HiOutlinePlus}
              onClick={() => setIsModuleModalOpen(true)}
            >
              Add Module
            </Button>
          )}
        </div>

        {(!course.modules || course.modules.length === 0) ? (
          <div className="p-8 text-center bg-white rounded-xl border border-slate-200/80 text-xs text-slate-500">
            No curriculum modules created yet. Add a module to begin organizing lectures.
          </div>
        ) : (
          course.modules.map((mod, idx) => {
            const lectures = moduleLectures[mod.id] || [];
            const materials = moduleMaterials[mod.id] || [];

            return (
              <div
                key={mod.id}
                className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden"
              >
                {/* Module Bar */}
                <div className="px-5 py-4 bg-slate-50/75 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-md bg-brand-600 text-white flex items-center justify-center font-bold text-xs">
                      {idx + 1}
                    </span>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm">{mod.title}</h3>
                      {mod.description && <p className="text-xs text-slate-500 mt-0.5">{mod.description}</p>}
                    </div>
                  </div>

                  {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        icon={HiOutlinePlus}
                        onClick={() => {
                          setSelectedModuleId(mod.id);
                          setIsLectureModalOpen(true);
                        }}
                      >
                        Lecture
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        icon={HiOutlineArrowUpTray}
                        onClick={() => {
                          setSelectedModuleId(mod.id);
                          setIsMaterialModalOpen(true);
                        }}
                      >
                        Material
                      </Button>
                      <button
                        onClick={() => handleDeleteModule(mod.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded cursor-pointer"
                        title="Delete Module"
                      >
                        <HiOutlineTrash className="text-base" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Lectures List */}
                <div className="divide-y divide-slate-100">
                  {lectures.length === 0 && materials.length === 0 ? (
                    <div className="p-4 text-center text-xs text-slate-400 italic">
                      No lectures or materials in this module yet.
                    </div>
                  ) : (
                    <>
                      {lectures.map((lec) => (
                        <div
                          key={lec.id}
                          className="p-4 flex items-center justify-between hover:bg-slate-50/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <HiOutlinePlayCircle className="text-2xl text-brand-600 shrink-0" />
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-slate-800">{lec.title}</p>
                                {lec.is_completed && (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                                    <HiOutlineCheckCircle /> Watched
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {lec.duration_minutes} min &bull; {lec.has_uploaded_video ? 'Uploaded Video Available' : 'Streaming Link'}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {/* Video Play */}
                            {(lec.has_uploaded_video || lec.video_url) && (
                              <Button
                                size="sm"
                                variant="secondary"
                                icon={HiOutlinePlayCircle}
                                onClick={() => setActiveVideoLecture(lec)}
                              >
                                Watch
                              </Button>
                            )}

                            {/* Student Complete */}
                            {role === ROLES.STUDENT && !lec.is_completed && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleCompleteLecture(lec.id)}
                              >
                                Mark Completed
                              </Button>
                            )}

                            {/* Instructor Video Upload */}
                            {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
                              <Button
                                size="sm"
                                variant="ghost"
                                icon={HiOutlineArrowUpTray}
                                onClick={() => setVideoUploadLecture(lec)}
                              >
                                Upload MP4
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}

                      {/* Materials List */}
                      {materials.map((mat) => (
                        <div
                          key={mat.id}
                          className="p-4 flex items-center justify-between bg-slate-50/20 hover:bg-slate-50/60 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <HiOutlineDocumentArrowDown className="text-2xl text-amber-600 shrink-0" />
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{mat.title}</p>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {mat.file_name} &bull; {formatFileSize(mat.file_size)}
                              </p>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="secondary"
                            icon={HiOutlineDocumentArrowDown}
                            onClick={() => handleDownloadMaterial(mat.id)}
                          >
                            Download
                          </Button>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Add Module Modal */}
      <Modal
        isOpen={isModuleModalOpen}
        onClose={() => setIsModuleModalOpen(false)}
        title="Add Curriculum Module"
        subtitle="Organize lectures into progressive syllabus modules"
      >
        <form onSubmit={handleCreateModule} className="space-y-4">
          <Input
            label="Module Title"
            value={moduleForm.title}
            onChange={(e) => setModuleForm({ ...moduleForm, title: e.target.value })}
            placeholder="e.g. Module 1: Introduction to Architecture"
            required
          />
          <Input
            label="Sequence Order"
            type="number"
            min="1"
            value={moduleForm.sequence_order}
            onChange={(e) => setModuleForm({ ...moduleForm, sequence_order: e.target.value })}
            required
          />
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Description (Optional)
            </label>
            <textarea
              rows={2}
              value={moduleForm.description}
              onChange={(e) => setModuleForm({ ...moduleForm, description: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="What this module covers..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsModuleModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={moduleLoading}>
              Add Module
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Lecture Modal */}
      <Modal
        isOpen={isLectureModalOpen}
        onClose={() => setIsLectureModalOpen(false)}
        title="Add Lecture to Module"
        subtitle="Define video lesson or lecture item"
      >
        <form onSubmit={handleCreateLecture} className="space-y-4">
          <Input
            label="Lecture Title"
            value={lectureForm.title}
            onChange={(e) => setLectureForm({ ...lectureForm, title: e.target.value })}
            placeholder="e.g. Setting up FastApi and Vite"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Duration (Minutes)"
              type="number"
              min="0"
              value={lectureForm.duration_minutes}
              onChange={(e) => setLectureForm({ ...lectureForm, duration_minutes: e.target.value })}
            />
            <Input
              label="Sequence Order"
              type="number"
              min="1"
              value={lectureForm.sequence_order}
              onChange={(e) => setLectureForm({ ...lectureForm, sequence_order: e.target.value })}
            />
          </div>
          <Input
            label="Video Stream URL (Optional)"
            value={lectureForm.video_url}
            onChange={(e) => setLectureForm({ ...lectureForm, video_url: e.target.value })}
            placeholder="https://youtube.com/embed/... or direct stream link"
          />
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsLectureModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={lectureLoading}>
              Create Lecture
            </Button>
          </div>
        </form>
      </Modal>

      {/* Upload Video Modal */}
      <Modal
        isOpen={!!videoUploadLecture}
        onClose={() => setVideoUploadLecture(null)}
        title="Upload Video Lecture"
        subtitle={`Uploading video file for "${videoUploadLecture?.title}"`}
      >
        <form onSubmit={handleUploadVideo} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center">
            <input
              type="file"
              accept="video/mp4,video/webm,video/quicktime"
              onChange={(e) => setVideoFile(e.target.files[0])}
              className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
              required
            />
            <p className="text-[11px] text-slate-400 mt-2">Accepted formats: .mp4, .webm, .mov (Max 500MB)</p>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setVideoUploadLecture(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={videoUploadLoading}>
              Upload Video
            </Button>
          </div>
        </form>
      </Modal>

      {/* Watch Video Modal */}
      <Modal
        isOpen={!!activeVideoLecture}
        onClose={() => setActiveVideoLecture(null)}
        title={activeVideoLecture?.title || 'Lecture Video'}
        maxWidth="max-w-4xl"
      >
        {activeVideoLecture && (
          <div className="space-y-4">
            <div className="aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center">
              {activeVideoLecture.has_uploaded_video ? (
                <video
                  controls
                  autoPlay
                  className="w-full h-full"
                  src={`${api.defaults.baseURL}/api/lectures/${activeVideoLecture.id}/video`}
                />
              ) : activeVideoLecture.video_url ? (
                <iframe
                  title={activeVideoLecture.title}
                  src={activeVideoLecture.video_url}
                  className="w-full h-full border-0"
                  allowFullScreen
                />
              ) : (
                <p className="text-white text-xs">No playable video source found.</p>
              )}
            </div>
            {activeVideoLecture.description && (
              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl">
                {activeVideoLecture.description}
              </p>
            )}
          </div>
        )}
      </Modal>

      {/* Upload Material Modal */}
      <Modal
        isOpen={isMaterialModalOpen}
        onClose={() => setIsMaterialModalOpen(false)}
        title="Upload Study Material"
        subtitle="Share lecture slides, code exercises, or PDF documents"
      >
        <form onSubmit={handleUploadMaterial} className="space-y-4">
          <Input
            label="Material Title"
            value={materialForm.title}
            onChange={(e) => setMaterialForm({ ...materialForm, title: e.target.value })}
            placeholder="e.g. Lecture Notes & Cheatsheet"
            required
          />
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center">
            <input
              type="file"
              onChange={(e) => setMaterialForm({ ...materialForm, file: e.target.files[0] })}
              className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
              required
            />
            <p className="text-[11px] text-slate-400 mt-2">Accepted formats: PDF, PPT, PPTX, DOC, DOCX, ZIP (Max 50MB)</p>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsMaterialModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={materialLoading}>
              Upload Document
            </Button>
          </div>
        </form>
      </Modal>

      {/* Assign Instructor Modal */}
      <Modal
        isOpen={isInstructorModalOpen}
        onClose={() => setIsInstructorModalOpen(false)}
        title="Assign Co-Instructor"
        subtitle="Authorize an instructor to manage course content and rosters"
      >
        <form onSubmit={handleAssignInstructor} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Faculty Instructor *
            </label>
            <select
              value={selectedInstructorId}
              onChange={(e) => setSelectedInstructorId(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose an instructor...</option>
              {allInstructors.map((inst) => (
                <option key={inst.instructor_profile_id} value={inst.instructor_profile_id}>
                  {inst.full_name} ({inst.employee_code}) - {inst.expertise || 'Faculty'}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsInstructorModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={instructorLoading}>
              Assign Instructor
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
