import React from 'react';
import { MessageSquare, X, Maximize2, Minimize2, Trash2, Download, History, Plus } from 'lucide-react';

interface ChatHeaderProps {
  embedded?: boolean;
  isExpanded?: boolean;
  chatSessionsCount: number;
  messagesCount: number;
  onToggleHistory: () => void;
  onExportChat: () => void;
  onClearChat: () => void;
  onNewChat: () => void;
  onToggleExpand?: () => void;
  onClose?: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  embedded = false,
  isExpanded = false,
  chatSessionsCount,
  messagesCount,
  onToggleHistory,
  onExportChat,
  onClearChat,
  onNewChat,
  onToggleExpand,
  onClose,
}) => {
  return (
    <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white p-5 flex items-center justify-between shadow-lg rounded-t-2xl">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-md">
          <MessageSquare className="w-7 h-7" />
        </div>
        <div>
          <h3 className="font-bold text-xl tracking-tight">Political Analysis AI</h3>
          <p className="text-xs text-blue-100 mt-0.5 flex items-center gap-1">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            Ask me anything about Bangladesh politics
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110 relative group"
          title="New Chat"
        >
          <Plus className="w-5 h-5" />
          <span className="absolute -bottom-8 right-0 bg-black/75 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            New Chat
          </span>
        </button>

        {/* History Button */}
        <button
          onClick={onToggleHistory}
          className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110 relative"
          title="Chat History"
        >
          <History className="w-5 h-5" />
          {chatSessionsCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
              {chatSessionsCount}
            </span>
          )}
        </button>

        {/* Export Button */}
        <button
          onClick={onExportChat}
          disabled={messagesCount === 0}
          className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Export Current Chat"
        >
          <Download className="w-5 h-5" />
        </button>

        {/* Clear Chat Button */}
        <button
          onClick={onClearChat}
          className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
          title="Clear Chat"
        >
          <Trash2 className="w-5 h-5" />
        </button>

        {/* Maximize/Minimize Button (only for non-embedded) */}
        {!embedded && onToggleExpand && (
          <button
            onClick={onToggleExpand}
            className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
            title={isExpanded ? "Minimize" : "Maximize"}
          >
            {isExpanded ? (
              <Minimize2 className="w-5 h-5" />
            ) : (
              <Maximize2 className="w-5 h-5" />
            )}
          </button>
        )}

        {/* Close Button (only for non-embedded) */}
        {!embedded && onClose && (
          <button
            onClick={onClose}
            className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatHeader;
