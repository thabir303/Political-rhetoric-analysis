export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: any[];
  processing_time?: number;
}

export interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  messages: Message[];
}

export const loadChatSessions = (): ChatSession[] => {
  const savedSessions = localStorage.getItem('chatSessions');
  if (savedSessions) {
    try {
      return JSON.parse(savedSessions);
    } catch (error) {
      console.error('Error loading chat history:', error);
      return [];
    }
  }
  return [];
};

export const saveChatSessions = (sessions: ChatSession[]): void => {
  localStorage.setItem('chatSessions', JSON.stringify(sessions));
};

export const getCurrentSessionId = (): string => {
  return localStorage.getItem('currentSessionId') || '';
};

export const setCurrentSessionId = (sessionId: string): void => {
  localStorage.setItem('currentSessionId', sessionId);
};

export const createNewSession = (): string => {
  const newSessionId = Date.now().toString();
  setCurrentSessionId(newSessionId);
  return newSessionId;
};

export const exportChatSession = (session: ChatSession): void => {
  const exportLines = [
    '═══════════════════════════════════════════════════════════',
    '         POLITICAL ANALYSIS AI - CHAT EXPORT',
    '═══════════════════════════════════════════════════════════',
    '',
    `Session Title: ${session.title}`,
    `Date: ${new Date(session.timestamp).toLocaleString('en-US', {
      dateStyle: 'full',
      timeStyle: 'long',
    })}`,
    `Total Messages: ${session.messages.length}`,
    '',
    '═══════════════════════════════════════════════════════════',
    'CONVERSATION',
    '═══════════════════════════════════════════════════════════',
    '',
  ];

  session.messages.forEach((msg) => {
    const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    exportLines.push('');
    exportLines.push(`[${msg.role === 'user' ? 'YOU' : 'AI'}] ${time}`);
    exportLines.push('─'.repeat(60));
    exportLines.push(msg.content);

    if (msg.sources && msg.sources.length > 0) {
      exportLines.push('');
      exportLines.push(`📚 SOURCES (${msg.sources.length}):`);
      msg.sources.forEach((source, idx) => {
        exportLines.push(`  ${idx + 1}. ${source.title}`);
        exportLines.push(`     Date: ${source.date}`);
        exportLines.push(`     Source: ${source.source}`);
        if (source.url) {
          exportLines.push(`     URL: ${source.url}`);
        }
        if (source.relevance_score) {
          exportLines.push(`     Relevance: ${(source.relevance_score * 100).toFixed(1)}%`);
        }
      });
    }

    if (msg.processing_time) {
      exportLines.push(`⏱️  Processing Time: ${msg.processing_time.toFixed(2)}s`);
    }
  });

  exportLines.push('');
  exportLines.push('');
  exportLines.push('═══════════════════════════════════════════════════════════');
  exportLines.push('           END OF CONVERSATION');
  exportLines.push('═══════════════════════════════════════════════════════════');
  exportLines.push('');
  exportLines.push('Exported from Political Analysis AI');
  exportLines.push(`Export Date: ${new Date().toLocaleString()}`);

  const exportText = exportLines.join('\n');
  const blob = new Blob([exportText], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const filename = `chat-export-${new Date(session.timestamp).toISOString().split('T')[0]}-${session.id.slice(-6)}.txt`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const updateSessionInList = (
  sessions: ChatSession[],
  currentSession: ChatSession
): ChatSession[] => {
  const updatedSessions = sessions.filter((s) => s.id !== currentSession.id);
  updatedSessions.unshift(currentSession);
  return updatedSessions;
};

export const createSessionTitle = (firstMessage: string): string => {
  return firstMessage.substring(0, 50) + (firstMessage.length > 50 ? '...' : '');
};
