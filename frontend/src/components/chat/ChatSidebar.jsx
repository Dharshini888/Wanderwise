import React, { useState } from 'react';
import {
  IconPlus, IconMessage, IconTrash, IconSearch,
  IconSparkles, IconCompass, IconHistory
} from '@tabler/icons-react';

export default function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateNewSession,
  onDeleteSession
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter(s =>
    (s.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="w-full lg:w-72 glass-card p-4 flex flex-col gap-3 rounded-2xl h-full shrink-0">
      {/* Top CTA */}
      <button
        onClick={onCreateNewSession}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[var(--color-primary-600)] hover:bg-blue-700 text-white font-extrabold text-xs transition-all shadow-md shrink-0"
      >
        <IconPlus size={16} /> New Conversation
      </button>

      {/* Search Input */}
      <div className="relative">
        <IconSearch size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search chats..."
          className="w-full pl-8 pr-3 py-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-xl text-xs font-semibold focus:outline-none focus:border-[var(--color-primary-500)]"
        />
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
        <div className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-wider pl-2 mb-1 flex items-center gap-1">
          <IconHistory size={12} /> Recent Chats ({filteredSessions.length})
        </div>

        {filteredSessions.length === 0 ? (
          <div className="p-4 text-center text-xs text-[var(--text-muted)] font-medium">
            No chats found.
          </div>
        ) : (
          filteredSessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between gap-2 p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-[var(--color-primary-600)]/10 text-[var(--color-primary-600)] dark:text-blue-400 font-extrabold border border-blue-500/20'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)]'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <IconMessage size={15} className={isActive ? 'text-[var(--color-primary-600)] dark:text-blue-400 shrink-0' : 'text-[var(--text-muted)] shrink-0'} />
                  <span className="truncate">{session.title || 'Conversation'}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  title="Delete Session"
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500 transition-all shrink-0"
                >
                  <IconTrash size={13} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
