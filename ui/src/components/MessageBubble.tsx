import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, AlertCircle, FileText, Download } from 'lucide-react';
import { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  const getIcon = () => {
    if (isUser) return <User className="w-5 h-5" />;
    if (isSystem) return <AlertCircle className="w-5 h-5" />;
    return <Bot className="w-5 h-5" />;
  };

  const getContainerClasses = () => {
    if (isUser) return 'bg-primary-600 text-white';
    if (isSystem) return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
    return 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700';
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} message-enter`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className={`flex items-start space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-primary-700 text-white' : 
            isSystem ? 'bg-red-500 text-white' : 
            'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}>
            {getIcon()}
          </div>
          
          <div className={`rounded-2xl px-4 py-3 ${getContainerClasses()} ${
            isUser ? 'rounded-tr-sm' : 'rounded-tl-sm'
          }`}>
            {message.attachments && message.attachments.length > 0 && (
              <div className="mb-2 space-y-2">
                {message.attachments.map((attachment) => (
                  <div
                    key={attachment.id}
                    className="flex items-center space-x-2 p-2 rounded bg-black/10 dark:bg-white/10"
                  >
                    <FileText className="w-4 h-4" />
                    <span className="text-sm truncate max-w-[200px]">{attachment.name}</span>
                    <a
                      href={attachment.url}
                      download
                      className="p-1 hover:bg-black/20 dark:hover:bg-white/20 rounded"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                ))}
              </div>
            )}
            
            <div className={`prose prose-sm max-w-none ${
              isUser ? 'prose-invert' : 'dark:prose-invert'
            }`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
            
            {isStreaming && (
              <span className="typing-indicator inline-block w-2 h-4 bg-current ml-1" />
            )}
          </div>
        </div>
        
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
