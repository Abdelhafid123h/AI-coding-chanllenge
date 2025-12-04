'use client';

import { useState } from 'react';
import axios from 'axios';
import styles from './page.module.css';

interface Message {
  type: 'question' | 'answer';
  content: string;
  sources?: string[];
}

export default function Home() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    // Add question to messages
    const newQuestion: Message = {
      type: 'question',
      content: question,
    };
    setMessages(prev => [...prev, newQuestion]);

    try {
      const response = await axios.post(`${API_URL}/ask`, {
        question: question.trim(),
      });

      const newAnswer: Message = {
        type: 'answer',
        content: response.data.answer,
        sources: response.data.sources,
      };

      setMessages(prev => [...prev, newAnswer]);
      setQuestion('');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMessage);
      
      const errorAnswer: Message = {
        type: 'answer',
        content: `Error: ${errorMessage}`,
        sources: [],
      };
      setMessages(prev => [...prev, errorAnswer]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <header className={styles.header}>
          <h1>RAG Q&A Chatbot</h1>
          <p>Ask questions about your documents</p>
        </header>

        <div className={styles.chatContainer}>
          <div className={styles.messagesContainer}>
            {messages.length === 0 ? (
              <div className={styles.emptyState}>
                <p>👋 Welcome! Ask a question to get started.</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.type === 'question'
                      ? styles.questionMessage
                      : styles.answerMessage
                  }
                >
                  <div className={styles.messageHeader}>
                    {message.type === 'question' ? '🧑 You' : '🤖 Assistant'}
                  </div>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                  {message.sources && message.sources.length > 0 && (
                    <div className={styles.sources}>
                      <strong>Sources:</strong>
                      <ul>
                        {message.sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className={styles.answerMessage}>
                <div className={styles.messageHeader}>🤖 Assistant</div>
                <div className={styles.messageContent}>
                  <div className={styles.loader}>Thinking...</div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className={styles.inputForm}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your documents..."
              className={styles.input}
              disabled={loading}
            />
            <button
              type="submit"
              className={styles.button}
              disabled={loading || !question.trim()}
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>

          {error && (
            <div className={styles.errorBanner}>
              {error}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
