import React from 'react';
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import ChatMessage from '../ChatMessage';
import SourceArticle from '../SourceArticle';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: any[];
  processing_time?: number;
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  showSources: { [key: string]: boolean };
  onToggleSources: (messageId: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  showSources,
  onToggleSources,
  messagesEndRef,
}) => {
  return (
    <>
      {messages.map((message) => (
        <div key={message.id}>
          <ChatMessage
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="ml-11 mt-2">
              <button
                onClick={() => onToggleSources(message.id)}
                className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mb-2 cursor-pointer"
              >
                {showSources[message.id] ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
                <span>
                  {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                </span>
              </button>

              {showSources[message.id] && (
                <div className="space-y-2 max-w-[70%]">
                  {message.sources.map((source, idx) => (
                    <SourceArticle key={idx} {...source} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Processing time */}
          {message.processing_time && (
            <p className="ml-11 text-xs text-gray-500 mt-1">
              Processed in {message.processing_time.toFixed(2)}s
            </p>
          )}
        </div>
      ))}

      {isLoading && (
        <div className="flex gap-3 mb-4 animate-pulse">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg">
            <Loader2 className="w-5 h-5 text-white animate-spin" />
          </div>
          <div className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 rounded-2xl px-5 py-3 shadow-md">
            <p className="text-sm text-gray-700 dark:text-gray-300 font-medium flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span>
              Analyzing articles...
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">This may take a few seconds</p>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </>
  );
};

export default MessageList;
