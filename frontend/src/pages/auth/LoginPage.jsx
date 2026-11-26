import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { HiOutlineMail, HiOutlineLockClosed } from 'react-icons/hi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import { loginStart, loginSuccess, loginFailure } from '../../store/authSlice';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      setError('Please fill in both email and password.');
      return;
    }

    setIsLoading(true);
    dispatch(loginStart());
    try {
      const res = await api.post('/api/auth/login', formData);
      dispatch(loginSuccess(res.data));
      toast.success(`Welcome back, ${res.data.user.full_name}!`);
      navigate('/dashboard');
    } catch (err) {
      const msg = getApiErrorMessage(err);
      setError(msg);
      dispatch(loginFailure(msg));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoFill = () => {
    setFormData({
      email: 'admin@lms-institute.com',
      password: 'Admin@123456',
    });
    setError('');
  };

  return (
    <div>
      <div className="mb-6 text-center">
        <h3 className="text-lg font-bold text-slate-900">Sign in to your account</h3>
        <p className="text-xs text-slate-500 mt-1">Enter your credentials to access the learning portal</p>
      </div>

      <ErrorAlert message={error} onClose={() => setError('')} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email Address"
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="admin@lms-institute.com"
          icon={HiOutlineMail}
          required
        />

        <Input
          label="Password"
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          placeholder="••••••••"
          icon={HiOutlineLockClosed}
          required
        />

        <div className="flex items-center justify-between text-xs">
          <button
            type="button"
            onClick={handleDemoFill}
            className="text-brand-600 hover:text-brand-700 font-semibold cursor-pointer underline decoration-dotted"
          >
            Quick Admin Fill
          </button>
          <Link
            to="/forgot-password"
            className="font-medium text-slate-600 hover:text-brand-600 transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
          Sign In
        </Button>
      </form>

      <div className="mt-6 pt-4 border-t border-slate-100 text-center">
        <Link
          to="/verify-certificate"
          className="text-xs text-slate-500 hover:text-brand-600 font-medium transition-colors"
        >
          Have a certificate? Verify its authenticity here &rarr;
        </Link>
      </div>
    </div>
  );
}
