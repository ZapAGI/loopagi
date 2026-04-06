"""Tests for the listener voice module and agent."""

from loopagi.agents.listener import LISTENER_KEYWORDS, LISTENER_ROLE, ListenerAgent
from loopagi.voice.listener import DEFAULT_MODEL_SIZE, DEFAULT_SAMPLE_RATE, Listener


def test_listener_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(LISTENER_ROLE, str)
    assert len(LISTENER_ROLE) > 30


def test_listener_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(LISTENER_KEYWORDS, list)
    assert len(LISTENER_KEYWORDS) > 3
    assert all(isinstance(k, str) for k in LISTENER_KEYWORDS)


def test_listener_keywords_contain_core_terms():
    """Core listener terms must be present."""
    core = {"listen", "microphone", "stt"}
    assert core.issubset(set(LISTENER_KEYWORDS))


def test_listener_defaults():
    """Verify listener default configuration."""
    assert DEFAULT_MODEL_SIZE == "base.en"
    assert DEFAULT_SAMPLE_RATE == 16000


def test_listener_init():
    """Listener should initialize without loading model."""
    listener = Listener(model_size="tiny.en", device="cpu", compute_type="int8")
    assert listener.model_size == "tiny.en"
    assert listener.device == "cpu"
    assert listener._model is None  # lazy loaded


def test_listener_auto_detect():
    """Listener with 'auto' device should resolve to cpu or cuda."""
    listener = Listener(model_size="tiny.en")
    assert listener.device in ("cpu", "cuda")


def test_listener_agent_init():
    """ListenerAgent should initialize with correct name."""
    agent = ListenerAgent(model_size="tiny.en")
    assert agent.name == "listener"
    assert agent.role == LISTENER_ROLE


def test_listener_agent_no_mic():
    """Agent should return helpful message when mic unavailable."""
    agent = ListenerAgent(model_size="tiny.en")
    # On CI/test environments, mic is usually unavailable
    if not agent.listener.available:
        result = agent.invoke("listen")
        assert "microphone" in result.lower() or "no " in result.lower()
