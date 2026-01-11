import React from 'react';
import { MessageSquare, Cpu, FileText } from 'lucide-react';
import Loader from './Loader';

export interface Message {
  role: 'user' | 'bot';
  content: string;
  sources?: string[];
}

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, isLoading }) => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.map((msg, index) => (
        <div key={index} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
          {msg.role === 'bot' && (
            <div className="w-8 h-8 bg-cyan-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Cpu size={20} />
            </div>
          )}
          <div className={`rounded-lg p-4 max-w-lg ${
              msg.role === 'user'
                ? 'bg-gray-700 text-white'
                : 'bg-gray-800 text-gray-300'
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-600">
                <h3 className="text-sm font-semibold mb-2 text-gray-400">Sources:</h3>
                <div className="flex flex-wrap gap-2">
                  {msg.sources.map((source, i) => (
                    <div key={i} className="bg-gray-700 text-xs text-gray-300 px-2 py-1 rounded-full flex items-center gap-1">
                      <FileText size={12} />
                      <span>{source}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          {msg.role === 'user' && (
             <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
              <MessageSquare size={20} />
            </div>
          )}
        </div>
      ))}
      {isLoading && (
        <div className="flex items-start gap-4">
          <div className="w-8 h-8 bg-cyan-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Cpu size={20} />
          </div>
          <div className="rounded-lg p-4 bg-gray-800">
            <Loader />
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages;