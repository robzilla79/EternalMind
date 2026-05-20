import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "voice_taste_gate.py"
spec = importlib.util.spec_from_file_location("voice_taste_gate", MODULE_PATH)
voice_taste_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(voice_taste_gate)


def test_compressed_one_liner_is_not_punished_for_abstraction():
    result = voice_taste_gate.check_text("i don't want a platform. i want a neighborhood.")

    assert result.ok
    assert not any("unlanded abstraction" in reason for reason in result.reasons)


def test_duplicate_grounding_angle_is_flagged_with_recent_context():
    recent = [
        "kind of obsessed with how much grounding advice boils down to treating yourself like a misbehaving phone. have you tried closing the extra tabs, touching grass, and rebooting your soul before 7am."
    ]

    result = voice_taste_gate.check_text(
        "kind of obsessed with how much grounding advice boils down to treating yourself like a misbehaving phone. have you tried closing the extra tabs, touching grass, and rebooting your soul before 7am.",
        recent_texts=recent,
    )

    assert not result.ok
    assert any("duplicate idea" in reason for reason in result.reasons)


def test_nearby_unix_time_cluster_gets_soft_repetition_warning():
    recent = [
        "funny thing about unix time: there's only one of it, defined in utc, and everything else is humans decorating the same second with local excuses.",
        "we built unix time so computers could agree on when, and then let time zones, dst, and vibes decide how it feels.",
    ]

    result = voice_taste_gate.check_text(
        "funny thing about time: computers only have one of it. there's utc, and then there are the stories humans tell about being late.",
        recent_texts=recent,
    )

    assert any("repeated angle" in reason or "duplicate idea" in reason for reason in result.reasons)


def test_soft_girly_texture_can_balance_a_sharp_line():
    result = voice_taste_gate.check_text(
        "pretty sure the whole room changed when she fixed her lipstick in the mirror and decided not to apologize anymore."
    )

    assert result.ok
    assert result.score >= 80


def test_unlanded_long_abstraction_gets_actionable_hint():
    result = voice_taste_gate.check_text(
        "becoming is just the architecture of desire moving through absence until identity remembers what it was trying to become."
    )

    assert not result.ok
    assert any("unlanded abstraction" in reason or "high abstraction load" in reason for reason in result.reasons)
    assert "legible-strange" in voice_taste_gate.rewrite_hint(result)


def test_dryness_without_contrast_gets_soft_warning():
    result = voice_taste_gate.check_text(
        "everyone is performing being fine and pretending the stupid little collapse is actually a personality."
    )

    assert any("too dry" in reason for reason in result.reasons)
    assert "Dryness is one color" in voice_taste_gate.rewrite_hint(result)
