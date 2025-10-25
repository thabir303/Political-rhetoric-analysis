import React from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  input: string;
  isLoading: boolean;
  messagesCount: number;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  isLoading,
  messagesCount,
  onInputChange,
  onSend,
  onKeyPress,
}) => {
  return (
    <div className="border-t-2 border-gray-200 dark:border-gray-700 p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 rounded-b-2xl">
      <div className="flex gap-3">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder="💬 Ask me anything about Bangladesh politics... (Press Enter to send)"
          className="flex-1 resize-none rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
          rows={2}
          disabled={isLoading}
        />
        <button
          onClick={onSend}
          disabled={!input.trim() || isLoading}
          className="self-end px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:via-blue-800 hover:to-indigo-800 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-xl transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none cursor-pointer disabled:cursor-not-allowed"
          title={input.trim() ? 'Send message' : 'Type something to send'}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      <div className="flex items-center justify-between mt-3">
        <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
          AI-powered • {messagesCount} message{messagesCount !== 1 ? 's' : ''}
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          🌐 English & বাংলা supported
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
