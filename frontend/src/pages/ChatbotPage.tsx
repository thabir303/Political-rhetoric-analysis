import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chatbot } from '../components/Chatbot';
import { jsPDF } from 'jspdf';
import { 
  MessageSquarePlus, 
  Trash2, 
  Edit3, 
  Download, 
  ChevronLeft, 
  ChevronRight,
  MessageCircle,
  Check,
  X,
  Search,
  Clock,
  MoreVertical,
  FileText,
  Home,
  Bot
} from 'lucide-react';

// Use the same interface as Chatbot's internal system
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: unknown[];
  processing_time?: number;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  messages: Message[];
}

const ChatbotPage: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showOptionsMenu, setShowOptionsMenu] = useState<string | null>(null);

  // Load chat sessions from localStorage (synced with Chatbot component)
  const loadSessions = useCallback(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    const savedCurrentId = localStorage.getItem('currentSessionId');
    
    if (savedSessions) {
      try {
        const sessions = JSON.parse(savedSessions);
        setChatSessions(sessions);
        if (savedCurrentId) {
          setCurrentSessionId(savedCurrentId);
        } else if (sessions.length > 0) {
          setCurrentSessionId(sessions[0].id);
          localStorage.setItem('currentSessionId', sessions[0].id);
        }
      } catch (error) {
        console.error('Error loading chat sessions:', error);
      }
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Poll for changes from Chatbot component (every 1 second)
  useEffect(() => {
    const interval = setInterval(() => {
      loadSessions();
    }, 1000);
    return () => clearInterval(interval);
  }, [loadSessions]);

  // Create new chat
  const handleNewChat = () => {
    const newSessionId = Date.now().toString();
    localStorage.setItem('currentSessionId', newSessionId);
    setCurrentSessionId(newSessionId);
    loadSessions();
  };

  // Delete chat
  const handleDeleteChat = (sessionId: string) => {
    const updatedSessions = chatSessions.filter(s => s.id !== sessionId);
    setChatSessions(updatedSessions);
    localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
    
    if (currentSessionId === sessionId) {
      if (updatedSessions.length > 0) {
        localStorage.setItem('currentSessionId', updatedSessions[0].id);
        setCurrentSessionId(updatedSessions[0].id);
      } else {
        localStorage.removeItem('currentSessionId');
        setCurrentSessionId('');
      }
    }
    setShowDeleteConfirm(null);
    setShowOptionsMenu(null);
  };

  // Switch to a chat session
  const handleSwitchSession = (sessionId: string) => {
    localStorage.setItem('currentSessionId', sessionId);
    setCurrentSessionId(sessionId);
  };

  // Rename chat
  const handleStartRename = (session: ChatSession) => {
    setEditingSessionId(session.id);
    setEditName(session.title);
    setShowOptionsMenu(null);
  };

  const handleSaveRename = () => {
    if (editingSessionId && editName.trim()) {
      const updatedSessions = chatSessions.map(s =>
        s.id === editingSessionId
          ? { ...s, title: editName.trim() }
          : s
      );
      setChatSessions(updatedSessions);
      localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
    }
    setEditingSessionId(null);
    setEditName('');
  };

  const handleCancelRename = () => {
    setEditingSessionId(null);
    setEditName('');
  };

  // Download chat as Text
  const handleDownloadChatAsText = (session: ChatSession) => {
    let textContent = `Chat: ${session.title}\n`;
    textContent += `Created: ${new Date(session.timestamp).toLocaleString()}\n`;
    textContent += `${'='.repeat(50)}\n\n`;
    
    session.messages.forEach((msg) => {
      textContent += `[${msg.role.toUpperCase()}] ${msg.timestamp ? new Date(msg.timestamp).toLocaleString() : ''}\n`;
      textContent += `${msg.content}\n\n`;
    });

    const dataUri = 'data:text/plain;charset=utf-8,' + encodeURIComponent(textContent);
    const exportFileDefaultName = `${session.title.replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().split('T')[0]}.txt`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    setShowOptionsMenu(null);
  };

  // Download chat as PDF
  const handleDownloadChatAsPDF = (session: ChatSession) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    const maxWidth = pageWidth - 2 * margin;
    let yPosition = margin;

    // Title
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(30, 64, 175); // Blue color
    doc.text('Political Analysis Chat Export', margin, yPosition);
    yPosition += 12;

    // Reset color
    doc.setTextColor(0, 0, 0);

    // Chat title
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Chat:', margin, yPosition);
    doc.setFont('helvetica', 'normal');
    doc.text(session.title || 'Untitled Chat', margin + 15, yPosition);
    yPosition += 8;

    // Date
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text('Date:', margin, yPosition);
    doc.setFont('helvetica', 'normal');
    doc.text(new Date(session.timestamp).toLocaleString(), margin + 15, yPosition);
    yPosition += 6;
    
    doc.setFont('helvetica', 'bold');
    doc.text('Messages:', margin, yPosition);
    doc.setFont('helvetica', 'normal');
    doc.text(String(session.messages.length), margin + 25, yPosition);
    yPosition += 12;

    // Separator line
    doc.setDrawColor(200, 200, 200);
    doc.setLineWidth(0.5);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 12;

    // Messages
    session.messages.forEach((msg) => {
      // Check if we need a new page
      if (yPosition > pageHeight - 50) {
        doc.addPage();
        yPosition = margin;
      }

      // Role header with background
      const isUser = msg.role === 'user';
      const roleText = isUser ? '[YOU]' : '[AI ASSISTANT]';
      
      // Role label
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(isUser ? 37 : 22, isUser ? 99 : 163, isUser ? 235 : 74); // Blue for user, Green for AI
      doc.text(roleText, margin, yPosition);
      
      // Timestamp
      if (msg.timestamp) {
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(128, 128, 128);
        const timestampX = isUser ? margin + 25 : margin + 55;
        doc.text(new Date(msg.timestamp).toLocaleString(), timestampX, yPosition);
      }
      yPosition += 8;

      // Message content - wrap text
      doc.setTextColor(50, 50, 50);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      const lines = doc.splitTextToSize(msg.content, maxWidth);
      
      lines.forEach((line: string) => {
        if (yPosition > pageHeight - 25) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(line, margin, yPosition);
        yPosition += 5;
      });

      yPosition += 10;
      
      // Add separator between messages
      doc.setDrawColor(230, 230, 230);
      doc.setLineWidth(0.2);
      doc.line(margin, yPosition - 5, pageWidth - margin, yPosition - 5);
    });

    // Footer
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(128, 128, 128);
      doc.setFont('helvetica', 'italic');
      doc.text('Generated by Political Analysis Chatbot', margin, pageHeight - 10);
      doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin - 25, pageHeight - 10);
    }

    // Save
    const fileName = `${(session.title || 'chat').replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    setShowOptionsMenu(null);
  };

  // Filter sessions by search
  const filteredSessions = chatSessions.filter(session =>
    session.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.messages.some(m => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex h-screen bg-[#0f172a] overflow-hidden">
      {/* Sidebar */}
      <div 
        className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 ease-in-out flex-shrink-0 overflow-hidden`}
      >
        <div className="h-full w-80 bg-[#1e293b] border-r border-gray-700/50 shadow-xl flex flex-col">
          {/* Sidebar Header with Home Navigation */}
          <div className="p-4 border-b border-gray-700/50">
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-3 py-2 bg-gray-700/50 hover:bg-gray-600/50 text-gray-300 hover:text-white rounded-lg transition-all duration-200 cursor-pointer"
              >
                <Home className="w-4 h-4" />
                <span className="text-sm font-medium">Home</span>
              </button>
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-blue-400" />
                <span className="text-white font-semibold">Chat AI</span>
              </div>
            </div>
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
            >
              <MessageSquarePlus className="w-5 h-5" />
              New Chat
            </button>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-gray-700/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-800/80 border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 placeholder-gray-500"
              />
            </div>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto p-2">
            {filteredSessions.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No chats yet</p>
                <p className="text-xs mt-1 text-gray-500">Start a new conversation!</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`group relative rounded-xl transition-all duration-200 ${
                      currentSessionId === session.id
                        ? 'bg-blue-600/20 border border-blue-500/50 shadow-md'
                        : 'hover:bg-gray-700/50 border border-transparent hover:border-gray-600/50'
                    }`}
                  >
                    {editingSessionId === session.id ? (
                      // Rename input
                      <div className="flex items-center gap-2 p-3">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename();
                            if (e.key === 'Escape') handleCancelRename();
                          }}
                          className="flex-1 px-2 py-1 text-sm bg-gray-800 border border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-200"
                          autoFocus
                        />
                        <button
                          onClick={handleSaveRename}
                          className="p-1 text-green-400 hover:bg-green-900/50 rounded-lg cursor-pointer"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleCancelRename}
                          className="p-1 text-red-400 hover:bg-red-900/50 rounded-lg cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      // Normal display
                      <div
                        className="flex items-center p-3 cursor-pointer"
                        onClick={() => handleSwitchSession(session.id)}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-200 truncate">
                            {session.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <Clock className="w-3 h-3 text-gray-500" />
                            <span className="text-xs text-gray-400">
                              {formatDate(session.timestamp)}
                            </span>
                            <span className="text-xs text-gray-500">
                              • {session.messages.length} messages
                            </span>
                          </div>
                        </div>
                        
                        {/* Options button */}
                        <div className="relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowOptionsMenu(showOptionsMenu === session.id ? null : session.id);
                            }}
                            className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-600/50 rounded-lg transition-all cursor-pointer"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>

                          {/* Options dropdown */}
                          {showOptionsMenu === session.id && (
                            <>
                              {/* Backdrop to close menu */}
                              <div 
                                className="fixed inset-0 z-[99]"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setShowOptionsMenu(null);
                                }}
                              />
                              <div 
                                className="absolute right-0 top-8 w-48 bg-gray-800 rounded-xl shadow-2xl border border-gray-600/50 py-2 z-[100]"
                              >
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleStartRename(session);
                                  }}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 cursor-pointer"
                                >
                                  <Edit3 className="w-4 h-4" />
                                  Rename
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadChatAsPDF(session);
                                  }}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 cursor-pointer"
                                >
                                  <FileText className="w-4 h-4" />
                                  Download PDF
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadChatAsText(session);
                                  }}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 cursor-pointer"
                                >
                                  <Download className="w-4 h-4" />
                                  Download Text
                                </button>
                                <hr className="my-2 border-gray-700" />
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setShowDeleteConfirm(session.id);
                                    setShowOptionsMenu(null);
                                  }}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-red-900/30 cursor-pointer"
                                >
                                  <Trash2 className="w-4 h-4" />
                                  Delete
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Delete confirmation */}
                    {showDeleteConfirm === session.id && (
                      <div className="absolute inset-0 bg-gray-800/95 backdrop-blur-sm rounded-xl flex items-center justify-center gap-2 z-40">
                        <span className="text-sm text-gray-300">Delete?</span>
                        <button
                          onClick={() => handleDeleteChat(session.id)}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 cursor-pointer"
                        >
                          Yes
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(null)}
                          className="px-3 py-1 bg-gray-600 text-gray-200 text-sm rounded-lg hover:bg-gray-500 cursor-pointer"
                        >
                          No
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-gray-700/50 text-center">
            <p className="text-xs text-gray-500">
              {chatSessions.length} chat{chatSessions.length !== 1 ? 's' : ''} • 
              {chatSessions.reduce((acc, s) => acc + s.messages.length, 0)} messages
            </p>
          </div>
        </div>
      </div>

      {/* Sidebar Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute left-0 top-1/2 transform -translate-y-1/2 z-50 bg-gray-800/90 backdrop-blur-sm border border-gray-600/50 rounded-r-xl p-2 shadow-lg hover:shadow-xl hover:bg-gray-700/90 transition-all cursor-pointer"
        style={{ left: sidebarOpen ? '318px' : '0px' }}
      >
        {sidebarOpen ? <ChevronLeft className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
      </button>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Chatbot */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full">
            <Chatbot
              key={currentSessionId}
              apiUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}
              isOpen={true}
              embedded={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;
