import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare } from 'lucide-react';
import ChatHeader from './components/ChatHeader';
import ClearChatModal from './components/ClearChatModal';
import HistoryPanel from './components/HistoryPanel';
import WelcomeScreen from './components/WelcomeScreen';
import MessageList from './components/MessageList';
import ChatInput from './components/ChatInput';
import type { Message, ChatSession } from './utils/chatUtils';
import {
  loadChatSessions,
  saveChatSessions,
  getCurrentSessionId,
  setCurrentSessionId as saveCurrentSessionId,
  createNewSession,
  exportChatSession,
  updateSessionInList,
  createSessionTitle,
} from './utils/chatUtils';
import { getAuthHeader } from '../../utils/auth';

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
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;

  // Load chat history from localStorage on mount
  useEffect(() => {
    const sessions = loadChatSessions();
    setChatSessions(sessions);

    const savedCurrentSession = getCurrentSessionId();
    if (savedCurrentSession) {
      setCurrentSessionId(savedCurrentSession);
      const currentSession = sessions.find((s) => s.id === savedCurrentSession);
      if (currentSession) {
        setMessages(currentSession.messages);
      }
    } else {
      const newSessionId = createNewSession();
      setCurrentSessionId(newSessionId);
    }
  }, []);

  // Save messages to current session whenever they change
  useEffect(() => {
    if (messages.length > 0 && currentSessionId) {
      const sessionTitle = createSessionTitle(messages[0]?.content);
      const currentSession: ChatSession = {
        id: currentSessionId,
        title: sessionTitle,
        timestamp: new Date().toISOString(),
        messages: messages,
      };

      const updatedSessions = updateSessionInList(chatSessions, currentSession);
      setChatSessions(updatedSessions);
      saveChatSessions(updatedSessions);
    }
  }, [messages, currentSessionId]);

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
      const authHeaders = getAuthHeader();
      const response = await fetch(`${apiUrl}/chatbot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({
          query: input,
          top_k: 20,  // Increased from 10 to 20 to show more sources
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

  const handleNewChat = () => {
    // Save current chat if it has messages
    if (messages.length > 0) {
      // Already saved via useEffect
    }
    // Create new session
    const newSessionId = createNewSession();
    setCurrentSessionId(newSessionId);
    setMessages([]);
    setShowSources({});
    setShowHistoryPanel(false);
  };

  const handleClearChat = () => {
    setShowClearModal(true);
  };

  const confirmClearChat = () => {
    handleNewChat(); // Use the new chat handler
    setShowClearModal(false);
  };

  const cancelClearChat = () => {
    setShowClearModal(false);
  };

  const loadChatSession = (sessionId: string) => {
    const session = chatSessions.find((s) => s.id === sessionId);
    if (session) {
      setMessages(session.messages);
      setCurrentSessionId(sessionId);
      saveCurrentSessionId(sessionId);
      setShowHistoryPanel(false);
    }
  };

  const deleteChatSession = (sessionId: string) => {
    const updatedSessions = chatSessions.filter((s) => s.id !== sessionId);
    setChatSessions(updatedSessions);
    saveChatSessions(updatedSessions);

    // If deleting current session, create new one
    if (sessionId === currentSessionId) {
      handleNewChat();
    }
  };

  const handleExportSession = (sessionId: string) => {
    const session = chatSessions.find((s) => s.id === sessionId);
    if (session) {
      exportChatSession(session);
    }
  };

  const handleExportCurrentChat = () => {
    if (currentSessionId) {
      handleExportSession(currentSessionId);
    }
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
      <ClearChatModal
        show={showClearModal}
        onConfirm={confirmClearChat}
        onCancel={cancelClearChat}
      />

      {/* Header */}
      <ChatHeader
        embedded={embedded}
        isExpanded={isExpanded}
        chatSessionsCount={chatSessions.length}
        messagesCount={messages.length}
        onToggleHistory={() => setShowHistoryPanel(!showHistoryPanel)}
        onExportChat={handleExportCurrentChat}
        onClearChat={handleClearChat}
        onNewChat={handleNewChat}
        onToggleExpand={!embedded ? () => setIsExpanded(!isExpanded) : undefined}
        onClose={!embedded ? handleClose : undefined}
      />

      {/* History Panel */}
      <HistoryPanel
        show={showHistoryPanel}
        sessions={chatSessions}
        currentSessionId={currentSessionId}
        onClose={() => setShowHistoryPanel(false)}
        onLoadSession={loadChatSession}
        onExportSession={handleExportSession}
        onDeleteSession={deleteChatSession}
      />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
        {messages.length === 0 ? (
          <WelcomeScreen onSelectExample={setInput} />
        ) : (
          <MessageList
            messages={messages}
            isLoading={isLoading}
            showSources={showSources}
            onToggleSources={toggleSources}
            messagesEndRef={messagesEndRef}
          />
        )}
      </div>

      {/* Input Area */}
      <ChatInput
        input={input}
        isLoading={isLoading}
        messagesCount={messages.length}
        onInputChange={setInput}
        onSend={handleSendMessage}
        onKeyPress={handleKeyPress}
      />
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
    ? 'fixed inset-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700'
    : 'fixed bottom-6 right-6 w-[520px] h-[700px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700';

  return (
    <div className={chatboxClasses} style={{ transition: 'all 0.3s ease-in-out' }}>
      {chatContent}
    </div>
  );
};

export default Chatbot;
