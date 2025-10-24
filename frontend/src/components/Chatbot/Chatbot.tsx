import React, { useState, useRef, useEffect } from 'react';
import { Send, X, MessageSquare, Loader2, ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';
import ChatMessage from './ChatMessage';
import SourceArticle from './SourceArticle';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SourceArticle[];
  processing_time?: number;
}

interface SourceArticle {
  title: string;
  date: string;
  source: string;
  url?: string;
  relevance_score?: number;
}

interface ChatbotProps {
  apiUrl?: string;
  isOpen?: boolean;
  onClose?: () => void;
  embedded?: boolean;
}

const Chatbot: React.FC<ChatbotProps> = ({
  apiUrl = 'http://localhost:8000/api/v1',
  isOpen: controlledIsOpen,
  onClose,
  embedded = false,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSources, setShowSources] = useState<{ [key: string]: boolean }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/chatbot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          top_k: 20,
          include_sources: true,
          language: null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from chatbot');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        sources: data.sources || [],
        processing_time: data.processing_time,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleSources = (messageId: string) => {
    setShowSources((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      setInternalIsOpen(false);
    }
  };

  if (!isOpen && !embedded) {
    return (
      <button
        onClick={() => setInternalIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all z-50"
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    );
  }

  const chatContent = (
    <>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">Political Analysis AI</h3>
            <p className="text-xs text-blue-100">Powered by gpt-4o-mini</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!embedded && (
            <>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="hover:bg-white/20 p-2 rounded transition-colors"
                title={isExpanded ? "Minimize" : "Maximize"}
              >
                {isExpanded ? (
                  <Minimize2 className="w-5 h-5" />
                ) : (
                  <Maximize2 className="w-5 h-5" />
                )}
              </button>
              <button
                onClick={handleClose}
                className="hover:bg-white/20 p-2 rounded transition-colors"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Welcome to Political Analysis AI
            </h4>
            <p className="text-sm mb-6">Ask me anything about Bangladesh politics!</p>
            <div className="mt-6 space-y-3 max-w-md mx-auto">
              <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Try asking:</p>
              <button
                onClick={() => setInput('Who are the main political actors regarding the 2026 election?')}
                className="block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-xl px-4 py-3 transition-all border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 shadow-sm hover:shadow-md"
              >
                <span className="text-blue-600 dark:text-blue-400 mr-2">→</span>
                Who are the main political actors regarding the 2026 election?
              </button>
              <button
                onClick={() => setInput('What are the current security risks during election period?')}
                className="block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-xl px-4 py-3 transition-all border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 shadow-sm hover:shadow-md"
              >
                <span className="text-blue-600 dark:text-blue-400 mr-2">→</span>
                What are the current security risks during election period?
              </button>
              <button
                onClick={() => setInput('Tell me about political reforms in Bangladesh')}
                className="block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-xl px-4 py-3 transition-all border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 shadow-sm hover:shadow-md"
              >
                <span className="text-blue-600 dark:text-blue-400 mr-2">→</span>
                Tell me about political reforms in Bangladesh
              </button>
            </div>
          </div>
        ) : (
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
                      onClick={() => toggleSources(message.id)}
                      className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mb-2"
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
              <div className="flex gap-3 mb-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Thinking...</p>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question here... (Press Enter to send)"
            className="flex-1 resize-none rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-gray-100 placeholder-gray-400"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="self-end px-5 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-xl transition-all flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          AI-powered analysis • {messages.length} messages
        </p>
      </div>
    </>
  );

  if (embedded) {
    return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 shadow-xl">
        {chatContent}
      </div>
    );
  }

  // Floating chatbot with expand/collapse
  const chatboxClasses = isExpanded
    ? "fixed inset-4 bg-white dark:bg-gray-900 rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700"
    : "fixed bottom-6 right-6 w-[440px] h-[680px] bg-white dark:bg-gray-900 rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700";

  return (
    <div className={chatboxClasses} style={{ transition: 'all 0.3s ease-in-out' }}>
      {chatContent}
    </div>
  );
};

export default Chatbot;
