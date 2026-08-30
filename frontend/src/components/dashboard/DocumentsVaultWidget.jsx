import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { IconFileText, IconAlertTriangle, IconChevronRight, IconLock, IconPlus } from '@tabler/icons-react';
import { getDocumentStats } from '../../api/documents';

export default function DocumentsVaultWidget() {
  const [stats, setStats] = useState({ total: 0, active: 0, expiring_soon: 0, expired: 0, trip_linked: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchStats = async () => {
      try {
        const data = await getDocumentStats();
        if (isMounted) setStats(data);
      } catch (_) {
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchStats();
    return () => { isMounted = false; };
  }, []);

  return (
    <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg hover:shadow-xl transition-all space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <IconFileText size={24} />
          </div>
          <div>
            <div className="text-[10px] font-extrabold uppercase text-[var(--text-muted)] tracking-wider">
              Travel Documents Vault
            </div>
            <h4 className="text-base font-black text-[var(--text-primary)]">
              Smart Vault
            </h4>
          </div>
        </div>
        <Link
          to="/documents"
          className="flex items-center gap-1 text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
        >
          <span>View Vault</span>
          <IconChevronRight size={16} />
        </Link>
      </div>

      {loading ? (
        <div className="h-16 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="p-3.5 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
            <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">Saved Documents</div>
            <div className="text-xl font-extrabold text-[var(--text-primary)] mt-0.5">{stats.total}</div>
          </div>

          <div className={`p-3.5 rounded-2xl border ${
            stats.expiring_soon > 0 || stats.expired > 0
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400'
              : 'bg-[var(--bg-glass)] border-[var(--border-color)]'
          }`}>
            <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">Expiring / Alert</div>
            <div className="text-xl font-extrabold flex items-center justify-between mt-0.5">
              <span>{stats.expiring_soon + stats.expired}</span>
              {(stats.expiring_soon > 0 || stats.expired > 0) && (
                <IconAlertTriangle size={18} className="text-amber-500 animate-bounce" />
              )}
            </div>
          </div>
        </div>
      )}

      {stats.expiring_soon > 0 && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs font-semibold flex items-center gap-2">
          <IconAlertTriangle size={16} className="shrink-0" />
          <span>{stats.expiring_soon} document(s) expiring within 30 days.</span>
        </div>
      )}
    </div>
  );
}
