import React from 'react';
import ReactMarkdown from 'react-markdown';
import { IconSparkles, IconUser } from '@tabler/icons-react';
import AIActionCard from './AIActionCard';

export default function ChatMessage({ message, onActionTrigger }) {
  if (!message) return null;

  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} my-2`}>
      <div className={`flex items-start gap-2.5 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 shadow-sm ${
          isUser
            ? 'bg-[var(--color-primary-600)] text-white'
            : 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
        }`}>
          {isUser ? <IconUser size={15} /> : <IconSparkles size={15} />}
        </div>

        {/* Message Bubble */}
        <div className={`space-y-2`}>
          <div className={`px-4 py-3 text-xs leading-relaxed shadow-sm ${
            isUser
              ? 'bg-[var(--color-primary-600)] text-white rounded-2xl rounded-tr-xs font-semibold'
              : 'glass-card text-[var(--text-primary)] rounded-2xl rounded-tl-xs'
          }`}>
            <ReactMarkdown
              components={{
                p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                a: ({node, ...props}) => <a className={isUser ? 'text-blue-100 underline' : 'text-[var(--color-primary-600)] dark:text-blue-400 underline'} {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                strong: ({node, ...props}) => <strong className="font-extrabold text-[var(--text-primary)]" {...props} />
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Render Action Cards if assistant generated any */}
          {!isUser && message.actions && message.actions.length > 0 && (
            <div className="space-y-2">
              {message.actions.map((act, idx) => (
                <AIActionCard key={idx} action={act} onActionTrigger={onActionTrigger} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
