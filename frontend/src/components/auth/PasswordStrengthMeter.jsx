import { useMemo } from 'react';
import { IconCheck, IconX } from '@tabler/icons-react';

export default function PasswordStrengthMeter({ password = '' }) {
  const analysis = useMemo(() => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password),
    };

    const passedCount = Object.values(checks).filter(Boolean).length;
    let score = 0;
    let label = 'Too Short';
    let color = 'bg-gray-300';
    let textColor = 'text-gray-400';

    if (password.length > 0) {
      if (passedCount <= 2) {
        score = 25;
        label = 'Weak';
        color = 'bg-red-500';
        textColor = 'text-red-500';
      } else if (passedCount === 3) {
        score = 50;
        label = 'Fair';
        color = 'bg-amber-500';
        textColor = 'text-amber-500';
      } else if (passedCount === 4) {
        score = 75;
        label = 'Good';
        color = 'bg-blue-500';
        textColor = 'text-blue-500';
      } else if (passedCount === 5) {
        score = 100;
        label = 'Strong & Secure';
        color = 'bg-emerald-500';
        textColor = 'text-emerald-500';
      }
    }

    return { checks, score, label, color, textColor };
  }, [password]);

  if (!password) return null;

  return (
    <div className="mt-2 flex flex-col gap-2 text-xs">
      {/* Progress Bar */}
      <div className="flex justify-between items-center text-[11px] font-semibold">
        <span className="text-[var(--text-muted)] uppercase tracking-wider">Password Strength</span>
        <span className={`font-bold ${analysis.textColor}`}>{analysis.label}</span>
      </div>

      <div className="w-full bg-[var(--border-color)] h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${analysis.color}`}
          style={{ width: `${analysis.score}%` }}
        ></div>
      </div>

      {/* Criteria Checklist */}
      <div className="grid grid-cols-2 gap-1.5 mt-1 text-[11px]">
        {[
          { key: 'length', label: '8+ characters' },
          { key: 'uppercase', label: 'Uppercase letter' },
          { key: 'lowercase', label: 'Lowercase letter' },
          { key: 'number', label: 'At least 1 number' },
          { key: 'special', label: 'Special symbol' },
        ].map((rule) => {
          const isValid = analysis.checks[rule.key];
          return (
            <div
              key={rule.key}
              className={`flex items-center gap-1 font-medium transition-colors ${
                isValid ? 'text-emerald-600 dark:text-emerald-400' : 'text-[var(--text-muted)]'
              }`}
            >
              {isValid ? <IconCheck size={12} /> : <IconX size={12} className="opacity-40" />}
              <span>{rule.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
