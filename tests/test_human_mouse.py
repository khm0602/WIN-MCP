import math
import random

from windows_mcp.desktop import human_mouse


def _path(start, end, seed, **kw):
    return human_mouse.plan(start, end, rng=random.Random(seed), **kw)


def test_ends_exactly_on_target():
    for seed in range(50):
        steps = _path((10, 10), (1500, 900), seed)
        assert steps[-1][:2] == (1500, 900)


def test_path_is_not_a_straight_line():
    bent = 0
    for seed in range(30):
        steps = _path((0, 0), (1000, 0), seed, allow_overshoot=False)
        if max(abs(y) for _, y, _ in steps) >= 10:
            bent += 1
    assert bent >= 25


def test_speed_rises_then_falls_and_varies():
    steps = _path((0, 0), (1200, 300), 3, allow_overshoot=False)
    pts = [(0, 0)] + [(x, y) for x, y, _ in steps]
    speeds = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    third = len(speeds) // 3
    middle = sum(speeds[third : 2 * third]) / third
    assert middle > 2 * (sum(speeds[:5]) / 5)
    assert middle > 2 * (sum(speeds[-5:]) / 5)
    waits = {round(w, 5) for _, _, w in steps}
    assert len(waits) > len(steps) // 2  # step timing is not uniform


def test_duration_scales_with_distance_and_is_capped():
    rng = random.Random(1)
    short = sum(w for *_, w in human_mouse.plan((0, 0), (40, 0), rng=rng, allow_overshoot=False))
    long_ = sum(w for *_, w in human_mouse.plan((0, 0), (2500, 0), rng=rng, allow_overshoot=False))
    assert 0.05 < short < long_ < 2.0


def test_explicit_duration_is_respected():
    steps = _path((0, 0), (800, 400), 7, duration=1.0, allow_overshoot=False)
    assert 0.8 < sum(w for *_, w in steps) < 1.2


def test_tiny_move_is_single_step():
    assert _path((5, 5), (6, 5), 0) == [(6, 5, 0.0)]


def test_overshoot_sometimes_passes_target_then_corrects():
    passed = 0
    for seed in range(60):
        steps = _path((0, 500), (1000, 500), seed)
        if max(x for x, _, _ in steps) > 1003:
            passed += 1
        assert steps[-1][:2] == (1000, 500)
    assert 5 <= passed <= 40


def test_glide_drives_callbacks_and_can_be_disabled(monkeypatch):
    seen, calls = [], []
    human_mouse.glide(
        (0, 0),
        (300, 200),
        lambda x, y: seen.append((x, y)),
        before_step=lambda: calls.append("b"),
        after_step=lambda: calls.append("a"),
        sleeper=lambda s: None,
    )
    assert seen[-1] == (300, 200)
    assert calls.count("b") == calls.count("a") == len(seen)
    monkeypatch.setenv("WINDOWS_MCP_HUMAN_MOUSE", "0")
    assert not human_mouse.enabled()
    monkeypatch.setenv("WINDOWS_MCP_HUMAN_MOUSE", "1")
    assert human_mouse.enabled()


def test_jitter_stays_within_limit_and_varies():
    rng = random.Random(4)
    pts = {human_mouse.jitter_point(500, 500, rng) for _ in range(300)}
    assert len(pts) > 20
    assert all(abs(x - 500) <= 4 and abs(y - 500) <= 4 for x, y in pts)
    assert (500, 500) in pts or len(pts) > 30


def test_click_hold_is_human_range():
    rng = random.Random(5)
    holds = [human_mouse.click_hold(rng) for _ in range(200)]
    assert all(0.05 <= h <= 0.16 for h in holds)
    assert max(holds) - min(holds) > 0.03


def test_key_gaps_uneven_with_pauses_after_punctuation():
    text = "hello world. this is a test, ok"
    gaps = human_mouse.key_gaps(text, random.Random(6))
    assert len(gaps) == len(text)
    assert all(0.012 <= g <= 0.45 for g in gaps)
    assert len({round(g, 3) for g in gaps}) > len(text) // 2
    dot = text.index(".")
    letters = [g for ch, g in zip(text, gaps) if ch.isalpha()]
    assert gaps[dot] > sorted(letters)[len(letters) // 2]


def test_key_gaps_keep_typing_quick():
    text = "가나다라마바사 아자차카타파하 " * 7  # ~100 chars
    total = sum(human_mouse.key_gaps(text, random.Random(11)))
    assert 2.0 <= total <= 6.0


def test_scroll_gaps_come_in_flicks():
    gaps = human_mouse.scroll_gaps(20, random.Random(8))
    assert len(gaps) == 20
    pauses = [g for g in gaps if g >= 0.15]
    quick = [g for g in gaps if g < 0.08]
    assert 3 <= len(pauses) <= 10 and len(quick) >= 10
