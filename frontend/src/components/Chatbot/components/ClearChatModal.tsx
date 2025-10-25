import React from 'react';
import { Trash2 } from 'lucide-react';

interface ClearChatModalProps {
  show: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const ClearChatModal: React.FC<ClearChatModalProps> = ({ show, onConfirm, onCancel }) => {
  if (!show) return null;

  return (
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
              This will start a new conversation. Your current chat will be saved in history, but the main chat area will be cleared.
            </p>
            <div className="flex gap-3">
              <button
                onClick={onCancel}
                className="flex-1 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-xl font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                className="flex-1 px-4 py-2.5 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-xl cursor-pointer"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClearChatModal;
