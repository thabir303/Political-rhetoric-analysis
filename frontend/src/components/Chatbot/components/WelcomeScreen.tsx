import React from 'react';
import { MessageSquare } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectExample: (example: string) => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectExample }) => {
  const exampleQueries = [
    {
      emoji: '🏛️',
      text: 'Who are the main political actors regarding the 2026 election?',
    },
    {
      emoji: '🔒',
      text: 'What are the current security risks during election period?',
    },
    {
      emoji: '⚖️',
      text: 'Tell me about political reforms in Bangladesh',
    },
  ];

  return (
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
      <div className="mt-8 space-y-3 max-w-md mx-auto">
        <p className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide flex items-center justify-center gap-2">
          <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
          Popular Questions
          <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
        </p>
        {exampleQueries.map((query, index) => (
          <button
            key={index}
            onClick={() => onSelectExample(query.text)}
            className="group block w-full text-left text-sm bg-white dark:bg-gray-800 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-gray-700 dark:hover:to-gray-600 rounded-xl px-5 py-4 transition-all duration-300 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 shadow-sm hover:shadow-lg cursor-pointer transform hover:-translate-y-0.5"
          >
            <div className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400 text-lg group-hover:scale-125 transition-transform duration-200">
                {query.emoji}
              </span>
              <span className="flex-1 text-gray-800 dark:text-gray-200 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                {query.text}
              </span>
            </div>
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-400 dark:text-gray-600 mt-8 italic">
        💡 Tip: You can ask in English or বাংলা!
      </p>
    </div>
  );
};

export default WelcomeScreen;
