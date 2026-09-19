import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import Icon from "./Icon.jsx";

// Lightweight markdown formatter for clean, bold, and bulleted rendering
function FormattedMessage({ text }) {
  if (!text) return null;

  const lines = text.split("\n");
  const elements = [];
  let currentList = [];

  function renderInline(str) {
    // Replace **bold** with <strong>
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });
  }

  function flushList() {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-1.5 space-y-1 pl-1">
          {currentList.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs leading-relaxed text-slate-700">
              <span className="text-blue-500 font-bold select-none">•</span>
              <div>{renderInline(item)}</div>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  }

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      elements.push(<div key={`spacer-${idx}`} className="h-2" />);
      return;
    }

    if (trimmed.startsWith("• ") || trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      currentList.push(trimmed.slice(2));
    } else {
      flushList();
      elements.push(
        <p key={`p-${idx}`} className="text-xs leading-relaxed text-slate-700 mb-1">
          {renderInline(trimmed)}
        </p>
      );
    }
  });

  flushList();
  return <div className="space-y-0.5">{elements}</div>;
}

export default function EmployeeCareerChatbot({
  isOpen,
  onClose,
  selectedRoleId = null,
  onClearRoleContext = null,
}) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeRoleId, setActiveRoleId] = useState(selectedRoleId);
  const [roleContext, setRoleContext] = useState(null);
  const [suggestedActions, setSuggestedActions] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Sync selectedRoleId when changed from parent
  useEffect(() => {
    setActiveRoleId(selectedRoleId);
  }, [selectedRoleId]);

  // Load chat context and suggestions whenever activeRoleId changes or on first open
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    async function loadContext() {
      try {
        const query = activeRoleId ? `?role_id=${activeRoleId}` : "";
        const data = await api(`/me/chat/context${query}`);
        if (!isMounted) return;

        setRoleContext(data);
        if (data.suggested_actions?.length) {
          setSuggestedActions(data.suggested_actions);
        }

        // Add initial greeting if first time open
        if (messages.length === 0) {
          const rolePhrase = data.role_title
            ? ` Currently reviewing **${data.role_title}** (${data.fit_score}% Fit, ${data.readiness_score}% Readiness).`
            : "";
          setMessages([
            {
              id: "init",
              role: "assistant",
              content: `Hello! I am your **RoleFlow Career Assistant**.${rolePhrase} Ask me anything about your verified skills, match factors, skill gaps, or learning roadmap!`,
              sources: data.sources || ["employee_profile"],
            },
          ]);
        }
      } catch (err) {
        console.error("Failed to load chat context:", err);
      }
    }

    loadContext();
    return () => {
      isMounted = false;
    };
  }, [isOpen, activeRoleId]);

  // Auto-scroll on new messages
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading, isOpen]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  async function handleSend(textToSend) {
    const text = (textToSend || inputText).trim();
    if (!text || isLoading) return;

    setInputText("");
    const userMsgId = `usr-${Date.now()}`;
    const newMessages = [...messages, { id: userMsgId, role: "user", content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const payload = {
        message: text,
        role_id: activeRoleId,
        conversation_id: conversationId,
        history: newMessages.slice(-6).map((m) => ({ role: m.role, content: m.content })),
      };

      const res = await api("/me/chat", { method: "POST", body: payload });
      if (res.conversation_id) setConversationId(res.conversation_id);
      if (res.suggested_actions?.length) setSuggestedActions(res.suggested_actions);

      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: res.message,
          sources: res.sources || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-err-${Date.now()}`,
          role: "assistant",
          content:
            "I encountered a temporary connection issue. You can still ask me about your verified skills, readiness score, or opportunities from your RoleFlow profile.",
          sources: [],
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleChipClick(chipText) {
    handleSend(chipText);
  }

  function handleClearContext() {
    setActiveRoleId(null);
    setRoleContext((prev) => (prev ? { ...prev, role_id: null, role_title: null } : null));
    if (onClearRoleContext) onClearRoleContext();
  }

  function handleResetChat() {
    setMessages([]);
    setConversationId(null);
    setInputText("");
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end p-3 sm:p-6 md:inset-auto md:bottom-6 md:right-6 pointer-events-none">
      <div
        className="pointer-events-auto flex flex-col w-full h-[92vh] sm:h-[620px] sm:w-[430px] rounded-3xl bg-white border border-slate-200/90 shadow-2xl shadow-slate-900/20 overflow-hidden transition-all duration-300 ease-out"
        style={{ animation: "careerChatFadeUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)" }}
      >
        {/* Style injection for micro-animations */}
        <style>{`
          @keyframes careerChatFadeUp {
            from { opacity: 0; transform: translateY(20px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
          }
          @keyframes pulseDot {
            0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
            40% { opacity: 1; transform: scale(1.15); }
          }
        `}</style>

        {/* 1. Header */}
        <header className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-4 py-3.5 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 shadow-md shadow-blue-500/20 text-white">
              <Icon name="sparkles" className="size-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900 leading-tight">RoleFlow Career Assistant</h3>
                <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded-full">
                  <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Connected
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Your AI guide for internal mobility</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={handleResetChat}
              disabled={isLoading || messages.length <= 1}
              className="rounded-lg p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition disabled:opacity-30"
              title="Reset conversation"
            >
              <Icon name="refresh" className="size-3.5" />
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
              title="Close assistant"
            >
              ✕
            </button>
          </div>
        </header>

        {/* 2. Role Context Banner (Compact) */}
        {roleContext?.role_title && (
          <div className="flex items-center justify-between border-b border-blue-100 bg-blue-50/70 px-4 py-2 text-[11px]">
            <div className="flex items-center gap-2 truncate">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-100/70 px-1.5 py-0.5 rounded">
                Discussing
              </span>
              <span className="font-semibold text-slate-800 truncate">{roleContext.role_title}</span>
              {roleContext.fit_score != null && (
                <span className="font-bold text-blue-700">· {roleContext.fit_score}% Fit</span>
              )}
              {roleContext.readiness_score != null && (
                <span className="font-bold text-emerald-700">· {roleContext.readiness_score}% Readiness</span>
              )}
            </div>
            <button
              onClick={handleClearContext}
              className="ml-2 text-slate-400 hover:text-slate-600 text-xs px-1"
              title="Clear role context"
            >
              ✕
            </button>
          </div>
        )}

        {/* 3. Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3.5 bg-slate-50/30">
          {messages.map((m) => {
            const isUser = m.role === "user";
            return (
              <div
                key={m.id}
                className={`flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="grid size-7 flex-shrink-0 place-items-center rounded-full bg-blue-50 border border-blue-200/80 text-blue-600 shadow-sm mt-0.5">
                    <Icon name="sparkles" className="size-3.5" />
                  </div>
                )}

                <div className={`max-w-[85%] ${isUser ? "text-right" : "text-left"}`}>
                  <div
                    className={`rounded-2xl px-4 py-2.5 shadow-sm text-xs leading-relaxed ${
                      isUser
                        ? "bg-blue-600 text-white rounded-tr-sm"
                        : "bg-white border border-slate-200/80 text-slate-800 rounded-tl-sm"
                    }`}
                  >
                    {isUser ? m.content : <FormattedMessage text={m.content} />}
                  </div>

                  {/* Grounded source indicator */}
                  {!isUser && m.sources?.length > 0 && (
                    <div className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-400 pl-1">
                      <span className="text-emerald-500 font-bold">✓</span>
                      <span>Based on your RoleFlow profile records</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex gap-2.5 justify-start items-center">
              <div className="grid size-7 flex-shrink-0 place-items-center rounded-full bg-blue-50 border border-blue-200 text-blue-600 shadow-sm">
                <Icon name="sparkles" className="size-3.5" />
              </div>
              <div className="rounded-2xl bg-white border border-slate-200/80 px-4 py-2.5 shadow-sm flex items-center gap-1.5">
                <span
                  className="size-2 rounded-full bg-blue-500"
                  style={{ animation: "pulseDot 1.4s infinite 0s" }}
                />
                <span
                  className="size-2 rounded-full bg-blue-500"
                  style={{ animation: "pulseDot 1.4s infinite 0.2s" }}
                />
                <span
                  className="size-2 rounded-full bg-blue-500"
                  style={{ animation: "pulseDot 1.4s infinite 0.4s" }}
                />
                <span className="text-[11px] text-slate-400 ml-1">Analyzing your profile...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 4. Quick Action Chips */}
        {suggestedActions.length > 0 && (
          <div className="border-t border-slate-100 bg-white px-3.5 py-2.5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5 px-0.5">
              Suggested Questions
            </p>
            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
              {suggestedActions.slice(0, 4).map((chip, i) => (
                <button
                  key={i}
                  onClick={() => handleChipClick(chip)}
                  disabled={isLoading}
                  className="rounded-full border border-slate-200 bg-slate-50/80 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 px-3 py-1 text-[11px] font-medium text-slate-600 transition-all duration-150 hover:-translate-y-0.5 hover:shadow-sm disabled:opacity-40 text-left"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 5. Input Composer */}
        <div className="border-t border-slate-200 bg-slate-50/50 p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask about your skills, opportunities, or career path..."
              disabled={isLoading}
              className="flex-1 rounded-2xl border border-slate-300 bg-white px-4 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="grid size-9 place-items-center rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-600/25 transition-all duration-150 hover:bg-blue-500 active:scale-95 disabled:opacity-40"
              title="Send message"
            >
              <Icon name="arrowRight" className="size-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
