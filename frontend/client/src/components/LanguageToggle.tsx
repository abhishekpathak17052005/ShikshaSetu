import React from "react";
import { Globe } from "lucide-react";
import { useTranslation, LANGUAGES } from "@/i18n";

export function LanguageToggle() {
  const { language, setLanguage } = useTranslation();

  return (
    <div className="flex items-center rounded-xl border border-slate-200/80 bg-white/90 p-1 shadow-sm backdrop-blur-sm">
      <div className="flex items-center gap-1 px-1.5 text-slate-400">
        <Globe size={14} className="text-[#087f76]" />
      </div>
      {LANGUAGES.map((lang) => {
        const isActive = language === lang.code;
        return (
          <button
            key={lang.code}
            type="button"
            onClick={() => setLanguage(lang.code)}
            className={`rounded-lg px-2.5 py-1 text-xs font-bold transition-all ${
              isActive
                ? "bg-[#123057] text-white shadow-sm"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
            title={`Switch to ${lang.name}`}
          >
            {lang.nativeName}
          </button>
        );
      })}
    </div>
  );
}

export default LanguageToggle;
