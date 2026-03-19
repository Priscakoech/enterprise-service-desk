import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, KeyRound, Copy, Check, RefreshCw } from 'lucide-react';
import api from '../../api/client';

export default function SignupCodePage() {
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const timerRef = useRef(null);

  const fetchCode = () => {
    api.get('/accounts/signup-code/')
      .then((r) => {
        setCode(r.data.code);
        setSecondsLeft(r.data.seconds_remaining);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchCode();
    return () => clearInterval(timerRef.current);
  }, []);

  // Countdown timer — refetch when it hits 0
  useEffect(() => {
    clearInterval(timerRef.current);
    if (secondsLeft <= 0) return;
    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          fetchCode();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [code]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const progress = secondsLeft / 600;

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Signup Auth Code</h1>
      </div>

      <div className="max-w-lg mx-auto">
        <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-8">
          <div className="text-center">
            <div className="w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-7 h-7 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              Share this code with agents and managers so they can register. The code rotates automatically every 10 minutes.
            </p>

            {loading ? (
              <div className="flex items-center justify-center py-8 text-slate-400">
                <RefreshCw className="w-5 h-5 animate-spin" />
              </div>
            ) : (
              <>
                {/* Code display */}
                <div className="relative inline-block">
                  <div className="flex items-center gap-3 px-6 py-4 rounded-xl bg-slate-50 dark:bg-slate-800 border-2 border-dashed border-slate-300 dark:border-slate-600">
                    <span className="text-3xl font-mono font-bold tracking-[0.2em] text-slate-900 dark:text-white">
                      {code}
                    </span>
                    <button
                      onClick={handleCopy}
                      className="p-2 rounded-lg text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                      title="Copy code"
                    >
                      {copied ? <Check className="w-5 h-5 text-green-500" /> : <Copy className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Timer */}
                <div className="mt-6">
                  <div className="flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-2">
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>
                      Refreshes in {minutes}:{seconds.toString().padStart(2, '0')}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 max-w-xs mx-auto">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-1000"
                      style={{ width: `${progress * 100}%` }}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Info card */}
        <div className="mt-4 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-400 mb-1">How it works</h3>
          <ul className="text-sm text-amber-700 dark:text-amber-400/80 space-y-1">
            <li>- Agents and managers must enter this code when signing up</li>
            <li>- Requesters can sign up freely without a code</li>
            <li>- The code changes automatically every 10 minutes</li>
            <li>- Only share the code with authorized personnel</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
