"""
=============================================================================
TEST SUITE: Gemini → Groq → Mock Fallback System Design
=============================================================================

Tests every layer of the fallback design:

  Layer 1 — Unit: GroqLLMProvider  (init, generate, generate_json, stream)
  Layer 2 — Unit: FallbackLLMProvider  (cascade logic for all three methods)
  Layer 3 — Integration: factory.get_llm_provider()  (env-driven wiring)
  Layer 4 — Config: Settings.groq_api_key  (pydantic field parsing)
  Layer 5 — System: Full Gemini → Groq → Mock cascade end-to-end
  Layer 6 — System: GeminiLLMProvider raises on all-model failure
  Layer 7 — System: MockLLMProvider still works (regression guard)
  Layer 8 — LLMProvider base interface compliance
  Layer 9 — Import smoke tests

Run with:
    pytest tests/test_groq_fallback_system.py -v
=============================================================================
"""
import json
import os
import unittest.mock as mock
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ── helpers ──────────────────────────────────────────────────────────────────

def _make_groq_completion(text: str):
    """Build a minimal Groq ChatCompletion-like mock."""
    choice = MagicMock()
    choice.message.content = text
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def _make_groq_stream_chunk(text: str):
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = text
    return chunk


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — GroqLLMProvider unit tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGroqLLMProviderInit:
    def test_successful_init(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            MockGroq.return_value = MagicMock()
            p = GroqLLMProvider(api_key="gsk_test_key")
        assert p.is_available() is True
        assert p.model_name == "llama-3.3-70b-versatile"

    def test_custom_model(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq"):
            p = GroqLLMProvider(api_key="gsk_test", model="llama-3.1-8b-instant")
        assert p.model_name == "llama-3.1-8b-instant"

    def test_init_failure_marks_unavailable(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq", side_effect=Exception("bad key")):
            p = GroqLLMProvider(api_key="bad_key")
        assert p.is_available() is False

    def test_unavailable_provider_raises_on_generate(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq", side_effect=Exception("bad key")):
            p = GroqLLMProvider(api_key="bad_key")
        with pytest.raises(Exception, match="not properly configured"):
            p.generate("hello")

    def test_models_to_try_order(self):
        from app.ai.providers.groq_provider import GroqLLMProvider, _GROQ_MODELS
        with patch("app.ai.providers.groq_provider.Groq"):
            p = GroqLLMProvider(api_key="x", model="gemma2-9b-it")
        models = p._models_to_try()
        assert models[0] == "gemma2-9b-it"
        assert len(models) == len(set(models))
        for m in _GROQ_MODELS:
            assert m in models


class TestGroqLLMProviderGenerate:
    def test_generate_success_first_model(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.return_value = _make_groq_completion("Hello from Groq!")
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        result = p.generate("What is 2+2?")
        assert result == "Hello from Groq!"

    def test_generate_falls_to_next_model_on_error(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.side_effect = [
                Exception("rate limit"),
                _make_groq_completion("ok!"),
            ]
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        result = p.generate("test")
        assert result == "ok!"

    def test_generate_raises_when_all_models_fail(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.side_effect = Exception("all down")
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        with pytest.raises(Exception, match="Groq LLM error across all candidate models"):
            p.generate("test")


class TestGroqLLMProviderGenerateJson:
    def test_generate_json_success(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        payload = [{"question": "Q1", "answer": "A"}]
        raw_text = json.dumps({"questions": payload})
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.return_value = _make_groq_completion(raw_text)
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        result = p.generate_json("generate questions")
        assert result == payload

    def test_generate_json_strips_markdown_fences(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        payload = {"key": "value"}
        raw_text = "```json\n" + json.dumps(payload) + "\n```"
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.return_value = _make_groq_completion(raw_text)
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        result = p.generate_json("gimme json")
        assert result == payload

    def test_generate_json_raises_on_all_model_failure(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.side_effect = Exception("overloaded")
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        with pytest.raises(Exception, match="Groq JSON generation failed"):
            p.generate_json("test")


class TestGroqLLMProviderStream:
    def test_generate_stream_yields_chunks(self):
        from app.ai.providers.groq_provider import GroqLLMProvider
        c1 = _make_groq_stream_chunk("Hello ")
        c2 = _make_groq_stream_chunk("world")
        c1.choices[0].delta.content = "Hello "
        c2.choices[0].delta.content = "world"
        with patch("app.ai.providers.groq_provider.Groq") as MockGroq:
            client = MagicMock()
            client.chat.completions.create.return_value = iter([c1, c2])
            MockGroq.return_value = client
            p = GroqLLMProvider(api_key="gsk_test")
        result = list(p.generate_stream("hi"))
        assert "Hello " in result
        assert "world" in result


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — FallbackLLMProvider cascade logic
# ══════════════════════════════════════════════════════════════════════════════

class TestFallbackLLMProviderGenerate:
    def test_returns_primary_when_gemini_works(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate.return_value = "from gemini"
        secondary = MagicMock()
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        assert provider.generate("test") == "from gemini"
        secondary.generate.assert_not_called()

    def test_falls_back_to_groq_when_gemini_fails(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate.side_effect = Exception("Gemini quota exceeded")
        secondary = MagicMock()
        secondary.generate.return_value = "from groq"
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        assert provider.generate("test") == "from groq"

    def test_falls_back_to_mock_when_both_fail(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate.side_effect = Exception("Gemini down")
        secondary = MagicMock()
        secondary.generate.side_effect = Exception("Groq down")
        mock_p = MagicMock()
        mock_p.generate.return_value = "from offline mock"
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        with patch.object(provider, "_get_mock", return_value=mock_p):
            result = provider.generate("test")
        assert result == "from offline mock"

    def test_is_available_true_if_any_provider_available(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock(); primary.is_available.return_value = False
        secondary = MagicMock(); secondary.is_available.return_value = True
        assert FallbackLLMProvider(primary=primary, secondary=secondary).is_available() is True

    def test_is_available_false_if_all_unavailable(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock(); primary.is_available.return_value = False
        secondary = MagicMock(); secondary.is_available.return_value = False
        assert FallbackLLMProvider(primary=primary, secondary=secondary).is_available() is False


class TestFallbackLLMProviderGenerateJson:
    def test_returns_primary_json(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate_json.return_value = [{"q": "1"}]
        secondary = MagicMock()
        result = FallbackLLMProvider(primary=primary, secondary=secondary).generate_json("test")
        assert result == [{"q": "1"}]
        secondary.generate_json.assert_not_called()

    def test_falls_back_to_groq_json_when_gemini_fails(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate_json.side_effect = Exception("RESOURCE_EXHAUSTED")
        secondary = MagicMock()
        secondary.generate_json.return_value = [{"q": "groq answer"}]
        result = FallbackLLMProvider(primary=primary, secondary=secondary).generate_json("test")
        assert result == [{"q": "groq answer"}]

    def test_falls_back_to_mock_json_when_both_fail(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock(); primary.generate_json.side_effect = Exception("gemini 503")
        secondary = MagicMock(); secondary.generate_json.side_effect = Exception("groq 429")
        mock_p = MagicMock(); mock_p.generate_json.return_value = {"offline": True}
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        with patch.object(provider, "_get_mock", return_value=mock_p):
            result = provider.generate_json("test")
        assert result == {"offline": True}

    def test_gemini_returns_none_falls_to_groq(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock(); primary.generate_json.return_value = None
        secondary = MagicMock(); secondary.generate_json.return_value = [{"q": "from groq"}]
        result = FallbackLLMProvider(primary=primary, secondary=secondary).generate_json("test")
        assert result == [{"q": "from groq"}]


class TestFallbackLLMProviderStream:
    def test_yields_gemini_stream_when_working(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate_stream.return_value = iter(["chunk1 ", "chunk2"])
        secondary = MagicMock()
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        result = list(provider.generate_stream("hi"))
        assert result == ["chunk1 ", "chunk2"]
        secondary.generate_stream.assert_not_called()

    def test_falls_back_to_groq_stream_when_gemini_fails(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        primary = MagicMock()
        primary.generate_stream.side_effect = Exception("Gemini stream error")
        secondary = MagicMock()
        secondary.generate_stream.return_value = iter(["groq chunk"])
        provider = FallbackLLMProvider(primary=primary, secondary=secondary)
        result = list(provider.generate_stream("hi"))
        assert result == ["groq chunk"]


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — Factory wiring
# ══════════════════════════════════════════════════════════════════════════════

class TestFactoryProviderResolution:
    def test_mock_provider_when_provider_is_mock(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        from app.ai.providers.mock_provider import MockLLMProvider
        settings = Settings(LLM_PROVIDER="mock", LLM_API_KEY="", MONGODB_URI="mongodb://localhost:27017")
        assert isinstance(get_llm_provider(settings=settings), MockLLMProvider)

    def test_gemini_only_when_no_groq_key(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        with patch("app.ai.providers.factory.GeminiLLMProvider") as MockGemini:
            mock_instance = MagicMock(spec=GeminiLLMProvider)
            MockGemini.return_value = mock_instance
            settings = Settings(LLM_PROVIDER="gemini", LLM_API_KEY="gemini_key_123", MONGODB_URI="mongodb://localhost:27017")
            with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
                provider = get_llm_provider(settings=settings)
        assert provider is mock_instance

    def test_fallback_provider_when_groq_key_set(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        with patch("app.ai.providers.factory.GeminiLLMProvider"), \
             patch("app.ai.providers.factory.GroqLLMProvider"):
            settings = Settings(LLM_PROVIDER="gemini", LLM_API_KEY="gemini_key", GROQ_API_KEY="gsk_test", MONGODB_URI="mongodb://localhost:27017")
            with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=False):
                provider = get_llm_provider(settings=settings)
        assert isinstance(provider, FallbackLLMProvider)

    def test_groq_standalone_provider(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        from app.ai.providers.groq_provider import GroqLLMProvider
        with patch("app.ai.providers.factory.GroqLLMProvider") as MockGroq:
            mock_instance = MagicMock(spec=GroqLLMProvider)
            MockGroq.return_value = mock_instance
            settings = Settings(LLM_PROVIDER="groq", MONGODB_URI="mongodb://localhost:27017")
            with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_standalone"}, clear=False):
                provider = get_llm_provider(settings=settings)
        assert provider is mock_instance

    def test_mock_fallback_when_groq_has_no_key(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        from app.ai.providers.mock_provider import MockLLMProvider
        settings = Settings(LLM_PROVIDER="groq", MONGODB_URI="mongodb://localhost:27017")
        env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
        env["GROQ_API_KEY"] = ""
        with patch.dict(os.environ, env, clear=True):
            provider = get_llm_provider(settings=settings)
        assert isinstance(provider, MockLLMProvider)

    def test_unknown_provider_raises(self):
        from app.ai.providers.factory import get_llm_provider
        from app.core.config import Settings
        settings = Settings(LLM_PROVIDER="anthropic", MONGODB_URI="mongodb://localhost:27017")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider(settings=settings)


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 4 — Config / Settings
# ══════════════════════════════════════════════════════════════════════════════

class TestSettingsConfig:
    def test_groq_api_key_defaults_empty(self):
        from app.core.config import Settings
        s = Settings(MONGODB_URI="mongodb://localhost:27017")
        assert s.groq_api_key == ""

    def test_groq_api_key_reads_from_env(self):
        from app.core.config import Settings
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_from_env"}, clear=False):
            s = Settings(MONGODB_URI="mongodb://localhost:27017")
        assert s.groq_api_key == "gsk_from_env"

    def test_settings_has_groq_api_key_field(self):
        from app.core.config import Settings
        s = Settings(MONGODB_URI="mongodb://localhost:27017")
        assert hasattr(s, "groq_api_key")

    def test_groq_api_key_can_be_set_directly(self):
        from app.core.config import Settings
        s = Settings(GROQ_API_KEY="direct_key", MONGODB_URI="mongodb://localhost:27017")
        assert s.groq_api_key == "direct_key"


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 5 — Full end-to-end cascade system tests
# ══════════════════════════════════════════════════════════════════════════════

class TestEndToEndFallbackCascade:
    def test_gemini_quota_exceeded_groq_succeeds(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        from app.ai.providers.groq_provider import GroqLLMProvider
        from app.ai.providers.fallback_provider import FallbackLLMProvider

        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        groq_client = MagicMock()
        groq_client.chat.completions.create.return_value = _make_groq_completion("Groq answered.")

        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client), \
             patch("app.ai.providers.groq_provider.Groq", return_value=groq_client):
            gemini_p = GeminiLLMProvider(api_key="gemini_key", model="gemini-2.0-flash")
            groq_p = GroqLLMProvider(api_key="gsk_test")
            provider = FallbackLLMProvider(primary=gemini_p, secondary=groq_p)

        result = provider.generate("Explain RAG architectures.")
        assert "Groq answered" in result

    def test_gemini_server_error_groq_succeeds(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        from app.ai.providers.groq_provider import GroqLLMProvider
        from app.ai.providers.fallback_provider import FallbackLLMProvider

        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("503 Service Unavailable")
        groq_client = MagicMock()
        groq_client.chat.completions.create.return_value = _make_groq_completion("Groq saved the day on 503.")

        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client), \
             patch("app.ai.providers.groq_provider.Groq", return_value=groq_client):
            gemini_p = GeminiLLMProvider(api_key="key")
            groq_p = GroqLLMProvider(api_key="gsk")
            provider = FallbackLLMProvider(primary=gemini_p, secondary=groq_p)

        assert "Groq saved" in provider.generate("test 503")

    def test_both_fail_uses_offline_mock(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        from app.ai.providers.groq_provider import GroqLLMProvider
        from app.ai.providers.fallback_provider import FallbackLLMProvider

        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("Gemini down")
        groq_client = MagicMock()
        groq_client.chat.completions.create.side_effect = Exception("Groq also down")

        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client), \
             patch("app.ai.providers.groq_provider.Groq", return_value=groq_client):
            gemini_p = GeminiLLMProvider(api_key="key")
            groq_p = GroqLLMProvider(api_key="gsk")
            provider = FallbackLLMProvider(primary=gemini_p, secondary=groq_p)

        result = provider.generate("test all-fail")
        assert isinstance(result, str) and len(result) > 0

    def test_json_cascade_gemini_fails_groq_returns_valid_json(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        from app.ai.providers.groq_provider import GroqLLMProvider
        from app.ai.providers.fallback_provider import FallbackLLMProvider

        questions_payload = [{"question": "What is RAG?", "options": ["A","B","C","D"], "correct_answer": "A", "explanation": "test", "difficulty": "MEDIUM", "bloom_level": "UNDERSTAND"}]
        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("quota")
        groq_client = MagicMock()
        groq_client.chat.completions.create.return_value = _make_groq_completion(json.dumps({"questions": questions_payload}))

        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client), \
             patch("app.ai.providers.groq_provider.Groq", return_value=groq_client):
            gemini_p = GeminiLLMProvider(api_key="key")
            groq_p = GroqLLMProvider(api_key="gsk")
            provider = FallbackLLMProvider(primary=gemini_p, secondary=groq_p)

        result = provider.generate_json("generate MCQs")
        assert result == questions_payload


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 6 — GeminiLLMProvider regression: must raise (not swallow) on failure
# ══════════════════════════════════════════════════════════════════════════════

class TestGeminiProviderRaisesOnFailure:
    def test_generate_json_raises_when_all_gemini_models_fail(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("all failed")
        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client):
            p = GeminiLLMProvider(api_key="key", model="gemini-2.0-flash")
        with pytest.raises(Exception, match="Gemini JSON generation failed"):
            p.generate_json("test prompt")

    def test_generate_raises_when_all_gemini_models_fail(self):
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        gemini_client = MagicMock()
        gemini_client.models.generate_content.side_effect = Exception("503")
        with patch("app.ai.providers.gemini_provider.genai.Client", return_value=gemini_client):
            p = GeminiLLMProvider(api_key="key", model="gemini-2.0-flash")
        with pytest.raises(Exception, match="Gemini LLM error across all candidate models"):
            p.generate("test prompt")


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 7 — MockLLMProvider still works (regression guard)
# ══════════════════════════════════════════════════════════════════════════════

class TestMockProviderRegression:
    def test_mock_generate_returns_string(self):
        from app.ai.providers.mock_provider import MockLLMProvider
        result = MockLLMProvider().generate("test prompt")
        assert isinstance(result, str) and len(result) > 0

    def test_mock_generate_json_returns_list_or_dict(self):
        from app.ai.providers.mock_provider import MockLLMProvider
        result = MockLLMProvider().generate_json("generate some json")
        assert isinstance(result, (list, dict))

    def test_mock_is_available(self):
        from app.ai.providers.mock_provider import MockLLMProvider
        assert MockLLMProvider().is_available() is True

    def test_fallback_provider_lazy_loads_mock(self):
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        provider = FallbackLLMProvider(primary=MagicMock(), secondary=MagicMock())
        assert provider._mock is None
        mock1 = provider._get_mock()
        mock2 = provider._get_mock()
        assert mock1 is mock2  # same instance (lazy singleton)


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 8 — LLMProvider base interface compliance
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMProviderBaseCompliance:
    def test_groq_is_subclass_of_llm_provider(self):
        from app.ai.providers.base import LLMProvider
        from app.ai.providers.groq_provider import GroqLLMProvider
        assert issubclass(GroqLLMProvider, LLMProvider)

    def test_fallback_is_subclass_of_llm_provider(self):
        from app.ai.providers.base import LLMProvider
        from app.ai.providers.fallback_provider import FallbackLLMProvider
        assert issubclass(FallbackLLMProvider, LLMProvider)

    def test_gemini_is_subclass_of_llm_provider(self):
        from app.ai.providers.base import LLMProvider
        from app.ai.providers.gemini_provider import GeminiLLMProvider
        assert issubclass(GeminiLLMProvider, LLMProvider)

    def test_mock_is_subclass_of_llm_provider(self):
        from app.ai.providers.base import LLMProvider
        from app.ai.providers.mock_provider import MockLLMProvider
        assert issubclass(MockLLMProvider, LLMProvider)

    def test_openai_is_subclass_of_llm_provider(self):
        from app.ai.providers.base import LLMProvider
        from app.ai.providers.openai_provider import OpenAIProvider
        assert issubclass(OpenAIProvider, LLMProvider)


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 9 — Import smoke tests
# ══════════════════════════════════════════════════════════════════════════════

class TestImportSmoke:
    def test_groq_provider_imports(self):
        import app.ai.providers.groq_provider  # noqa: F401

    def test_fallback_provider_imports(self):
        import app.ai.providers.fallback_provider  # noqa: F401

    def test_factory_imports(self):
        import app.ai.providers.factory  # noqa: F401

    def test_all_providers_importable(self):
        from app.ai.providers.groq_provider import GroqLLMProvider  # noqa: F401
        from app.ai.providers.fallback_provider import FallbackLLMProvider  # noqa: F401
        from app.ai.providers.gemini_provider import GeminiLLMProvider  # noqa: F401
        from app.ai.providers.mock_provider import MockLLMProvider  # noqa: F401
