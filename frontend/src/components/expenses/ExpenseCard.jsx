import React, { useState } from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';
import {
  IconReceipt, IconMapPin, IconCalendar, IconCreditCard,
  IconEdit, IconTrash, IconFileText, IconSparkles, IconEye
} from '@tabler/icons-react';

export default function ExpenseCard({ expense, onEdit, onDelete }) {
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  if (!expense) return null;

  const amt = parseFloat(expense.amount || 0);
  const curr = expense.currency || 'USD';
  const meta = expense.receipt_metadata || {};

  return (
    <div className="p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/80 shadow-sm hover:shadow-md transition-all space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 uppercase">
              {expense.category}
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              {expense.payment_method}
            </span>
            {expense.expense_source === 'OCR' && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center gap-1">
                <IconSparkles size={12} /> OCR Scanned
              </span>
            )}
          </div>

          <h4 className="text-sm font-extrabold text-gray-900 dark:text-white flex items-center gap-1">
            {expense.title}
          </h4>

          {expense.location_name && (
            <p className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1 font-semibold">
              <IconMapPin size={13} /> {expense.location_name}
            </p>
          )}

          {expense.notes && (
            <p className="text-xs text-gray-500 dark:text-gray-400 italic line-clamp-1">
              "{expense.notes}"
            </p>
          )}
        </div>

        <div className="text-right space-y-1 shrink-0">
          <div className="text-base font-black text-gray-900 dark:text-white">
            {formatCurrency(amt, curr)}
          </div>
          <div className="text-[10px] text-gray-400 flex items-center justify-end gap-1 font-medium">
            <IconCalendar size={12} /> {String(expense.expense_date)}
          </div>
        </div>
      </div>

      {/* Action buttons & Receipt Preview */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700/60 text-xs">
        {meta.filename ? (
          <button
            onClick={() => setShowReceiptModal(true)}
            className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
          >
            <IconReceipt size={14} /> Receipt ({meta.filename})
          </button>
        ) : (
          <span className="text-[10px] text-gray-400">No Receipt</span>
        )}

        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(expense)}
            className="p-1 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30"
          >
            <IconEdit size={16} />
          </button>
          <button
            onClick={() => onDelete(expense.id)}
            className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30"
          >
            <IconTrash size={16} />
          </button>
        </div>
      </div>

      {/* Receipt Modal Preview */}
      {showReceiptModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-sm w-full p-5 space-y-3 shadow-2xl border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
              <IconReceipt size={18} /> Receipt Metadata
            </h3>
            <div className="text-xs space-y-1 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-xl border border-gray-200 dark:border-gray-600">
              <div><strong>Filename:</strong> {meta.filename}</div>
              <div><strong>OCR Status:</strong> {meta.ocr_status || 'Completed'}</div>
              <div><strong>OCR Confidence:</strong> {meta.ocr_confidence ? `${Math.round(meta.ocr_confidence * 100)}%` : 'N/A'}</div>
            </div>
            <button
              onClick={() => setShowReceiptModal(false)}
              className="w-full py-2 bg-gray-100 dark:bg-gray-700 text-xs font-bold rounded-xl"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
