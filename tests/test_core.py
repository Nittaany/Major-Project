"""
Hardware-free unit tests for Jarvis-EcoSign core logic.

No webcam, no real MediaPipe/TensorFlow/OpenCV, no network or LLM calls.
Heavy third-party modules are stubbed ONLY while ISL_Controller is imported.

Run from repo root:  pytest -v
"""
import importlib.util
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")


def _load(name, relpath, stub_modules=()):
    """Load a source file by path (no package assumptions), optionally stubbing deps."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, relpath))
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {m: MagicMock() for m in stub_modules}):
        spec.loader.exec_module(mod)
    return mod


norm_mod = _load("norm_mod", "utils/normalization.py")
math_mod = _load("math_mod", "utils/math_utils.py")
isl_mod = _load(
    "isl_mod", "controllers/ISL_Controller.py",
    stub_modules=("mediapipe", "cv2", "tensorflow", "tflite_runtime",
                  "tflite_runtime.interpreter"),
)

normalize_features = norm_mod.normalize_features
OneEuroFilter = math_mod.OneEuroFilter
SigmoidController = math_mod.SigmoidController
parse_intent = isl_mod.parse_intent


# ───────────────────────── helpers ─────────────────────────
def _lm(arr):
    return SimpleNamespace(landmark=[SimpleNamespace(x=float(p[0]), y=float(p[1]), z=float(p[2]))
                                     for p in arr])


def make_results(pose, lh=None, rh=None):
    return SimpleNamespace(
        pose_landmarks=_lm(pose) if pose is not None else None,
        left_hand_landmarks=_lm(lh) if lh is not None else None,
        right_hand_landmarks=_lm(rh) if rh is not None else None,
    )


def random_body(seed=0, shoulder_width=0.3):
    rng = np.random.default_rng(seed)
    pose = rng.uniform(0.2, 0.8, (33, 3))
    pose[11] = [0.5 - shoulder_width / 2, 0.45, 0.0]   # left shoulder
    pose[12] = [0.5 + shoulder_width / 2, 0.45, 0.0]   # right shoulder
    lh = rng.uniform(0.2, 0.8, (21, 3))
    rh = rng.uniform(0.2, 0.8, (21, 3))
    return pose, lh, rh


# ═══════════════ 1. SHOULDER-INVARIANT NORMALIZATION ═══════════════
class TestNormalization:
    def test_output_shape_is_201(self):
        out = normalize_features(make_results(*random_body()))
        assert out.shape == (201,)  # 25*3 + 21*3 + 21*3

    def test_empty_results_returns_finite_201_zeros(self):
        out = normalize_features(make_results(None))
        assert out.shape == (201,)
        assert np.all(out == 0.0)

    @pytest.mark.parametrize("scale", [0.5, 1.7, 2.0])
    @pytest.mark.parametrize("shift", [(0.0, 0.0, 0.0), (0.1, -0.05, 0.02)])
    def test_scale_and_translation_invariance(self, scale, shift):
        pose, lh, rh = random_body(1)
        base = normalize_features(make_results(pose, lh, rh))
        t = np.array(shift)
        moved = normalize_features(make_results(pose * scale + t, lh * scale + t, rh * scale + t))
        np.testing.assert_allclose(base, moved, atol=1e-9)

    def test_chest_center_maps_to_origin(self):
        pose, lh, rh = random_body(2)
        out = normalize_features(make_results(pose, lh, rh)).reshape(-1, 3)
        # shoulders (idx 11, 12) should be symmetric about the origin, 1.0 apart
        np.testing.assert_allclose(out[11] + out[12], 0.0, atol=1e-9)
        assert np.linalg.norm(out[11] - out[12]) == pytest.approx(1.0)

    def test_zero_shoulder_distance_is_safe(self):
        pose, lh, rh = random_body(3, shoulder_width=0.0)  # both shoulders coincide
        with np.errstate(all="raise"):  # any div-by-zero would raise
            out = normalize_features(make_results(pose, lh, rh))
        assert out.shape == (201,)
        assert np.all(np.isfinite(out))

    def test_undetected_shoulders_falls_back_to_raw_finite(self):
        pose, lh, rh = random_body(4)
        pose[11] = 0.0
        pose[12] = 0.0
        out = normalize_features(make_results(pose, lh, rh))
        assert np.all(np.isfinite(out))

    def test_nan_input_is_neutralised_by_training_sanitisation(self):
        """normalize_features does not scrub NaN itself; the sanitisation contract
        (nan_to_num + clip(-5, 5)) used in training must yield a finite, bounded vector."""
        pose, lh, rh = random_body(5)
        lh[3] = np.nan
        pose[11] = np.nan  # worst case: NaN shoulder poisons the whole vector
        out = normalize_features(make_results(pose, lh, rh))
        clean = np.clip(np.nan_to_num(out), -5.0, 5.0)
        assert np.all(np.isfinite(clean))
        assert clean.min() >= -5.0 and clean.max() <= 5.0

    def test_utils_and_isl_controller_implementations_agree(self):
        """Guards against train/serve skew: ISL_Controller embeds its own copy."""
        for seed in range(5):
            res = make_results(*random_body(seed))
            np.testing.assert_allclose(normalize_features(res),
                                       isl_mod.normalize_features(res), atol=1e-12)


# ═══════════════════════ 2. MATH UTILITIES ═══════════════════════
class TestOneEuroFilter:
    def test_first_sample_passthrough(self):
        assert OneEuroFilter(1.0, 0.0)(5.0, 0.0) == 5.0

    def test_constant_signal_stays_constant(self):
        f = OneEuroFilter(min_cutoff=1.0, beta=0.5)
        outs = [f(3.0, i / 30) for i in range(60)]
        np.testing.assert_allclose(outs, 3.0, atol=1e-12)

    def test_reduces_jitter_variance(self):
        rng = np.random.default_rng(0)
        noisy = 100 + rng.normal(0, 2.0, 300)
        f = OneEuroFilter(min_cutoff=1.0, beta=0.0)
        smooth = np.array([f(x, i / 30) for i, x in enumerate(noisy)])
        assert smooth[30:].std() < 0.6 * noisy[30:].std()

    def test_step_response_is_monotonic_and_does_not_overshoot(self):
        f = OneEuroFilter(min_cutoff=1.0, beta=0.0)
        f(0.0, 0.0)
        outs = [f(10.0, (i + 1) / 30) for i in range(120)]
        assert all(b >= a for a, b in zip(outs, outs[1:]))
        assert max(outs) <= 10.0 + 1e-9
        assert outs[-1] == pytest.approx(10.0, abs=0.05)

    def test_higher_beta_means_less_lag_on_fast_motion(self):
        def run(beta):
            f = OneEuroFilter(min_cutoff=0.5, beta=beta)
            return [f(40.0 * i, i / 30) for i in range(30)][-1]
        truth = 40.0 * 29
        assert abs(truth - run(0.5)) < abs(truth - run(0.0))

    def test_duplicate_timestamp_does_not_crash_or_nan(self):
        f = OneEuroFilter(1.0, 0.1)
        f(1.0, 0.0)
        y = f(2.0, 0.0)  # t_e == 0
        assert np.isfinite(y)


class TestSigmoidController:
    def test_gain_bounds_across_velocity_range(self):
        c = SigmoidController(min_gain=1.0, max_gain=15.0, v_inf=25, k=0.2)
        gains = np.array([c.get_gain(v) for v in np.linspace(-200, 500, 400)])
        assert gains.min() >= 1.0 - 1e-9
        assert gains.max() <= 15.0 + 1e-9

    def test_asymptotes(self):
        c = SigmoidController(1.0, 15.0, 25, 0.2)
        assert c.get_gain(-200) == pytest.approx(1.0, abs=1e-3)
        assert c.get_gain(500) == pytest.approx(15.0, abs=1e-3)

    def test_midpoint_at_v_inf(self):
        c = SigmoidController(1.0, 15.0, 25, 0.2)
        assert c.get_gain(25) == pytest.approx(8.0)  # (min+max)/2

    def test_monotonic_increasing(self):
        c = SigmoidController()
        g = [c.get_gain(v) for v in range(0, 200, 5)]
        assert all(b >= a for a, b in zip(g, g[1:]))


# ═══════════════ 3. LINGUISTIC / INTENT PARSER ═══════════════
class TestParseIntent:
    @pytest.mark.parametrize("glosses, expected", [
        (["HELLO"], "Hello everyone."),
        (["THANK YOU"], "Thank you so much."),
        (["GOOD MORNING"], "Good morning to everyone."),
        (["TIME"], "What is the time?"),
        (["TIME", "YOU"], "Could you please tell me the current time?"),
        (["YOU", "HAPPY"], "Are you happy?"),
        (["YOU", "GOOD"], "Are you doing well?"),
        (["HELLO", "TEACHER"], "Hello, honorable teacher."),
        (["THANK YOU", "TEACHER"], "Thank you very much, respected teacher."),
        (["I", "TEACHER"], "I am a teacher."),
    ])
    def test_known_short_glosses_resolve_deterministically(self, glosses, expected):
        sentence, matched = parse_intent(glosses)
        assert matched is True
        assert sentence.strip() == expected

    def test_single_I_uses_user_name(self):
        sentence, matched = parse_intent(["I"], user_name="Asha")
        assert matched is True and "Asha" in sentence

    @pytest.mark.parametrize("glosses", [
        ["I", "YOU", "GOOD"],
        ["GOOD MORNING", "FATHER", "TIME"],
        ["TEACHER", "FATHER", "HAPPY", "HELLO"],
    ])
    def test_three_or_more_glosses_route_to_llm(self, glosses):
        sentence, matched = parse_intent(glosses)
        assert matched is False
        assert sentence.endswith((".", "?")) and sentence[0].isupper()

    @pytest.mark.parametrize("glosses", [["FATHER", "HAPPY"], ["GOOD"], ["FATHER", "TEACHER"]])
    def test_unknown_short_combinations_fall_back_to_llm(self, glosses):
        sentence, matched = parse_intent(glosses)
        assert matched is False
        assert sentence.endswith((".", "?"))

    def test_known_quirk_extra_word_is_dropped_by_greeting_rule(self):
        """Characterisation test: any 2-gloss buffer containing HELLO (other than
        TEACHER) collapses to the greeting and drops the second gloss. Update this
        test deliberately if the rule is tightened."""
        sentence, matched = parse_intent(["HELLO", "HAPPY"])
        assert matched is True and sentence == "Hello everyone."

    def test_fallback_uses_question_mark_when_you_or_time_present(self):
        sentence, matched = parse_intent(["I", "YOU"])
        assert matched is False and sentence.endswith("?")

    def test_fallback_applies_grammatical_ordering(self):
        sentence, matched = parse_intent(["HAPPY", "FATHER", "I"])  # >=3 -> LLM path
        assert matched is False
        assert sentence.lower().startswith("i father happy")

    def test_empty_buffer_does_not_crash(self):
        sentence, matched = parse_intent([])
        assert matched is False and isinstance(sentence, str)


class TestHelpers:
    def test_normalize_gloss_order_priority(self):
        assert isl_mod.normalize_gloss_order(["HELLO", "GOOD", "TIME", "FATHER", "YOU", "I"]) == \
            ["I", "YOU", "FATHER", "TIME", "GOOD", "HELLO"]

    def test_normalize_gloss_order_unknown_goes_last_and_is_stable(self):
        assert isl_mod.normalize_gloss_order(["ZEBRA", "I", "APPLE"]) == ["I", "ZEBRA", "APPLE"]

    @pytest.mark.parametrize("buf, expected", [
        ([], 3.0),
        (["I"], 6.0),
        (["I", "HAPPY"], 5.0),
        (["HELLO"], 3.5),
        (["GOOD", "TIME"], 4.0),
    ])
    def test_dynamic_timeout(self, buf, expected):
        assert isl_mod.calculate_dynamic_timeout(buf) == expected

    def test_dynamic_timeout_always_within_documented_range(self):
        for buf in ([], ["I"], ["YOU", "GOOD"], ["HELLO"], ["TIME", "GOOD", "HAPPY"]):
            assert 3.0 <= isl_mod.calculate_dynamic_timeout(buf) <= 6.0
