import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Loader2 } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { Conversation, Message, Attachment, SystemMode } from '../types';
import MessageBubble from './MessageBubble';
import { v4 as uuidv4 } from 'uuid';

interface ChatProps {
  conversation: Conversation;
  onUpdate: (conversation: Conversation) => void;
  apiBase: string;
  mode: SystemMode;
}

const Chat: React.FC<ChatProps> = ({ conversation, onUpdate, apiBase, mode }) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileDrop,
    noClick: true
  });

  useEffect(() => {
    scrollToBottom();
  }, [conversation.messages, streamingContent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  async function handleFileDrop(acceptedFiles: File[]) {
    const attachments: Attachment[] = [];
    
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await fetch(`${apiBase}/api/upload`, {
          method: 'POST',
          body: formData
        });
        const data = await response.json();
        
        if (data.success) {
          attachments.push({
            id: data.fileId,
            name: file.name,
            type: file.type,
            size: file.size,
            url: data.url
          });
        }
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
    
    if (attachments.length > 0) {
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: `Uploaded ${attachments.length} file(s)`,
        timestamp: new Date().toISOString(),
        attachments
      };
      
      const updated = {
        ...conversation,
        messages: [...conversation.messages, userMessage],
        updatedAt: new Date().toISOString()
      };
      onUpdate(updated);
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    const updatedConversation = {
      ...conversation,
      messages: [...conversation.messages, userMessage],
      updatedAt: new Date().toISOString()
    };
    
    onUpdate(updatedConversation);
    setInput('');
    setIsLoading(true);
    setStreamingContent('');

    try {
      const response = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          conversationId: conversation.id,
          mode: mode,
          history: conversation.messages.slice(-10)
        })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                setStreamingContent('');
                const assistantMessage: Message = {
                  id: uuidv4(),
                  role: 'assistant',
                  content: fullContent,
                  timestamp: new Date().toISOString()
                };
                
                onUpdate({
                  ...updatedConversation,
                  messages: [...updatedConversation.messages, assistantMessage],
                  updatedAt: new Date().toISOString()
                });
              } else {
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.content) {
                    fullContent += parsed.content;
                    setStreamingContent(fullContent);
                  }
                } catch (e) {
                  fullContent += data;
                  setStreamingContent(fullContent);
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'system',
        content: 'Error: Failed to get response. Please try again.',
        timestamp: new Date().toISOString()
      };
      onUpdate({
        ...updatedConversation,
        messages: [...updatedConversation.messages, errorMessage],
        updatedAt: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
      setStreamingContent('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full" {...getRootProps()}>
      <input {...getInputProps()} />
      
      {isDragActive && (
        <div className="absolute inset-0 bg-primary-500/20 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg">
            <p className="text-lg font-medium">Drop files here</p>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {streamingContent && (
          <MessageBubble
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              timestamp: new Date().toISOString()
            }}
            isStreaming
          />
        )}
        
        {isLoading && !streamingContent && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />
          </div>
          
          <button
            type="button"
            className="p-3 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            {...getRootProps()}
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
