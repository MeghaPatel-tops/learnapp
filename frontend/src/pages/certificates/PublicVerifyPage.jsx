import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { HiOutlineCheckBadge, HiOutlineXCircle, HiOutlineMagnifyingGlass, HiOutlineArrowLeft } from 'react-icons/hi2';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/feedback/LoadingSpinner';
import api, { getApiErrorMessage } from '../../services/api';
import { formatDate } from '../../utils/formatters';

export default function PublicVerifyPage() {
  const { code: urlCode } = useParams();
  const [code, setCode] = useState(urlCode || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleVerify = async (searchCode) => {
    const query = searchCode || code;
    if (!query) return;

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await api.get(`/api/certificates/verify/${encodeURIComponent(query)}`);
      setResult(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (urlCode) {
      handleVerify(urlCode);
    }
  }, [urlCode]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-brand-50/20 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 mb-6 transition-colors"
          >
            <HiOutlineArrowLeft /> Back to Portal Sign In
          </Link>
          <div className="inline-flex w-14 h-14 rounded-2xl bg-brand-600 text-white items-center justify-center font-bold text-2xl shadow-lg shadow-brand-500/30 mb-3">
            <HiOutlineCheckBadge className="text-3xl" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Certificate Authenticity Verification</h1>
          <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
            Official public verification service by Apex Training Institute. Enter any certificate ID or verification code to validate credential authenticity.
          </p>
        </div>

        <Card className="p-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleVerify();
            }}
            className="flex flex-col sm:flex-row gap-3"
          >
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. CERT-2026-XXXX or verification code"
              icon={HiOutlineMagnifyingGlass}
              className="flex-1"
              required
            />
            <Button type="submit" variant="primary" isLoading={loading} className="shrink-0">
              Verify Credential
            </Button>
          </form>

          {loading && <LoadingSpinner message="Searching verification records..." />}

          {error && !loading && (
            <div className="mt-6 rounded-xl bg-rose-50 border border-rose-200 p-5 text-center space-y-2">
              <HiOutlineXCircle className="mx-auto text-3xl text-rose-500" />
              <h4 className="text-sm font-bold text-rose-900">Certificate Not Found</h4>
              <p className="text-xs text-rose-700">{error}</p>
            </div>
          )}

          {result && !loading && (
            <div className="mt-6 rounded-2xl bg-emerald-50/60 border border-emerald-200 p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-emerald-200/60">
                <div className="flex items-center gap-2">
                  <HiOutlineCheckBadge className="text-2xl text-emerald-600" />
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                    Official Verified Credential
                  </span>
                </div>
                <span className="text-[11px] font-mono font-bold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-lg">
                  {result.certificate_number}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 font-medium">Recipient Student:</span>
                  <p className="text-sm font-bold text-slate-900 mt-0.5">{result.student_name}</p>
                  <p className="text-[11px] text-slate-500">{result.student_code}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Program / Course:</span>
                  <p className="text-sm font-bold text-slate-900 mt-0.5">{result.course_name}</p>
                  <p className="text-[11px] text-slate-500">{result.course_code}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Date of Issuance:</span>
                  <p className="text-sm font-bold text-slate-800 mt-0.5">{formatDate(result.issue_date)}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Verification Code:</span>
                  <p className="text-sm font-mono font-bold text-slate-800 mt-0.5">{result.verification_code}</p>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
