import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  HiOutlineClock,
  HiOutlineCheckCircle,
  HiOutlineXCircle,
  HiOutlineArrowLeft,
} from 'react-icons/hi2';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';

export default function QuizRunnerPage() {
  const { quizId, attemptId } = useParams();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    const fetchAttempt = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/quizzes/${quizId}/attempts`);
        const found = (res.data || []).find((a) => String(a.id) === String(attemptId));
        if (found) {
          setAttempt(found);
          if (found.status === 'submitted') {
            setIsSubmitted(true);
          }
          // Pre-populate saved answers
          const saved = {};
          (found.answers || []).forEach((ans) => {
            if (ans.selected_option_id) {
              saved[ans.question_id] = ans.selected_option_id;
            }
          });
          setSelectedAnswers(saved);

          // Calculate time left in seconds
          const expires = new Date(found.expires_at).getTime();
          const now = Date.now();
          const diff = Math.max(0, Math.floor((expires - now) / 1000));
          setTimeLeft(diff);
        } else {
          setError('Quiz attempt session not found.');
        }
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    fetchAttempt();
  }, [quizId, attemptId]);

  // Timer countdown
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0 || isSubmitted) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmitQuiz();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, isSubmitted]);

  const handleSelectOption = async (questionId, optionId) => {
    if (isSubmitted) return;

    setSelectedAnswers((prev) => ({ ...prev, [questionId]: optionId }));

    try {
      await api.post(`/api/quizzes/${quizId}/attempts/${attemptId}/save-answer`, {
        question_id: questionId,
        selected_option_id: optionId,
      });
    } catch {
      // silent background save error handling
    }
  };

  const handleSubmitQuiz = async () => {
    setSubmitting(true);
    try {
      const res = await api.post(`/api/quizzes/${quizId}/attempts/${attemptId}/submit`);
      setAttempt(res.data);
      setIsSubmitted(true);
      toast.success('Quiz submitted successfully!');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const formatTimer = (seconds) => {
    if (seconds === null) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  if (loading) return <LoadingSpinner size="lg" message="Loading examination session..." />;
  if (error || !attempt) return <ErrorAlert message={error || 'Attempt not found'} />;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Top Banner with Countdown */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm flex items-center justify-between sticky top-20 z-20">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Attempt #{attempt.attempt_number}
          </span>
          <h2 className="text-base font-bold text-slate-900 leading-tight">Interactive MCQ Examination</h2>
        </div>

        {!isSubmitted ? (
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-sm font-bold shadow-xs ${
              (timeLeft || 0) < 300
                ? 'bg-rose-100 text-rose-700 animate-pulse'
                : 'bg-brand-50 text-brand-700'
            }`}
          >
            <HiOutlineClock className="text-lg" />
            <span>{formatTimer(timeLeft)}</span>
          </div>
        ) : (
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold ${
              attempt.is_passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
            }`}
          >
            {attempt.is_passed ? <HiOutlineCheckCircle className="text-lg" /> : <HiOutlineXCircle className="text-lg" />}
            <span>Score: {attempt.score} ({attempt.is_passed ? 'PASSED' : 'NOT PASSED'})</span>
          </div>
        )}
      </div>

      {/* Result Card if Submitted */}
      {isSubmitted && (
        <Card className="p-6 bg-gradient-to-br from-slate-50 to-brand-50/20 text-center space-y-3">
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl mx-auto ${
              attempt.is_passed ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'
            }`}
          >
            {attempt.is_passed ? '✓' : '!'}
          </div>
          <h3 className="text-lg font-black text-slate-900">
            {attempt.is_passed ? 'Congratulations! You Passed' : 'Attempt Completed'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            You scored <strong className="text-slate-900">{attempt.score}</strong> marks on this assessment.
          </p>
          <div className="pt-2">
            <Button variant="secondary" onClick={() => navigate('/quizzes')} icon={HiOutlineArrowLeft}>
              Back to Quizzes List
            </Button>
          </div>
        </Card>
      )}

      {/* Questions List */}
      <div className="space-y-4">
        {(attempt.questions || []).map((q, qIdx) => {
          const selectedOption = selectedAnswers[q.id];

          return (
            <Card key={q.id} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-md bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {qIdx + 1}
                  </span>
                  <div>
                    <h4 className="font-semibold text-slate-900 text-sm leading-snug">{q.question_text}</h4>
                    <span className="text-[10px] text-slate-400 font-medium">{q.marks} Marks</span>
                  </div>
                </div>
              </div>

              {/* Options */}
              <div className="mt-4 space-y-2">
                {(q.options || []).map((opt) => {
                  const isChecked = selectedOption === opt.id;

                  return (
                    <label
                      key={opt.id}
                      onClick={() => handleSelectOption(q.id, opt.id)}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-xs font-medium cursor-pointer transition-all ${
                        isChecked
                          ? 'border-brand-500 bg-brand-50/40 text-brand-900 shadow-xs'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q_${q.id}`}
                        checked={isChecked}
                        onChange={() => {}}
                        disabled={isSubmitted}
                        className="w-4 h-4 text-brand-600 focus:ring-brand-500 cursor-pointer"
                      />
                      <span>{opt.option_text}</span>
                    </label>
                  );
                })}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Bottom Submit Button */}
      {!isSubmitted && (
        <div className="flex justify-end p-4 bg-white rounded-xl border border-slate-200/80 shadow-sm">
          <Button
            size="lg"
            variant="primary"
            onClick={handleSubmitQuiz}
            isLoading={submitting}
          >
            Submit Final Answers
          </Button>
        </div>
      )}
    </div>
  );
}
