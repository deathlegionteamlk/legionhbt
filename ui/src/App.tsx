import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { ThemeProvider } from './hooks/useTheme';
import { Conversation, SystemMode, SystemStatus } from './types';
import { v4 as uuidv4 } from 'uuid';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8080';

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    agent: false,
    model: false,
    rag: false,
    sandbox: false,
    evolution: false
  });
  const [currentMode, setCurrentMode] = useState<SystemMode>('agent');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: uuidv4(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      mode: currentMode
    };
    setConversations([newConversation, ...conversations]);
    setCurrentConversation(newConversation);
  };

  const selectConversation = (conversation: Conversation) => {
    setCurrentConversation(conversation);
    setCurrentMode(conversation.mode);
  };

  const deleteConversation = (id: string) => {
    setConversations(conversations.filter(c => c.id !== id));
    if (currentConversation?.id === id) {
      setCurrentConversation(null);
    }
  };

  const updateConversation = (updated: Conversation) => {
    setConversations(conversations.map(c => c.id === updated.id ? updated : c));
    if (currentConversation?.id === updated.id) {
      setCurrentConversation(updated);
    }
  };

  return (
    <ThemeProvider>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar
          conversations={conversations}
          currentConversation={currentConversation}
          onSelect={selectConversation}
          onDelete={deleteConversation}
          onNew={createNewConversation}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
        
        <div className="flex-1 flex flex-col min-w-0">
          <Header
            systemStatus={systemStatus}
            currentMode={currentMode}
            onModeChange={setCurrentMode}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />
          
          <main className="flex-1 overflow-hidden">
            {currentConversation ? (
              <Chat
                conversation={currentConversation}
                onUpdate={updateConversation}
                apiBase={API_BASE}
                mode={currentMode}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
                    Welcome to LEGIONHBT
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400 mb-6">
                    Select a conversation or start a new one
                  </p>
                  <button
                    onClick={createNewConversation}
                    className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    New Conversation
                  </button>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;
