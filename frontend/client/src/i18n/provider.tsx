import React, { createContext, useContext, useEffect, useState } from "react";
import {
  SupportedLanguage,
  DEFAULT_LANGUAGE,
  LANGUAGE_STORAGE_KEY,
  LANGUAGES,
} from "./languages";
import { en } from "./en";
import { hi } from "./hi";

type TranslationDictionary = typeof en;

interface LanguageContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (path: string, params?: Record<string, string | number>) => string;
  isHindi: boolean;
}

const dictionaries: Record<SupportedLanguage, TranslationDictionary> = {
  en,
  hi,
};

export const LanguageContext = createContext<LanguageContextType>({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => {},
  t: (path: string) => path,
  isHindi: false,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY) as SupportedLanguage;
    if (saved && (saved === "en" || saved === "hi")) {
      return saved;
    }
    return DEFAULT_LANGUAGE;
  });

  const setLanguage = (lang: SupportedLanguage) => {
    setLanguageState(lang);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    document.documentElement.lang = lang;
  };

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const t = (path: string, params?: Record<string, string | number>): string => {
    const keys = path.split(".");
    let current: any = dictionaries[language] || dictionaries.en;

    for (const key of keys) {
      if (current && typeof current === "object" && key in current) {
        current = current[key];
      } else {
        // Fallback to English dictionary if key missing in current language
        let fallback: any = dictionaries.en;
        for (const fbKey of keys) {
          if (fallback && typeof fallback === "object" && fbKey in fallback) {
            fallback = fallback[fbKey];
          } else {
            return path; // Return raw path key if missing
          }
        }
        current = fallback;
        break;
      }
    }

    if (typeof current !== "string") {
      return path;
    }

    if (params) {
      let result = current;
      for (const [pKey, pVal] of Object.entries(params)) {
        result = result.replace(new RegExp(`{${pKey}}`, "g"), String(pVal));
      }
      return result;
    }

    return current;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        isHindi: language === "hi",
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};
