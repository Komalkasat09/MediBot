'use client';
import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, Cpu, FileText, Sparkles, Mic, MicOff, Image as ImageIcon, X } from 'lucide-react';

interface Message {
  role: 'user' | 'bot';
  content: string;
  sources?: string[];
  image?: string;
}

const Bot3D = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    let animationFrame: number;
    let time = 0;
    
    const animate = () => {
      time += 0.02;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const float = Math.sin(time) * 10;
      
      ctx.fillStyle = 'rgba(6, 182, 212, 0.1)';
      ctx.beginPath();
      ctx.ellipse(centerX, centerY + 120, 80, 20, 0, 0, Math.PI * 2);
      ctx.fill();
      
      const gradient = ctx.createRadialGradient(centerX, centerY + float, 0, centerX, centerY + float, 120);
      gradient.addColorStop(0, 'rgba(6, 182, 212, 0.3)');
      gradient.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(centerX - 120, centerY + float - 120, 240, 240);
      
      ctx.fillStyle = '#1e293b';
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(centerX, centerY - 30 + float, 60, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      
      const eyeGlow = ctx.createRadialGradient(centerX - 20, centerY - 35 + float, 0, centerX - 20, centerY - 35 + float, 10);
      eyeGlow.addColorStop(0, '#22d3ee');
      eyeGlow.addColorStop(1, '#06b6d4');
      ctx.fillStyle = eyeGlow;
      ctx.beginPath();
      ctx.arc(centerX - 20, centerY - 35 + float, 8, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = eyeGlow;
      ctx.beginPath();
      ctx.arc(centerX + 20, centerY - 35 + float, 8, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY - 90 + float);
      ctx.lineTo(centerX, centerY - 70 + float);
      ctx.stroke();
      
      const antennaGlow = ctx.createRadialGradient(centerX, centerY - 90 + float, 0, centerX, centerY - 90 + float, 8);
      antennaGlow.addColorStop(0, '#22d3ee');
      antennaGlow.addColorStop(1, '#06b6d4');
      ctx.fillStyle = antennaGlow;
      ctx.beginPath();
      ctx.arc(centerX, centerY - 90 + float, 5, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = '#1e293b';
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 3;
      ctx.fillRect(centerX - 50, centerY + 30 + float, 100, 80);
      ctx.strokeRect(centerX - 50, centerY + 30 + float, 100, 80);
      
      ctx.fillStyle = '#0e7490';
      ctx.fillRect(centerX - 35, centerY + 45 + float, 70, 40);
      
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 1;
      for (let i = 0; i < 3; i++) {
        ctx.beginPath();
        ctx.moveTo(centerX - 30, centerY + 55 + i * 10 + float);
        ctx.lineTo(centerX + 30, centerY + 55 + i * 10 + float);
        ctx.stroke();
      }
      
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 8;
      ctx.lineCap = 'round';
      
      ctx.beginPath();
      ctx.moveTo(centerX - 50, centerY + 50 + float);
      ctx.lineTo(centerX - 80, centerY + 70 + float + Math.sin(time * 2) * 5);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(centerX + 50, centerY + 50 + float);
      ctx.lineTo(centerX + 80, centerY + 70 + float - Math.sin(time * 2) * 5);
      ctx.stroke();
      
      for (let i = 0; i < 3; i++) {
        const angle = time * 2 + i * (Math.PI * 2 / 3);
        const radius = 100;
        const px = centerX + Math.cos(angle) * radius;
        const py = centerY + Math.sin(angle) * radius + float;
        
        const particleGlow = ctx.createRadialGradient(px, py, 0, px, py, 5);
        particleGlow.addColorStop(0, 'rgba(34, 211, 238, 0.8)');
        particleGlow.addColorStop(1, 'rgba(34, 211, 238, 0)');
        ctx.fillStyle = particleGlow;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      }
      
      animationFrame = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, []);
  
  return (
    <canvas 
      ref={canvasRef} 
      width={400} 
      height={400}
      className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-20 pointer-events-none"
    />
  );
};

const Loader = () => {
  return (
    <div className="flex items-center space-x-2">
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400"></div>
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400" style={{ animationDelay: '0.2s' }}></div>
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400" style={{ animationDelay: '0.4s' }}></div>
    </div>
  );
};

export default function EnhancedMedicalChatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMessages([
      { 
        role: 'bot', 
        content: 'Hello! I\'m your AI medical assistant with vision and voice capabilities. You can type, speak, or upload medical images for analysis.' 
      }
    ]);

    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsRecording(false);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if ((!input.trim() && !selectedImage) || isLoading) return;

    const userMessage: Message = { 
      role: 'user', 
      content: input || 'Analyzing image...',
      image: selectedImage || undefined
    };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    const currentImage = selectedImage;
    setInput('');
    setSelectedImage(null);
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: currentInput,
          image_base64: currentImage 
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      const botMessage: Message = {
        role: 'bot',
        content: data.answer,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to get answer:', error);
      const errorMessage: Message = {
        role: 'bot',
        content: "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running at http://127.0.0.1:8000",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <Bot3D />

      <header className="relative bg-slate-800/80 backdrop-blur-lg border-b border-cyan-500/20 p-6 shadow-lg">
        <div className="flex items-center justify-center gap-3">
          <div className="relative">
            <Sparkles className="text-cyan-400" size={28} />
            <div className="absolute inset-0 blur-xl bg-cyan-400/50"></div>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 text-transparent bg-clip-text">
            Multimodal RAG Medical Chatbot
          </h1>
        </div>
        <p className="text-center text-slate-400 text-sm mt-2">Text • Voice • Vision powered by AI</p>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''} animate-fadeIn`}
          >
            {msg.role === 'bot' && (
              <div className="relative w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                <Cpu size={22} className="text-white" />
                <div className="absolute inset-0 rounded-full bg-cyan-400/30 animate-ping"></div>
              </div>
            )}
            <div className={`rounded-2xl p-5 max-w-2xl backdrop-blur-sm transition-all hover:scale-[1.02] ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-cyan-600/90 to-blue-600/90 text-white shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-800/90 text-slate-200 border border-slate-700/50 shadow-xl'
              }`}
            >
              {msg.image && (
                <img 
                  src={msg.image} 
                  alt="Uploaded" 
                  className="rounded-lg mb-3 max-w-full h-auto max-h-64 object-contain border border-slate-600"
                />
              )}
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-600/50">
                  <h3 className="text-sm font-semibold mb-3 text-cyan-400 flex items-center gap-2">
                    <FileText size={14} />
                    Referenced Sources
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((source, i) => (
                      <div 
                        key={i} 
                        className="bg-slate-700/50 text-xs text-slate-300 px-3 py-1.5 rounded-full flex items-center gap-1.5 border border-slate-600/30 hover:border-cyan-500/50 transition-colors"
                      >
                        <FileText size={12} className="text-cyan-400" />
                        <span>{source}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                <MessageSquare size={22} className="text-white" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start gap-4 animate-fadeIn">
            <div className="relative w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Cpu size={22} className="text-white" />
              <div className="absolute inset-0 rounded-full bg-cyan-400/30 animate-ping"></div>
            </div>
            <div className="rounded-2xl p-5 bg-slate-800/90 border border-slate-700/50">
              <Loader />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="relative p-6 bg-slate-800/80 backdrop-blur-lg border-t border-cyan-500/20">
        {selectedImage && (
          <div className="max-w-4xl mx-auto mb-4 relative">
            <div className="relative inline-block">
              <img 
                src={selectedImage} 
                alt="Selected" 
                className="rounded-lg max-h-32 border-2 border-cyan-500/50"
              />
              <button
                onClick={removeImage}
                className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 rounded-full p-1 shadow-lg transition-all"
              >
                <X size={16} className="text-white" />
              </button>
            </div>
          </div>
        )}
        <div className="flex items-center gap-3 max-w-4xl mx-auto">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="p-4 rounded-xl bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            title="Upload image"
          >
            <ImageIcon size={22} className="text-cyan-400" />
          </button>
          <button
            onClick={toggleRecording}
            disabled={isLoading}
            className={`p-4 rounded-xl transition-all ${
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                : 'bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={isRecording ? "Stop recording" : "Start voice input"}
          >
            {isRecording ? (
              <MicOff size={22} className="text-white" />
            ) : (
              <Mic size={22} className="text-cyan-400" />
            )}
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask your medical question..."
            disabled={isLoading}
            className="flex-1 p-4 rounded-xl bg-slate-700/50 border border-slate-600/50 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-white placeholder-slate-400 backdrop-blur-sm transition-all"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || (!input.trim() && !selectedImage)}
            className="p-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-cyan-500/50 hover:scale-105 active:scale-95"
          >
            <Send size={22} className="text-white" />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}