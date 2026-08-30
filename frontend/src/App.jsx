import { useState, useRef, useEffect } from 'react';

function App() {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem('conversations');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentChatId, setCurrentChatId] = useState(() => Date.now().toString());
  
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);
  const wasTypingRef = useRef(false);

  // Save conversation whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      setConversations(prev => {
        const existingIdx = prev.findIndex(c => c.id === currentChatId);
        const title = messages[0].content.slice(0, 30) + (messages[0].content.length > 30 ? '...' : '');
        
        const updatedChat = {
          id: currentChatId,
          title: title,
          messages: messages,
          updatedAt: Date.now()
        };

        let newConversations;
        if (existingIdx >= 0) {
          newConversations = [...prev];
          newConversations[existingIdx] = updatedChat;
        } else {
          newConversations = [updatedChat, ...prev];
        }
        
        // Sort by updatedAt descending
        newConversations.sort((a, b) => b.updatedAt - a.updatedAt);
        localStorage.setItem('conversations', JSON.stringify(newConversations));
        return newConversations;
      });
    }
  }, [messages, currentChatId]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(Date.now().toString());
  };

  const loadConversation = (id) => {
    const chat = conversations.find(c => c.id === id);
    if (chat) {
      setMessages(chat.messages);
      setCurrentChatId(chat.id);
    }
  };

  const handleClearHistory = () => {
    setConversations([]);
    setMessages([]);
    setCurrentChatId(Date.now().toString());
    localStorage.removeItem('conversations');
  };

  // Initialize theme
  useEffect(() => {
    if (theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
      setTheme('dark');
    } else {
      document.documentElement.classList.remove('dark');
      setTheme('light');
    }
  }, []);

  const toggleTheme = () => {
    if (theme === 'dark') {
      document.documentElement.classList.remove('dark');
      setTheme('light');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      setTheme('dark');
      localStorage.setItem('theme', 'dark');
    }
  };

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'auto'
      });
    }
  };

  useEffect(() => {
    if (isTyping) {
      wasTypingRef.current = true;
      scrollToBottom();
    } else {
      if (wasTypingRef.current) {
        wasTypingRef.current = false;
        const lastMsgIndex = messages.length - 1;
        if (lastMsgIndex >= 0) {
          const msgEl = document.getElementById(`message-${lastMsgIndex}`);
          if (msgEl) {
            msgEl.scrollIntoView({ behavior: 'auto', block: 'start' });
            return;
          }
        }
      }
      scrollToBottom();
    }
  }, [messages, isTyping]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isTyping && inputValue.trim() !== '') {
        handleSubmission(inputValue);
      }
    }
  };

  const handleSubmitForm = (e) => {
    e.preventDefault();
    if (!isTyping && inputValue.trim() !== '') {
      handleSubmission(inputValue);
    }
  };

  const handleSubmission = async (query) => {
    // Add user message
    const userMsg = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    
    setIsTyping(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      const assistantMsg = { 
        role: 'assistant', 
        content: data.answer,
        sources: data.sources 
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error("Query Error:", error);
      const errorMsg = {
        role: 'assistant',
        content: "I apologize, but I encountered a network error or backend issue while trying to retrieve that information. Please try again in a moment.",
        isError: true
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleQuickPrompt = (prompt) => {
    if (!isTyping) {
      handleSubmission(prompt);
    }
  };

  const formatMessageContent = (text) => {
    if (!text) return null;
    
    // Basic regex to replace markdown links with HTML links
    const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g);
    
    return parts.map((part, index) => {
      const linkMatch = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch) {
        return (
          <a key={index} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="text-secondary dark:text-primary-fixed underline decoration-secondary/40 dark:decoration-primary-fixed/40 underline-offset-4 hover:decoration-secondary dark:hover:decoration-primary-fixed transition-all">
            {linkMatch[1]}
          </a>
        );
      }
      
      // Handle simple newlines
      return (
        <span key={index}>
          {part.split('\n').map((line, i) => (
            <span key={i}>
              {line}
              {i !== part.split('\n').length - 1 && <br />}
            </span>
          ))}
        </span>
      );
    });
  };

  return (
    <div className="flex flex-col h-[100dvh] overflow-hidden">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-surface dark:bg-gray-800 shadow-[0_4px_20px_rgba(0,51,102,0.08)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <div className="h-20 max-w-container-max mx-auto px-margin-mobile lg:px-margin-desktop flex items-center justify-between">
          <div className="flex-1"></div>
          <div className="flex flex-col items-center text-center">
            <h1 className="font-headline-lg-mobile text-headline-lg-mobile lg:font-title-md lg:text-title-md text-primary dark:text-primary-fixed">🏦 Mutual Fund FAQ Assistant</h1>
            <span className="font-caption text-caption text-on-surface-variant dark:text-gray-400">AI-Powered Factual Data</span>
          </div>
          <div className="flex-1 flex justify-end items-center gap-4">
            <nav className="hidden md:flex items-center gap-gutter mr-4">
              <span className="transition-colors text-primary dark:text-primary-fixed font-bold">Assistant</span>
              <a className="font-label-md text-label-md text-on-surface-variant dark:text-gray-400 hover:text-primary dark:hover:text-primary-fixed transition-colors" href="#">Disclaimer</a>
            </nav>
            <div className="w-8 h-8 rounded-full bg-primary dark:bg-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary dark:text-on-primary-container text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="w-full pt-20 flex-1 min-h-0 flex flex-col md:flex-row relative overflow-hidden">
        
        {/* Sidebar */}
        <aside className="hidden md:flex flex-col w-64 lg:w-72 bg-surface-container-low dark:bg-gray-800/50 border-r border-outline-variant/30 dark:border-gray-700 h-full flex-shrink-0 z-40">
          <div className="p-4 border-b border-outline-variant/20 dark:border-gray-700">
            <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-3 bg-primary text-on-primary py-4 px-6 rounded-xl hover:bg-primary/90 dark:bg-primary-container dark:text-on-primary-container dark:hover:bg-primary-container/90 transition-all duration-300 shadow-xl shadow-primary/20 dark:shadow-none ring-1 ring-primary-fixed/30 hover:scale-[1.02] active:scale-95 group">
              <span className="material-symbols-outlined text-[24px] font-bold">add</span>
              <span className="font-label-md font-bold tracking-wide">New Chat</span>
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto py-2 flex flex-col">
            <h3 className="px-4 py-2 font-caption text-on-surface-variant dark:text-gray-400 uppercase tracking-wider text-xs font-semibold">Recent Conversations</h3>
            <nav className="flex flex-col gap-1 px-2 mb-auto relative">
               {conversations.length === 0 ? (
                 <div className="px-4 py-2 text-caption text-on-surface-variant/50 italic">No recent chats</div>
               ) : (
                 conversations.map(chat => (
                   <button 
                     key={chat.id}
                     onClick={() => loadConversation(chat.id)}
                     className={`w-full text-left px-3 py-2 rounded-lg truncate transition-colors text-body-sm ${currentChatId === chat.id ? 'bg-primary/10 dark:bg-primary-fixed/20 text-primary dark:text-primary-fixed font-medium' : 'text-on-surface-variant dark:text-gray-300 hover:bg-surface-container-high dark:hover:bg-gray-700'}`}
                   >
                     {chat.title}
                   </button>
                 ))
               )}
            </nav>
            
            <div className="p-4 border-t border-outline-variant/20 dark:border-gray-700 mt-4 relative">
              <button onClick={handleClearHistory} className="w-full flex items-center justify-start gap-3 px-3 py-2.5 mb-2 rounded-md hover:bg-error-container/10 dark:hover:bg-red-900/20 transition-colors group text-error dark:text-red-400">
                <span className="material-symbols-outlined text-[18px]">delete_sweep</span>
                <span className="font-body-md">Clear History</span>
              </button>
              <button onClick={toggleTheme} className="w-full flex items-center justify-start gap-3 px-3 py-2.5 rounded-md hover:bg-surface-container-high dark:hover:bg-gray-700/50 transition-colors group">
                <span className="material-symbols-outlined text-on-surface-variant dark:text-gray-400 group-hover:text-primary dark:group-hover:text-primary-fixed text-[18px]">
                  {theme === 'dark' ? 'light_mode' : 'dark_mode'}
                </span>
                <span className="font-body-md text-on-surface dark:text-gray-200">
                  {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                </span>
              </button>
            </div>
          </div>
        </aside>

        {/* Chat Area */}
        <div className="flex flex-col w-full h-full relative overflow-hidden">
          
          {/* Main Chat Container */}
          <div ref={chatContainerRef} className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden relative flex flex-col items-center w-full pb-40">
            
            {/* Abstract Background Decoration */}
            <div className="absolute inset-0 pointer-events-none opacity-40 mix-blend-multiply dark:mix-blend-screen dark:opacity-10 flex justify-center -z-10">
              <svg className="w-full h-full text-primary-fixed-dim/20 dark:text-primary-fixed/30 fill-current animate-[spin_120s_linear_infinite]" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg">
                <path d="M48.5,-63.3C62.1,-52.1,72.1,-36.8,77.7,-19.7C83.3,-2.6,84.4,16.2,76.5,31.4C68.6,46.6,51.7,58.3,34.2,65.3C16.6,72.4,-1.7,74.9,-20.2,71.7C-38.6,68.6,-57.2,59.8,-68.8,45.2C-80.4,30.5,-85,10,-81.4,-8.4C-77.8,-26.8,-66,-43.2,-51,-54.6C-36.1,-66,-18,-72.4,-0.2,-72.2C17.7,-71.9,35,-65,48.5,-63.3Z" transform="translate(500 500) scale(4)"></path>
              </svg>
            </div>

            <div className={`w-full max-w-[800px] flex flex-col gap-6 p-margin-mobile lg:p-margin-desktop ${messages.length === 0 ? 'min-h-full justify-center' : ''}`}>
              
              {/* Welcome Section */}
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center text-center py-12 px-4 animate-[fadeInUp_0.6s_ease-out_forwards]">
                  <div className="w-16 h-16 rounded-2xl bg-primary dark:bg-primary-container flex items-center justify-center mb-6 shadow-xl shadow-primary/20 dark:shadow-none ring-4 ring-primary-fixed/30 dark:ring-primary-fixed/10">
                    <span className="material-symbols-outlined text-on-primary dark:text-on-primary-container text-[32px]" style={{fontVariationSettings: "'FILL' 1"}}>smart_toy</span>
                  </div>
                  <h2 className="font-headline-lg-mobile lg:font-headline-lg text-primary dark:text-primary-fixed mb-2">How can I help you today?</h2>
                  <p className="font-body-md text-on-surface-variant dark:text-gray-400 max-w-md mx-auto mb-8">I can answer factual questions about HDFC mutual fund schemes on Groww.</p>
                  
                  <div className="flex flex-col w-full gap-3 text-left">
                    <p className="font-label-md text-on-surface-variant/70 dark:text-gray-500 uppercase tracking-widest text-xs mb-2 pl-2">💡 Try asking:</p>
                    
                    {[
                      { icon: 'percent', text: 'What is the expense ratio of HDFC Mid Cap Fund?' },
                      { icon: 'output', text: 'What is the exit load for HDFC ELSS Tax Saver Fund?' },
                      { icon: 'payments', text: 'What is the minimum SIP amount for HDFC Large Cap Fund?' }
                    ].map((btn, idx) => (
                      <button 
                        key={idx}
                        onClick={() => handleQuickPrompt(btn.text)}
                        disabled={isTyping}
                        className="group flex items-start gap-4 p-4 rounded-xl bg-surface-container-low dark:bg-gray-800/80 hover:bg-secondary-fixed/50 dark:hover:bg-gray-700 transition-all duration-300 relative overflow-hidden text-left"
                      >
                        <div className="w-8 h-8 rounded-full bg-primary/10 dark:bg-primary-fixed/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 dark:group-hover:bg-primary-fixed/20 transition-colors">
                          <span className="material-symbols-outlined text-primary dark:text-primary-fixed text-[16px]">{btn.icon}</span>
                        </div>
                        <span className="font-body-md text-on-surface dark:text-gray-200 flex-1 mt-1">{btn.text}</span>
                        <span className="material-symbols-outlined text-on-surface-variant dark:text-gray-400 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all mt-1">arrow_forward</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Message List */}
              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';
                return (
                  <div id={`message-${index}`} key={index} className={`flex w-full animate-[fadeInUp_0.4s_ease-out_forwards] ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`flex max-w-[85%] gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                      {/* Avatar */}
                      <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center mt-1 shadow-sm ${isUser ? 'bg-tertiary-fixed dark:bg-gray-700' : 'bg-primary dark:bg-primary-container'}`}>
                        {isUser ? (
                          <span className="material-symbols-outlined text-on-tertiary-fixed dark:text-gray-200 text-[18px]">person</span>
                        ) : (
                          <span className="material-symbols-outlined text-on-primary dark:text-on-primary-container text-[18px]" style={{fontVariationSettings: "'FILL' 1"}}>smart_toy</span>
                        )}
                      </div>

                      {/* Bubble */}
                      <div className={
                        isUser 
                          ? 'bg-primary dark:bg-primary-container text-on-primary dark:text-on-primary-container rounded-2xl rounded-tr-sm px-5 py-3 shadow-[0_4px_20px_rgba(0,51,102,0.08)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)]' 
                          : `bg-surface-container-lowest dark:bg-gray-800 text-on-surface dark:text-gray-200 rounded-2xl rounded-tl-sm px-6 py-4 shadow-[0_4px_20px_rgba(0,51,102,0.08)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)] ring-1 ring-outline-variant/20 dark:ring-gray-700 ${msg.isError ? 'ring-error/50 bg-error-container/10 dark:ring-red-500/50 dark:bg-red-900/10' : ''}`
                      }>
                        <div className="font-body-md whitespace-pre-wrap">
                          {formatMessageContent(msg.content)}
                        </div>

                        {/* Sources */}
                        {!isUser && msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-outline-variant/20 dark:border-gray-700 flex flex-wrap gap-2 items-center">
                            <span className="font-label-md text-on-surface-variant dark:text-gray-400 text-xs uppercase tracking-wider">Sources:</span>
                            {msg.sources.map((src, i) => (
                              <a key={i} href={src.url || src.source_url || '#'} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-container-low dark:bg-gray-700 hover:bg-secondary-fixed/40 dark:hover:bg-gray-600 transition-colors font-caption text-secondary dark:text-primary-fixed no-underline">
                                <span className="material-symbols-outlined text-[14px]">link</span> {src.title || src.scheme_name || src.section || 'Source'}
                              </a>
                            ))}
                          </div>
                        )}

                        {/* Disclaimer */}
                        {!isUser && (
                          <div className="mt-4 bg-surface-container-low dark:bg-gray-700/50 rounded-lg p-3 flex items-start gap-2">
                            <span className="material-symbols-outlined text-on-surface-variant dark:text-gray-400 text-[16px] shrink-0 mt-0.5">info</span>
                            <p className="font-caption text-on-surface-variant dark:text-gray-400 text-[11px] leading-tight m-0">
                              Disclaimer: The information provided is factual data extracted from Groww based on recent scrapes. It does not constitute financial advice or investment recommendations.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex w-full justify-start animate-[fadeInUp_0.4s_ease-out_forwards]">
                  <div className="flex max-w-[85%] gap-4 flex-row">
                    <div className="w-8 h-8 rounded-full shrink-0 flex items-center justify-center mt-1 bg-primary dark:bg-primary-container shadow-sm">
                      <span className="material-symbols-outlined text-on-primary dark:text-on-primary-container text-[18px]" style={{fontVariationSettings: "'FILL' 1"}}>smart_toy</span>
                    </div>
                    <div className="bg-surface-container-lowest dark:bg-gray-800 rounded-2xl rounded-tl-sm px-5 py-4 shadow-[0_4px_20px_rgba(0,51,102,0.08)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)] ring-1 ring-outline-variant/20 dark:ring-gray-700 flex items-center gap-1.5 h-[48px]">
                      <div className="w-2 h-2 rounded-full bg-primary/40 dark:bg-primary-fixed/40 animate-[bounce_1.4s_infinite_ease-in-out_both] delay-[-0.32s]"></div>
                      <div className="w-2 h-2 rounded-full bg-primary/40 dark:bg-primary-fixed/40 animate-[bounce_1.4s_infinite_ease-in-out_both] delay-[-0.16s]"></div>
                      <div className="w-2 h-2 rounded-full bg-primary/40 dark:bg-primary-fixed/40 animate-[bounce_1.4s_infinite_ease-in-out_both]"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-background via-background/95 to-transparent dark:from-gray-900 dark:via-gray-900/95 pt-12 pb-margin-mobile lg:pb-margin-desktop px-margin-mobile lg:px-margin-desktop flex flex-col items-center z-20 pointer-events-none">
            
            <div className="w-full max-w-[800px] pointer-events-auto">
              <form onSubmit={handleSubmitForm} className="relative flex items-end w-full rounded-2xl bg-surface dark:bg-gray-800 shadow-[0_8px_30px_rgba(0,51,102,0.12)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.4)] border-none ring-1 ring-outline-variant/30 dark:ring-gray-700 transition-all duration-300 focus-within:ring-2 focus-within:ring-secondary dark:focus-within:ring-primary-fixed focus-within:shadow-[0_8px_40px_rgba(48,94,160,0.2)] dark:focus-within:shadow-[0_8px_40px_rgba(0,0,0,0.5)]">
                <textarea 
                  ref={inputRef}
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  disabled={isTyping}
                  className="w-full bg-transparent border-none outline-none resize-none font-body-md text-on-surface dark:text-gray-100 px-6 py-4 min-h-[56px] max-h-[150px] scrollbar-hide placeholder:text-on-surface-variant/50 dark:placeholder:text-gray-500 flex-1 leading-relaxed" 
                  placeholder="Type your question..." 
                  rows="1"
                />
                <button 
                  type="submit" 
                  disabled={inputValue.trim() === '' || isTyping}
                  className="p-4 shrink-0 text-primary dark:text-primary-fixed hover:text-secondary dark:hover:text-primary-fixed-dim disabled:text-outline-variant dark:disabled:text-gray-600 disabled:cursor-not-allowed transition-colors group relative"
                >
                  <div className="w-10 h-10 rounded-full flex items-center justify-center group-hover:bg-primary/5 dark:group-hover:bg-primary-fixed/10 transition-colors">
                    <span className="material-symbols-outlined transform group-hover:translate-x-1 group-active:scale-95 transition-all" style={{fontVariationSettings: "'FILL' 1"}}>send</span>
                  </div>
                </button>
              </form>
              
              <div className="flex flex-col items-center mt-3 gap-2">
                <span className="font-caption text-caption text-on-surface-variant/60 dark:text-gray-500 text-center">Responses are generated by AI and may be inaccurate.</span>
                
                {/* Disclaimer Banner */}
                <div className="bg-error-container/30 dark:bg-error-container/20 border border-error/20 dark:border-error/30 py-1 px-3 rounded-full flex items-center justify-center gap-1.5 backdrop-blur-md shadow-sm">
                  <span className="material-symbols-outlined text-error dark:text-red-400 text-[14px]" style={{fontVariationSettings: "'FILL' 1"}}>warning</span>
                  <p className="font-caption font-medium text-error dark:text-red-300 m-0 text-[10px] uppercase tracking-wider">Facts-only. No investment advice.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
