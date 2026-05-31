import React from 'react';
import { Sun, Moon, Activity, Terminal, Cpu, Database, Box, GitBranch } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';
import { SystemStatus, SystemMode } from '../types';

interface HeaderProps {
  systemStatus: SystemStatus;
  currentMode: SystemMode;
  onModeChange: (mode: SystemMode) => void;
  onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({
  systemStatus,
  currentMode,
  onModeChange,
  onToggleSidebar
}) => {
  const { theme, toggleTheme } = useTheme();

  const modes: { id: SystemMode; label: string; icon: React.ReactNode }[] = [
    { id: 'agent', label: 'Agent', icon: <Terminal className="w-4 h-4" /> },
    { id: 'model', label: 'Model', icon: <Cpu className="w-4 h-4" /> },
    { id: 'rag', label: 'RAG', icon: <Database className="w-4 h-4" /> },
    { id: 'sandbox', label: 'Sandbox', icon: <Box className="w-4 h-4" /> },
    { id: 'evolution', label: 'Evolution', icon: <GitBranch className="w-4 h-4" /> }
  ];

  return (
    <header className="h-16 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex items-center justify-between px-4">
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          LEGIONHBT
        </h1>
        
        <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />
        
        <div className="flex items-center space-x-1">
          {modes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => onModeChange(mode.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                currentMode === mode.id
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {mode.icon}
              <span className="capitalize">{mode.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          {Object.entries(systemStatus).map(([key, status]) => (
            <div
              key={key}
              className={`w-2 h-2 rounded-full ${
                status ? 'bg-green-500' : 'bg-red-500'
              }`}
              title={`${key}: ${status ? 'online' : 'offline'}`}
            />
          ))}
        </div>
        
        <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />
        
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </header>
  );
};

export default Header;
