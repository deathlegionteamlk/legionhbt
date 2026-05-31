import React from 'react';
import { Plus, Trash2, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react';
import { Conversation } from '../types';

interface SidebarProps {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  onSelect: (conversation: Conversation) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  currentConversation,
  onSelect,
  onDelete,
  onNew,
  isOpen,
  onToggle
}) => {
  const getModeColor = (mode: string) => {
    const colors: Record<string, string> = {
      agent: 'bg-blue-500',
      model: 'bg-green-500',
      rag: 'bg-purple-500',
      sandbox: 'bg-orange-500',
      evolution: 'bg-pink-500'
    };
    return colors[mode] || 'bg-gray-500';
  };

  return (
    <>
      <div className={`fixed inset-y-0 left-0 z-50 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } w-80`}>
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={onNew}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>New Conversation</span>
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onSelect(conversation)}
                className={`group flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors ${
                  currentConversation?.id === conversation.id
                    ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${getModeColor(conversation.mode)}`} />
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {conversation.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(conversation.updatedAt).toLocaleDateString()}
                  </p>
                </div>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conversation.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            
            {conversations.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No conversations yet</p>
              </div>
            )}
          </div>
          
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
              LEGIONHBT v1.0.0
            </div>
          </div>
        </div>
      </div>
      
      <button
        onClick={onToggle}
        className={`fixed top-4 z-50 p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg transition-all duration-300 ${
          isOpen ? 'left-[328px]' : 'left-4'
        }`}
      >
        {isOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
      </button>
    </>
  );
};

export default Sidebar;
