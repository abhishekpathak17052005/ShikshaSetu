import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  X,
  Send,
  Bot,
  User as UserIcon,
  ChevronRight,
  BookOpen,
  ArrowRight,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Award,
  Minimize2,
  Maximize2,
} from "lucide-react";
import {
  api,
  AssistantChatResponse,
  AssistantSourceCitation,
  SuggestedAction,
} from "@/lib/api";
import { useTranslation } from "@/i18n";
import { toast } from "sonner";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  sources?: AssistantSourceCitation[];
  suggested_actions?: SuggestedAction[];
  model_provider?: string;
}

interface CapabilityAssistantProps {
  currentPage?: string;
  onNavigate: (page: string) => void;
}

export function CapabilityAssistant({
  currentPage = "Dashboard",
  onNavigate,
}: CapabilityAssistantProps) {
  const { t, isHindi } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const starterPrompts = isHindi
    ? [
        t("assistant.prompt1"),
        t("assistant.prompt2"),
        t("assistant.prompt3"),
        t("assistant.prompt4"),
      ]
    : [
        "What are my highest priority skill gaps?",
        "Recommend iGOT courses for my current role",
        "Explain Sampling Techniques for MoSPI surveys",
        "How does learning evidence differ from assessments?",
      ];

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      text: isHindi
        ? `**नमस्ते अधिकारी।** मैं आपका **कर्मयोगी एआई सह-पायलट (Co-Pilot)** हूँ।\n\nमैं राष्ट्रीय सिविल सेवा क्षमता ढांचे, सत्यापित आईगॉट कर्मयोगी कैटलॉग और आपके व्यक्तिगत क्षमता प्रोफ़ाइल पर आधारित हूँ।\n\nआज मैं आपके क्षमता विकास में किस प्रकार सहायता कर सकता हूँ?`
        : `**Namaste Officer.** I am your **Karmayogi AI Co-Pilot**.\n\nI am grounded in the National Civil Services Competency Framework, verified iGOT Karmayogi catalog, and your personalized capability profile.\n\nHow can I support your capability development today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      suggested_actions: [
        {
          action_type: "VIEW_GAP",
          label: isHindi ? "कौशल अंतराल देखें" : "View My Skill Gaps",
          target_page: "Skill Gaps",
        },
        {
          action_type: "START_LEARNING",
          label: isHindi ? "प्रशिक्षण अनुशंसाएं देखें" : "Browse Recommendations",
          target_page: "Recommendations",
        },
      ],
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue("");
    setLoading(true);

    try {
      const res: AssistantChatResponse = await api.assistant.chat({
        message: text,
        context_page: currentPage,
      });

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: res.sources,
        suggested_actions: res.suggested_actions,
        model_provider: res.model_provider,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      toast.error(err.message || "Failed to reach Karmayogi AI Co-Pilot");
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          sender: "assistant",
          text: `⚠️ **Connection Notice**: Unable to contact the AI Co-Pilot service. Please verify your network connection or try again shortly.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleActionClick = (action: SuggestedAction) => {
    if (action.target_page) {
      onNavigate(action.target_page);
      toast.info(`Navigating to ${action.target_page}`);
    }
  };

  return (
    <>
      {/* Floating Co-Pilot Trigger Button */}
      {!isOpen && (
        <button
          id="karmayogi-copilot-trigger"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-full bg-gradient-to-r from-[#123057] via-[#204e8a] to-[#087f76] px-5 py-3 text-white shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-white/20 group"
          title="Open Karmayogi AI Co-Pilot"
        >
          <div className="relative">
            <Sparkles size={18} className="text-[#ef7e37] animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
          </div>
          <span className="text-xs font-black tracking-wide">Karmayogi AI Co-Pilot</span>
          <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold text-teal-200">
            Assistant
          </span>
        </button>
      )}

      {/* Expandable Assistant Window */}
      {isOpen && (
        <div
          id="karmayogi-copilot-modal"
          className={`fixed z-50 flex flex-col bg-white shadow-2xl border border-slate-200 transition-all duration-300 ${
            isExpanded
              ? "inset-4 sm:inset-10 rounded-3xl"
              : "bottom-6 right-6 w-[95vw] sm:w-[460px] h-[640px] max-h-[88vh] rounded-3xl"
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-[#123057] to-[#1e467d] p-4 text-white rounded-t-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-[#ef7e37] border border-white/10">
                <Bot size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-black text-white">{t("assistant.title")}</h3>
                  <span className="rounded-md bg-teal-500/20 px-2 py-0.5 text-[10px] font-bold text-teal-300 border border-teal-400/30">
                    Grounded RAG
                  </span>
                </div>
                <p className="text-[11px] text-slate-300">
                  {t("assistant.subtitle")}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="rounded-lg p-1.5 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-lg p-1.5 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
                title="Close Co-Pilot"
              >
                <X size={17} />
              </button>
            </div>
          </div>

          {/* Context Ribbon */}
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-2 text-[11px] text-slate-500">
            <span className="flex items-center gap-1 font-semibold">
              <ShieldCheck size={13} className="text-[#087f76]" /> {t("assistant.activeView")}:{" "}
              <strong className="text-[#123057]">{currentPage}</strong>
            </span>
            <span className="text-[10px] text-slate-400 font-medium">
              Zero Hallucination Grounding
            </span>
          </div>

          {/* Message Thread */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/40">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.sender === "assistant" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-800 border border-teal-100 text-xs font-bold mt-0.5">
                    <Sparkles size={14} className="text-[#ef7e37]" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-[#123057] text-white shadow-sm rounded-br-none"
                      : "bg-white text-slate-800 border border-slate-200/80 shadow-sm rounded-bl-none"
                  }`}
                >
                  {msg.sender === "assistant" ? (
                    <MarkdownRenderer content={msg.text} />
                  ) : (
                    <div className="whitespace-pre-wrap font-medium">{msg.text}</div>
                  )}

                  {/* Sources / Citations */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3.5 pt-3 border-t border-slate-100 space-y-1.5">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 block">
                        Verified Sources & Curriculum:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((src, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-700 border border-slate-200/60 hover:bg-slate-200 transition-colors"
                            title={src.excerpt || src.title}
                          >
                            <BookOpen size={10} className="text-teal-600" />
                            {src.source_id}: {src.title.slice(0, 28)}
                            {src.title.length > 28 ? "..." : ""}
                            {src.url && (
                              <a
                                href={src.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <ExternalLink size={9} />
                              </a>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggested Actions */}
                  {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap gap-2">
                      {msg.suggested_actions.map((action, aIdx) => (
                        <button
                          key={aIdx}
                          onClick={() => handleActionClick(action)}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-50 px-3 py-1.5 text-[11px] font-bold text-teal-900 border border-teal-200 hover:bg-teal-100 transition-colors"
                        >
                          <span>{action.label}</span>
                          <ArrowRight size={11} />
                        </button>
                      ))}
                    </div>
                  )}

                  <div
                    className={`mt-1.5 text-[10px] text-right ${
                      msg.sender === "user" ? "text-slate-300" : "text-slate-400"
                    }`}
                  >
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === "user" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-900 border border-blue-200 text-xs font-bold mt-0.5">
                    <UserIcon size={14} />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-3 text-xs text-slate-500 bg-white p-3.5 rounded-2xl border border-slate-200 w-fit">
                <RefreshCw size={14} className="animate-spin text-[#087f76]" />
                <span>{t("assistant.thinking")}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Chips */}
          {messages.length <= 2 && (
            <div className="p-3 border-t border-slate-100 bg-white space-y-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                {t("assistant.suggestedPrompts")}
              </span>
              <div className="flex flex-wrap gap-1.5">
                {starterPrompts.map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSendMessage(prompt)}
                    className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-700 text-left transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Box */}
          <div className="p-3.5 border-t border-slate-200 bg-white rounded-b-3xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                id="copilot-input-field"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={t("assistant.placeholder")}
                disabled={loading}
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:bg-white focus:border-[#087f76] focus:outline-none transition-all placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || loading}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#123057] text-white hover:bg-[#087f76] transition-colors disabled:opacity-40 disabled:hover:bg-[#123057]"
                title="Send"
              >
                <Send size={15} />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default CapabilityAssistant;
