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
} from "lucide-react";
import {
  api,
  AssistantChatResponse,
  AssistantSourceCitation,
  SuggestedAction,
} from "@/lib/api";
import { useTranslation } from "@/i18n";
import { toast } from "sonner";
import { ThinkingIndicator } from "@/components/motion/MotionUtils";
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
  headerMode?: boolean;
}

export const CapabilityAssistant = React.memo(function CapabilityAssistant({
  currentPage = "Dashboard",
  onNavigate,
  headerMode = false,
}: CapabilityAssistantProps) {
  const { t, isHindi } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

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

  const createWelcomeMessage = (): Message => ({
      id: "welcome-1",
      sender: "assistant",
      text: isHindi
        ? `**नमस्ते अधिकारी।** मैं आपका **शिक्षासेतु एआई सहायक** हूँ।\n\nमैं राष्ट्रीय सिविल सेवा क्षमता ढांचे, सत्यापित आईगॉट कर्मयोगी कैटलॉग और आपके व्यक्तिगत क्षमता प्रोफ़ाइल पर आधारित हूँ।\n\nआज मैं आपके क्षमता विकास में किस प्रकार सहायता कर सकता हूँ?`
        : `**Namaste Officer.** I am your **ShikshaSetu AI Assistant**.\n\nI am grounded in the National Civil Services Competency Framework, verified iGOT Karmayogi catalog, and your personalized capability profile.\n\nHow can I support your capability development today?`,
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
  });

  const [messages, setMessages] = useState<Message[]>([createWelcomeMessage()]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusStage, setStatusStage] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleNewChat = () => {
    abortControllerRef.current?.abort();
    setMessages([{ ...createWelcomeMessage(), id: `welcome-${Date.now()}` }]);
    setInputValue("");
    setLoading(false);
    setStatusStage("");
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen, statusStage]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    // Abort any prior in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue("");
    setLoading(true);
    setStatusStage("Thinking...");

    let hasReceivedTokens = false;

    try {
      await api.assistant.stream(
        { message: text, context_page: currentPage },
        (event) => {
          if (event.type === "status") {
            setStatusStage(event.message || "Checking your competency context...");
          } else if (event.type === "delta") {
            if (!hasReceivedTokens) {
              hasReceivedTokens = true;
              setStatusStage(""); // hide thinking indicator once tokens start rendering
              setMessages((prev) => [
                ...prev,
                {
                  id: assistantMessageId,
                  sender: "assistant",
                  text: event.delta,
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                },
              ]);
            } else {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, text: m.text + event.delta }
                    : m
                )
              );
            }
          } else if (event.type === "done") {
            const res = event.response;
            setStatusStage("");
            setMessages((prev) => {
              const exists = prev.some((m) => m.id === assistantMessageId);
              if (exists) {
                return prev.map((m) =>
                  m.id === assistantMessageId
                    ? {
                        ...m,
                        text: res.answer || m.text,
                        sources: res.sources,
                        suggested_actions: res.suggested_actions,
                        model_provider: res.model_provider,
                      }
                    : m
                );
              } else {
                return [
                  ...prev,
                  {
                    id: assistantMessageId,
                    sender: "assistant",
                    text: res.answer,
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    sources: res.sources,
                    suggested_actions: res.suggested_actions,
                    model_provider: res.model_provider,
                  },
                ];
              }
            });
          }
        },
        controller.signal
      );
    } catch (streamErr: any) {
      if (streamErr.name === "AbortError") {
        return; // User cancelled
      }
      // Graceful fallback to standard chat endpoint if streaming encounters an error
      try {
        const res = await api.assistant.chat({ message: text, context_page: currentPage });
        setMessages((prev) => {
          const filtered = prev.filter((m) => m.id !== assistantMessageId);
          return [
            ...filtered,
            {
              id: assistantMessageId,
              sender: "assistant",
              text: res.answer,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
              sources: res.sources,
              suggested_actions: res.suggested_actions,
              model_provider: res.model_provider,
            },
          ];
        });
      } catch (err: any) {
        toast.error(err.message || "Failed to reach Karmayogi AI Co-Pilot");
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== assistantMessageId),
          {
            id: `error-${Date.now()}`,
            sender: "assistant",
            text: `⚠️ **Connection Notice**: Unable to contact the AI Co-Pilot service. Please verify your network connection or try again shortly.`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      }
    } finally {
      setLoading(false);
      setStatusStage("");
    }
  };

  const handleActionClick = (action: SuggestedAction) => {
    if (action.target_page) {
      onNavigate(action.target_page);
    }
  };

  return (
    <>
      {/* Floating Co-Pilot Trigger Button */}
      {!isOpen && (
        <button
          id="karmayogi-copilot-trigger"
          onClick={() => setIsOpen(true)}
          className={headerMode
            ? "relative z-50 flex items-center gap-2 rounded-full border border-white/20 bg-gradient-to-r from-[#123057] via-[#204e8a] to-[#087f76] px-3.5 py-2 text-white shadow-md hover:shadow-lg btn-interactive group"
            : "fixed !bottom-4 !right-4 z-50 flex max-w-[calc(100vw-2rem)] items-center gap-2.5 rounded-full border border-white/20 bg-gradient-to-r from-[#123057] via-[#204e8a] to-[#087f76] px-5 py-3 text-white shadow-xl hover:shadow-2xl btn-interactive group sm:!bottom-6 sm:!right-6"}
          style={headerMode ? undefined : { position: "fixed" }}
          title={t("assistant.title")}
        >
          <div className="relative">
            <Sparkles size={18} className="text-[#ef7e37] animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
          </div>
          <span className="text-xs font-black tracking-wide">{t("assistant.title")}</span>
          <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold text-teal-200">
            Assistant
          </span>
        </button>
      )}

      {/* Expandable Assistant Window */}
      {isOpen && (
        <div
          id="karmayogi-copilot-modal"
          className="fixed left-1/2 top-20 z-50 flex h-[640px] max-h-[88vh] w-[95vw] -translate-x-1/2 flex-col rounded-3xl border border-slate-200 bg-white shadow-2xl anim-scale-in transition-all duration-300 sm:w-[460px]"
          style={{ position: "fixed" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-[#123057] to-[#1e467d] p-4 text-white rounded-t-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-[#ef7e37] border border-white/10">
                <Bot size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white tracking-tight">{t("assistant.title")}</h3>
                </div>
                <p className="text-[11px] text-slate-300">
                  {t("assistant.subtitle")}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleNewChat}
                className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[11px] font-semibold text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
                title="Start a new chat"
              >
                <RefreshCw size={14} />
                <span>New chat</span>
              </button>
              <button
                onClick={() => {
                  abortControllerRef.current?.abort();
                  setIsOpen(false);
                }}
                className="rounded-lg p-1.5 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
                title="Close Assistant"
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
          </div>

          {/* Message Thread */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/40">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 anim-fade-up ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.sender === "assistant" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-800 border border-teal-100 text-xs font-bold mt-0.5 anim-badge-pop">
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
                    <div className="mt-3.5 pt-3 border-t border-slate-100 space-y-1.5 anim-fade-up">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                        Verified Sources & Curriculum:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((src, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] font-medium tracking-tight text-slate-700 border border-slate-200/60 hover:bg-slate-200 transition-colors"
                            title={src.excerpt || src.title}
                          >
                            <BookOpen size={10} className="text-teal-600 font-sans" />
                            <span className="font-mono">{src.source_id}</span>: <span className="font-sans font-medium">{src.title.slice(0, 28)}</span>
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
                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap gap-2 anim-fade-up">
                      {msg.suggested_actions.map((action, aIdx) => (
                        <button
                          key={aIdx}
                          onClick={() => handleActionClick(action)}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-50 px-3 py-1.5 text-[11px] font-bold text-teal-900 border border-teal-200 hover:bg-teal-100 btn-interactive"
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
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-900 border border-blue-200 text-xs font-bold mt-0.5 anim-badge-pop">
                    <UserIcon size={14} />
                  </div>
                )}
              </div>
            ))}

            {loading && statusStage && (
              <div className="anim-fade-up">
                <ThinkingIndicator label={statusStage} />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Chips */}
          {messages.length <= 2 && (
            <div className="p-3 border-t border-slate-100 bg-white space-y-1.5 anim-fade-up">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                {t("assistant.suggestedPrompts")}
              </span>
              <div className="flex flex-wrap gap-1.5">
                {starterPrompts.map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSendMessage(prompt)}
                    className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-700 text-left btn-interactive"
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
});

export default CapabilityAssistant;
