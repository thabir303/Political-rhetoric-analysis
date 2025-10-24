import React from 'react';
import { Chatbot } from '../components/Chatbot';

const ChatbotPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Political Analysis Chatbot
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Ask questions about Bangladesh politics and get AI-powered answers based on our article database
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg" style={{ height: 'calc(100vh - 200px)' }}>
          <Chatbot
            apiUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}
            isOpen={true}
            embedded={true}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;
