export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: Attachment[];
  metadata?: Record<string, any>;
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  mode: SystemMode;
}

export type SystemMode = 'agent' | 'model' | 'rag' | 'sandbox' | 'evolution';

export interface SystemStatus {
  agent: boolean;
  model: boolean;
  rag: boolean;
  sandbox: boolean;
  evolution: boolean;
}

export interface StreamingResponse {
  content: string;
  done: boolean;
}

export interface FileUploadResponse {
  success: boolean;
  fileId?: string;
  error?: string;
}

export interface Theme {
  mode: 'light' | 'dark';
  accent: string;
}
