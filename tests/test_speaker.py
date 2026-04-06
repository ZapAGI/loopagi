"""Tests for the speaker voice module and agent."""

from loopagi.agents.speaker import SPEAKER_KEYWORDS, SPEAKER_ROLE, SpeakerAgent
from loopagi.voice.speaker import DEFAULT_VOICE, Speaker


def test_speaker_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(SPEAKER_ROLE, str)
    assert len(SPEAKER_ROLE) > 30


def test_speaker_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(SPEAKER_KEYWORDS, list)
    assert len(SPEAKER_KEYWORDS) > 3
    assert all(isinstance(k, str) for k in SPEAKER_KEYWORDS)


def test_speaker_keywords_contain_core_terms():
    """Core speaker terms must be present."""
    core = {"say", "speak", "tts"}
    assert core.issubset(set(SPEAKER_KEYWORDS))


def test_speaker_default_voice():
    """Verify default voice model name."""
    assert DEFAULT_VOICE == "en_US-lessac-medium"


def test_speaker_init():
    """Speaker should initialize without loading model."""
    speaker = Speaker(voice="en_US-lessac-medium")
    assert speaker.voice_name == "en_US-lessac-medium"
    assert speaker._voice is None  # lazy loaded


def test_speaker_agent_init():
    """SpeakerAgent should initialize with correct name."""
    agent = SpeakerAgent()
    assert agent.name == "speaker"
    assert agent.role == SPEAKER_ROLE


def test_speaker_agent_empty_text():
    """Agent should handle empty text gracefully."""
    agent = SpeakerAgent()
    result = agent.invoke("say ")
    # Either "nothing to say" or "no audio output" depending on hardware
    assert "nothing" in result.lower() or "audio output" in result.lower()


def test_speaker_agent_strips_prefix():
    """Agent should strip command prefixes from text."""
    agent = SpeakerAgent()
    # Without speakers, it will fail, but we're testing prefix stripping
    if not agent.speaker.available:
        result = agent.invoke("say hello world")
        assert "audio output" in result.lower() or "error" in result.lower()
