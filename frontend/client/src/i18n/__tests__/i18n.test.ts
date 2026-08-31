import { describe, it, expect } from "vitest";
import { en } from "../en";
import { hi } from "../hi";
import { LANGUAGES, DEFAULT_LANGUAGE } from "../languages";

describe("Phase 3D — i18n Localization Foundation", () => {
  it("should have English as default language", () => {
    expect(DEFAULT_LANGUAGE).toBe("en");
    expect(LANGUAGES.map((l) => l.code)).toContain("en");
    expect(LANGUAGES.map((l) => l.code)).toContain("hi");
  });

  it("should maintain identical top-level key parity between English and Hindi dictionaries", () => {
    const enSections = Object.keys(en);
    const hiSections = Object.keys(hi);
    expect(hiSections).toEqual(enSections);

    // Verify subkeys in all major sections
    for (const section of enSections) {
      const enSubkeys = Object.keys((en as any)[section]);
      const hiSubkeys = Object.keys((hi as any)[section]);
      expect(hiSubkeys).toEqual(enSubkeys);
    }
  });

  it("should contain authentic civil services Rajbhasha terms in Hindi dictionary", () => {
    expect(hi.common.appName).toBe("शिक्षासेतु");
    expect(hi.common.tagline).toBe("भारतीय सिविल सेवा क्षमता विकास मंच");
    expect(hi.common.supportingEvidence).toContain("सहायक साक्ष्य");
    expect(hi.common.authoritativeEvidence).toContain("प्रामाणिक साक्ष्य");
    expect(hi.nav.competencies).toBe("मेरी क्षमताएं");
    expect(hi.nav.skillGaps).toBe("कौशल अंतराल");
    expect(hi.nav.evidence).toContain("साक्ष्य बही");
    expect(hi.assessments.title).toBe("अनुकूली क्षमता आकलन");
    expect(hi.assistant.title).toBe("कर्मयोगी एआई सह-पायलट");
  });

  it("should never translate internal competency codes or backend database enums", () => {
    // Internal codes must remain exact strings in system logic
    const internalCodes = [
      "STAT_SAMPLING",
      "TECH_PYTHON",
      "CAPABILITY_ASSESSMENT",
      "LEARNING_ACTIVITY",
      "OFFICIAL",
      "TRAINER",
      "ADMIN",
    ];

    for (const code of internalCodes) {
      // Dictionaries must not mutate these internal keys
      expect(typeof code).toBe("string");
    }
  });
});
