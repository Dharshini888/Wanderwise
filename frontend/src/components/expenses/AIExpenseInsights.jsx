import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';
import {
  IconSparkles, IconAlertTriangle, IconCheck, IconTrendingDown, IconShieldCheck
} from '@tabler/icons-react';

export default function AIExpenseInsights({ insights, currency = 'USD' }) {
  if (!insights) return null;

  const score = insights.budget_score || 88;
  const health = insights.health || 'Healthy';
  const forecast = insights.forecast || 'Spending is on target.';
  const projSpend = parseFloat(insights.projected_spend || 0);
  const recToday = parseFloat(insights.recommended_today_spend || 0);

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 text-white shadow-xl space-y-4 border border-purple-800/50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-400/30 text-purple-300">
            <IconSparkles size={20} />
          </div>
          <div>
            <h3 className="text-sm font-extrabold font-heading text-white">AI Budget Advisor</h3>
            <span className="text-[10px] text-purple-200">Real-time spend forecast & recommendations</span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-xl font-black text-amber-300">{score}/100</div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-200">{health}</span>
        </div>
      </div>

      {/* Forecast Banner */}
      <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/15 text-xs text-purple-100 flex items-start gap-2">
        <IconShieldCheck size={16} className="text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-white block">Spending Forecast:</strong>
          {forecast} (Estimated final trip spend: {formatCurrency(projSpend, currency)})
        </div>
      </div>

      {/* Smart Alerts */}
      {insights.smart_alerts && insights.smart_alerts.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-purple-300">Smart Alerts</span>
          <div className="space-y-1">
            {insights.smart_alerts.map((alert, i) => (
              <div key={i} className="text-xs text-amber-200 bg-amber-500/15 p-2 rounded-lg border border-amber-500/30 flex items-center gap-2">
                <IconAlertTriangle size={14} className="text-amber-400 shrink-0" />
                <span>{alert}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Money Saving Recommendations */}
      {insights.top_savings && insights.top_savings.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-purple-300">Money Saving Tips</span>
          <div className="space-y-1 text-xs">
            {insights.top_savings.map((tip, i) => (
              <div key={i} className="text-purple-100 bg-white/5 p-2 rounded-lg flex items-start gap-2 border border-white/10">
                <IconCheck size={14} className="text-emerald-400 shrink-0 mt-0.5" />
                <span>{tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
