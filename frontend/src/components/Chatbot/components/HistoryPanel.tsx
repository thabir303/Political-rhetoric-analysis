import React from 'react';
import { History, Clock, Download, Trash2, X } from 'lucide-react';

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  messages: any[];
}

interface HistoryPanelProps {
  show: boolean;
  sessions: ChatSession[];
  currentSessionId: string;
  onClose: () => void;
  onLoadSession: (sessionId: string) => void;
  onExportSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({
  show,
  sessions,
  currentSessionId,
  onClose,
  onLoadSession,
  onExportSession,
  onDeleteSession,
}) => {
  if (!show) return null;

  return (
    <div className="absolute top-16 right-0 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border-2 border-gray-200 dark:border-gray-700 z-50 max-h-[500px] overflow-hidden flex flex-col">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 flex items-center justify-between rounded-t-xl">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5" />
          <h3 className="font-bold text-sm">Chat History</h3>
        </div>
        <button
          onClick={onClose}
          className="hover:bg-white/20 p-1.5 rounded-lg transition-all cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-3">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No chat history yet</p>
            <p className="text-xs mt-1">Start a conversation to save history</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 border-2 transition-all cursor-pointer hover:shadow-md ${
                  session.id === currentSessionId
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-blue-300'
                }`}
              >
                <div
                  onClick={() => onLoadSession(session.id)}
                  className="flex-1"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {session.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(session.timestamp).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                        {session.messages.length} message{session.messages.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    {session.id === currentSessionId && (
                      <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full font-medium">
                        Active
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1 mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onExportSession(session.id);
                    }}
                    className="flex-1 px-2 py-1.5 bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 cursor-pointer"
                    title="Export this chat"
                  >
                    <Download className="w-3 h-3" />
                    Export
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Delete this chat session? This cannot be undone.')) {
                        onDeleteSession(session.id);
                      }
                    }}
                    className="flex-1 px-2 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-700 dark:text-red-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 cursor-pointer"
                    title="Delete this chat"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {sessions.length > 0 && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            💾 Conversations saved locally on your device
          </p>
        </div>
      )}
    </div>
  );
};

export default HistoryPanel;
