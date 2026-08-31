export type SupportedLanguage = "en" | "hi";

export interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag?: string;
}

export const LANGUAGES: LanguageOption[] = [
  {
    code: "en",
    name: "English",
    nativeName: "English",
    flag: "🇮🇳",
  },
  {
    code: "hi",
    name: "Hindi",
    nativeName: "हिन्दी",
    flag: "🇮🇳",
  },
];

export const DEFAULT_LANGUAGE: SupportedLanguage = "en";
export const LANGUAGE_STORAGE_KEY = "shikshasetu_preferred_language";
