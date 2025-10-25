import React, { useState, useRef, useEffect } from 'react';
import { Send, X, MessageSquare, Loader2, ChevronDown, ChevronUp, Maximize2, Minimize2, Trash2 } from 'lucide-react';
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
  const [showClearModal, setShowClearModal] = useState(false);
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

  const handleClearChat = () => {
    setShowClearModal(true);
  };

  const confirmClearChat = () => {
    setMessages([]);
    setShowSources({});
    setShowClearModal(false);
  };

  const cancelClearChat = () => {
    setShowClearModal(false);
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
        className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:via-blue-800 hover:to-indigo-800 text-white rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 z-50 cursor-pointer hover:scale-110 animate-bounce"
        title="Open Political Analysis AI Chat"
      >
        <MessageSquare className="w-7 h-7" />
      </button>
    );
  }

  const chatContent = (
    <>
      {/* Clear Chat Modal */}
      {showClearModal && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[60] rounded-2xl">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-md mx-4 transform transition-all duration-300 scale-100">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Clear All Messages?
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  This will permanently delete all your chat messages and conversation history. This action cannot be undone.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={cancelClearChat}
                    className="flex-1 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-xl font-medium transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmClearChat}
                    className="flex-1 px-4 py-2.5 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-xl cursor-pointer"
                  >
                    Clear All
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
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
          {!embedded && (
            <>
              <button
                onClick={handleClearChat}
                className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
                title="Clear Chat"
              >
                <Trash2 className="w-5 h-5" />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
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
                className="hover:bg-white/20 p-2.5 rounded-lg transition-all duration-200 cursor-pointer hover:scale-110"
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
          <div className="text-center text-gray-500 mt-8 px-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-lg animate-pulse">
              <MessageSquare className="w-10 h-10 text-white" />
            </div>
            <h4 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Welcome! 👋
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 max-w-sm mx-auto leading-relaxed">
              I'm your AI assistant for Bangladesh political analysis. Ask me anything!
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mb-6 italic">
              Powered by advanced AI • Analyzing real news articles
            </p>
            <div className="mt-8 space-y-3 max-w-md mx-auto">
              <p className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide flex items-center justify-center gap-2">
                <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                Popular Questions
                <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
              </p>
              <button
                onClick={() => setInput('Who are the main political actors regarding the 2026 election?')}
                className="group block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-gray-700 dark:hover:to-gray-600 rounded-xl px-5 py-4 transition-all duration-300 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 shadow-sm hover:shadow-lg cursor-pointer transform hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-3">
                  <span className="text-blue-600 dark:text-blue-400 text-lg group-hover:scale-125 transition-transform duration-200">🏛️</span>
                  <span className="flex-1 text-gray-800 dark:text-gray-200 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                    Who are the main political actors regarding the 2026 election?
                  </span>
                </div>
              </button>
              <button
                onClick={() => setInput('What are the current security risks during election period?')}
                className="group block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-gray-700 dark:hover:to-gray-600 rounded-xl px-5 py-4 transition-all duration-300 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 shadow-sm hover:shadow-lg cursor-pointer transform hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-3">
                  <span className="text-blue-600 dark:text-blue-400 text-lg group-hover:scale-125 transition-transform duration-200">🔒</span>
                  <span className="flex-1 text-gray-800 dark:text-gray-200 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                    What are the current security risks during election period?
                  </span>
                </div>
              </button>
              <button
                onClick={() => setInput('Tell me about political reforms in Bangladesh')}
                className="group block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-gray-700 dark:hover:to-gray-600 rounded-xl px-5 py-4 transition-all duration-300 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 shadow-sm hover:shadow-lg cursor-pointer transform hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-3">
                  <span className="text-blue-600 dark:text-blue-400 text-lg group-hover:scale-125 transition-transform duration-200">⚖️</span>
                  <span className="flex-1 text-gray-800 dark:text-gray-200 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                    Tell me about political reforms in Bangladesh
                  </span>
                </div>
              </button>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-600 mt-8 italic">
              💡 Tip: You can ask in English or বাংলা!
            </p>
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
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {/* Input Area */}
      <div className="border-t-2 border-gray-200 dark:border-gray-700 p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 rounded-b-2xl">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="💬 Ask me anything about Bangladesh politics... (Press Enter to send)"
            className="flex-1 resize-none rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="self-end px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:via-blue-800 hover:to-indigo-800 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-xl transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none cursor-pointer disabled:cursor-not-allowed"
            title={input.trim() ? "Send message" : "Type something to send"}
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
            AI-powered • {messages.length} message{messages.length !== 1 ? 's' : ''}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 italic">
            🌐 English & বাংলা supported
          </p>
        </div>
      </div>
    </>
  );

  if (embedded) {
    return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-2xl border-2 border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
        {chatContent}
      </div>
    );
  }

  // Floating chatbot with expand/collapse
  const chatboxClasses = isExpanded
    ? "fixed inset-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700"
    : "fixed bottom-6 right-6 w-[520px] h-[700px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700";

  return (
    <div className={chatboxClasses} style={{ transition: 'all 0.3s ease-in-out' }}>
      {chatContent}
    </div>
  );
};

export default Chatbot;
