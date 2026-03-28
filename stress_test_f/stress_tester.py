import streamlit as st
import random
import subprocess
import tempfile
import os
import string
import math
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Stress Tester", layout="wide")

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@700&display=swap');
html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; background-color: #0a0a0f; color: #e0e0ff; }
.stApp { background: #0a0a0f; }
h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc; text-shadow: 0 0 20px #00ffcc88; }
h2, h3 { color: #7faaff; }
.stButton > button {
    background: linear-gradient(135deg, #00ffcc22, #7f00ff22);
    border: 1px solid #00ffcc66; color: #00ffcc;
    font-family: 'JetBrains Mono', monospace; font-weight: 700;
    letter-spacing: 2px; padding: 12px 32px; transition: all 0.2s;
}
.stButton > button:hover { background: linear-gradient(135deg,#00ffcc44,#7f00ff44); box-shadow: 0 0 20px #00ffcc55; }
.stSelectbox > div, .stTextInput > div, .stTextArea > div { background: #111128 !important; border-color: #333366 !important; color: #e0e0ff !important; }
.stTabs [data-baseweb="tab"] { font-family: 'JetBrains Mono', monospace; color: #7faaff; }
.stTabs [aria-selected="true"] { color: #00ffcc; border-bottom: 2px solid #00ffcc; }
.stProgress > div > div { background: linear-gradient(90deg, #00ffcc, #7f00ff); }
div[data-testid="stExpander"] { border: 1px solid #333366; border-radius: 6px; background: #111128; }
.upload-box { border: 1px dashed #333366; border-radius: 6px; padding: 8px; background: #0d0d22; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ STRESS TESTER GODMODE")
st.caption("Every edge case. Every structure. Every distribution.")

# ─────────────────────────────────────────────
#  Mode Lists
# ─────────────────────────────────────────────
INT_MODES = [
    # ── General ──
    "random",
    "uniform random",
    "small values (near lo)",
    "large values (near hi)",
    "near lo+1",
    "near hi-1",
    "near lo and hi mixed",
    # ── Constant ──
    "all equal (random val)",
    "all lo",
    "all hi",
    "all zero",
    "all one",
    "all minus one",
    "all lo+1",
    "all hi-1",
    # ── Boundary scatter ──
    "boundary values only (lo/hi)",
    "boundary with one mid",
    "three-value boundary (lo, mid, hi)",
    # ── Sorted ──
    "sorted ascending",
    "sorted descending",
    "strictly increasing",
    "strictly decreasing",
    "almost sorted (few swaps)",
    "almost sorted descending",
    "rotated sorted",
    "double rotated sorted",
    "k-sorted (each elem ≤k away from sorted pos)",
    "sorted then reversed second half",
    # ── Patterns ──
    "alternating lo hi",
    "alternating hi lo",
    "alternating +1 -1",
    "alternating min max random",
    "saw wave",
    "triangle wave",
    "step function",
    "random walk",
    "random walk biased up",
    "random walk biased down",
    "random walk with resets",
    "sinusoidal-like",
    # ── Special values ──
    "powers of 2",
    "powers of 2 minus 1",
    "powers of 2 plus 1",
    "multiples of k",
    "divisors spread",
    "prime-like (odd)",
    "fibonacci-like",
    "arithmetic sequence",
    "geometric sequence",
    "squares (i*i)",
    "triangular numbers",
    "cubes (i*i*i)",
    "factorials clamped",
    # ── Duplicates ──
    "duplicates heavy (2 vals)",
    "duplicates heavy (3 vals)",
    "few distinct values",
    "one dominant value",
    "exactly one duplicate pair",
    "all distinct",
    "k distinct values uniform",
    # ── Spikes ──
    "single spike max",
    "single spike min",
    "single spike mid",
    "two spikes",
    "spikes at both ends",
    "spike at index 0",
    "spike at last index",
    "random spikes scattered",
    "valley at index 0",
    "valley at last index",
    # ── Shape ──
    "palindrome",
    "peak in middle",
    "valley in middle",
    "W shape",
    "M shape",
    "staircase up",
    "staircase down",
    "interleaved small large",
    "interleaved large small",
    "two sorted halves (unsorted overall)",
    "prefix max array",
    "suffix min array",
    "prefix min array",
    "suffix max array",
    # ── Negatives (only auto-picked when lo<0) ──
    "random with negatives",
    "all negative",
    "mixed sign",
    "abs values then negated",
    "sign alternating",
    # ── Overflow bait ──
    "near INT_MAX",
    "near LLONG_MAX",
    "near INT_MIN",
    "near LLONG_MIN",
    "near INT_MAX and INT_MIN mixed",
    "near LLONG_MAX and LLONG_MIN mixed",
    # ── Permutation ──
    "permutation of 1..n",
    "identity permutation",
    "reverse permutation",
    "almost identity (few swaps)",
    "cycle permutation",
    "random derangement",
    # ── Binary / bit ──
    "binary (0/1)",
    "binary heavy zeros",
    "binary heavy ones",
    "popcount spread",
    "alternating bits",
    "all bits set values",
    # ── Misc ──
    "zero heavy",
    "one heavy",
    "two values alternating random",
    "random then sorted tail",
    "sorted then random tail",
    "exactly one inversion",
    "max prefix sums",
    "non-decreasing with plateaus",
    "non-increasing with plateaus",
    "sqrt-like values",
    "log-like values",
    "random with forced lo",
    "random with forced hi",
    "random with forced lo and hi",
    "increasing then decreasing",
    "decreasing then increasing",
]

NEGATIVE_ONLY_MODES = {
    "random with negatives", "all negative", "mixed sign", "sign alternating",
    "abs values then negated", "near INT_MIN", "near LLONG_MIN",
    "all minus one", "near INT_MIN and INT_MAX mixed",
    "near LLONG_MAX and LLONG_MIN mixed",
}

STRING_MODES = [
    "random",
    # ── Charset ──
    "random lowercase",
    "random uppercase",
    "random mixed case",
    "random alphanumeric",
    "random digits only",
    "random printable",
    "random whitespace-free printable",
    # ── Single char ──
    "all 'a'",
    "all same char (random)",
    "all 'z'",
    # ── Binary-like ──
    "binary string (ab)",
    "binary string (01)",
    "binary heavy zeros",
    "binary heavy ones",
    # ── Patterns ──
    "alternating ab",
    "alternating aabb",
    "alternating abab",
    "periodic short",
    "periodic medium",
    "periodic long",
    "run-length encoded feel",
    # ── Palindromes ──
    "palindrome",
    "almost palindrome (1 flip)",
    "almost palindrome (2 flips)",
    "palindrome with center spike",
    "palindrome all same char",
    # ── Sorted ──
    "sorted asc (chars)",
    "sorted desc (chars)",
    "almost sorted chars",
    "rotated sorted string",
    # ── Repeats ──
    "prefix repeat",
    "suffix repeat",
    "single char repeated with spike",
    "two chars, one spike",
    "period-2 with one break",
    # ── Special content ──
    "random DNA (ACGT)",
    "random RNA (ACGU)",
    "random hex lowercase",
    "random hex uppercase",
    "random base64 chars",
    "only vowels",
    "no vowels / only consonants",
    # ── Bracket/structure ──
    "parentheses random",
    "balanced parentheses",
    "brackets mixed (()[]{} random)",
    "balanced brackets",
    "nested brackets deep",
    "unbalanced extra open",
    "unbalanced extra close",
    # ── Case patterns ──
    "camelCase-like",
    "snake_case-like",
    "random punctuation",
    "random with spaces",
    "increasing chars (a to z wrap)",
    "decreasing chars (z to a wrap)",
    # ── Edge & tricky ──
    "all distinct chars (if short enough)",
    "max distinct chars",
    "single char then all different",
    "two halves different chars",
    "border string (prefix = suffix)",
    "no repeated adjacent chars",
    "all repeated adjacent pairs",
    # ── Edge lengths ──
    "length 1",
    "empty string",
]

TREE_MODES = [
    "random",
    "bamboo (path)",
    "star",
    "caterpillar",
    "double star",
    "perfect binary tree",
    "complete binary tree",
    "random binary tree",
    "balanced k-ary tree",
    "maximum depth (bamboo)",
    "minimum depth (star)",
    "heavy path",
    "random high depth",
    "random low depth",
    "broom (chain + star end)",
    "spider (multi legs from root)",
    "two chains joined at root",
    "three chains joined at root",
    "chain with random subtrees",
    "zigzag path",
    "random with one heavy node",
    "Prufer random",
    "almost bamboo (few branches)",
    "almost star (few chains)",
    "single node (n=1)",
    "two nodes (n=2)",
    "three nodes (n=3)",
    "right-skewed binary",
    "left-skewed binary",
    "complete ternary tree",
    "centipede (chain of chains)",
    "forest-like (star of stars)",
]

GRAPH_MODES = [
    "random",
    "random sparse",
    "random medium density",
    "random dense",
    "complete graph",
    "tree (connected acyclic)",
    "connected random",
    "disconnected (2 components)",
    "disconnected (many components)",
    "single isolated node + rest connected",
    "path graph",
    "cycle graph",
    "wheel graph",
    "grid graph",
    "ladder graph",
    "petersen-like",
    "tournament (directed complete)",
    "bipartite random",
    "bipartite complete",
    "bipartite unbalanced",
    "DAG random",
    "DAG layered",
    "DAG single source",
    "DAG single sink",
    "sparse with one hub",
    "multiple hubs",
    "single node",
    "two nodes",
    "empty (no edges)",
    "self loops only",
    "multi edges only",
    "graph with bridge",
    "graph with articulation point",
    "source-sink layered",
    "clique + path tail",
    "two cliques connected by bridge",
    "random planar-like",
    "star of cliques",
]

# ─────────────────────────────────────────────
#  Utilities
# ─────────────────────────────────────────────
def C(x, lo, hi):
    """Clamp x into [lo, hi]."""
    return max(lo, min(hi, x))

def num_input(label, key, default=10, min_val=0):
    return int(st.number_input(label, min_value=min_val, value=default, key=key))

def rand_prime_like(lo, hi):
    for _ in range(200):
        n = random.randint(lo, hi) | 1
        if n > 1 and n % 3 != 0:
            return n
    return C(3, lo, hi)

def make_balanced_parens(length):
    n = length // 2
    if n == 0:
        return ""
    s, open_count, close_needed = [], 0, 0
    for i in range(2 * n):
        can_open = open_count < n
        can_close = close_needed > 0
        if can_open and can_close:
            if random.random() < 0.5:
                s.append('('); open_count += 1; close_needed += 1
            else:
                s.append(')'); close_needed -= 1
        elif can_open:
            s.append('('); open_count += 1; close_needed += 1
        else:
            s.append(')'); close_needed -= 1
    return ''.join(s)

def make_balanced_brackets(length):
    pairs = ['()', '[]', '{}']
    n = length // 2
    if n == 0:
        return ""
    stack, s = [], []
    for i in range(n):
        if not stack or (random.random() < 0.5 and len(stack) < n - i):
            p = random.choice(pairs); s.append(p[0]); stack.append(p[1])
        else:
            s.append(stack.pop())
    while stack:
        s.append(stack.pop())
    return ''.join(s)

def rand_multiple_of_k(lo, hi, k):
    lo_mult = math.ceil(lo / k)
    hi_mult = math.floor(hi / k)
    if lo_mult > hi_mult:
        return C(0, lo, hi) if lo <= 0 <= hi else lo
    return random.randint(lo_mult, hi_mult) * k

def _safe_divisors(n, lo, hi, max_iters=100_000):
    divs = []
    limit = min(int(n**0.5) + 1, max_iters)
    for i in range(1, limit):
        if n % i == 0:
            if lo <= i <= hi:
                divs.append(i)
            other = n // i
            if other != i and lo <= other <= hi:
                divs.append(other)
    return divs

# ─────────────────────────────────────────────
#  Integer Array Generator
# ─────────────────────────────────────────────
def generate_int_array(size, lo, hi, mode):
    if size == 0:
        return []
    if lo > hi:
        lo, hi = hi, lo
    Cl = lambda x: C(x, lo, hi)
    mid = lo + (hi - lo) // 2

    if mode == "random":
        pool = [m for m in INT_MODES[1:] if lo < 0 or m not in NEGATIVE_ONLY_MODES]
        mode = random.choice(pool)

    if mode == "uniform random":
        return [random.randint(lo, hi) for _ in range(size)]
    elif mode == "small values (near lo)":
        top = Cl(lo + max(1, (hi - lo) // 10))
        return [random.randint(lo, top) for _ in range(size)]
    elif mode == "large values (near hi)":
        bot = Cl(hi - max(1, (hi - lo) // 10))
        return [random.randint(bot, hi) for _ in range(size)]
    elif mode == "near lo+1":
        return [Cl(lo + random.randint(0, 2)) for _ in range(size)]
    elif mode == "near hi-1":
        return [Cl(hi - random.randint(0, 2)) for _ in range(size)]
    elif mode == "near lo and hi mixed":
        delta = max(1, (hi - lo) // 20)
        lo_pool = list(range(lo, Cl(lo + delta) + 1))
        hi_pool = list(range(Cl(hi - delta), hi + 1))
        pool = lo_pool + hi_pool
        return [random.choice(pool) for _ in range(size)]
    elif mode == "all equal (random val)":
        return [random.randint(lo, hi)] * size
    elif mode == "all lo":
        return [lo] * size
    elif mode == "all hi":
        return [hi] * size
    elif mode == "all zero":
        z = 0 if lo <= 0 <= hi else lo
        return [z] * size
    elif mode == "all one":
        v = 1 if lo <= 1 <= hi else lo
        return [v] * size
    elif mode == "all minus one":
        v = -1 if lo <= -1 <= hi else lo
        return [v] * size
    elif mode == "all lo+1":
        return [Cl(lo + 1)] * size
    elif mode == "all hi-1":
        return [Cl(hi - 1)] * size
    elif mode == "boundary values only (lo/hi)":
        return [random.choice([lo, hi]) for _ in range(size)]
    elif mode == "boundary with one mid":
        return [random.choice([lo, mid, hi]) for _ in range(size)]
    elif mode == "three-value boundary (lo, mid, hi)":
        arr = [lo] * (size // 3) + [mid] * (size // 3) + [hi] * (size - 2 * (size // 3))
        random.shuffle(arr)
        return arr
    elif mode == "sorted ascending":
        return sorted(random.randint(lo, hi) for _ in range(size))
    elif mode == "sorted descending":
        return sorted((random.randint(lo, hi) for _ in range(size)), reverse=True)
    elif mode == "strictly increasing":
        span = hi - lo + 1
        if span >= size:
            return sorted(random.sample(range(lo, hi + 1), size))
        return list(range(lo, lo + size))
    elif mode == "strictly decreasing":
        span = hi - lo + 1
        if span >= size:
            return sorted(random.sample(range(lo, hi + 1), size), reverse=True)
        return list(range(lo + size - 1, lo - 1, -1))
    elif mode == "almost sorted (few swaps)":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        for _ in range(max(1, size // 20)):
            i, j = random.randint(0, size - 1), random.randint(0, size - 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif mode == "almost sorted descending":
        arr = sorted((random.randint(lo, hi) for _ in range(size)), reverse=True)
        for _ in range(max(1, size // 20)):
            i, j = random.randint(0, size - 1), random.randint(0, size - 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif mode == "rotated sorted":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        k = random.randint(1, max(1, size - 1))
        return arr[k:] + arr[:k]
    elif mode == "double rotated sorted":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        k1 = random.randint(1, max(1, size // 2))
        k2 = random.randint(k1, max(k1, size - 1))
        return arr[k1:k2] + arr[:k1] + arr[k2:]
    elif mode == "k-sorted (each elem ≤k away from sorted pos)":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        k = max(1, size // 10)
        for i in range(size):
            j = C(i + random.randint(-k, k), 0, size - 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif mode == "sorted then reversed second half":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        half = size // 2
        arr[half:] = arr[half:][::-1]
        return arr
    elif mode == "alternating lo hi":
        return [hi if i % 2 == 0 else lo for i in range(size)]
    elif mode == "alternating hi lo":
        return [lo if i % 2 == 0 else hi for i in range(size)]
    elif mode == "alternating +1 -1":
        a = Cl(1); b = Cl(-1) if lo < 0 else lo
        return [a if i % 2 == 0 else b for i in range(size)]
    elif mode == "alternating min max random":
        vals = [random.randint(lo, hi) for _ in range(size)]
        for i in range(0, size, 4): vals[i] = lo
        for i in range(2, size, 4): vals[i] = hi
        return vals
    elif mode == "saw wave":
        period = max(2, random.randint(2, max(2, size // 3)))
        rng = hi - lo
        return [Cl(lo + int(rng * ((i % period) / period))) for i in range(size)]
    elif mode == "triangle wave":
        period = max(2, random.randint(2, max(2, size // 3)))
        rng = hi - lo
        def tri(i):
            t = i % period; half = period // 2
            return Cl(lo + int(rng * (t / half if t <= half else (period - t) / half)))
        return [tri(i) for i in range(size)]
    elif mode == "step function":
        steps = random.randint(2, max(2, min(10, size)))
        step_h = (hi - lo) // steps
        arr = []
        for s in range(steps):
            count = size // steps + (1 if s < size % steps else 0)
            arr.extend([Cl(lo + s * step_h)] * count)
        return arr[:size]
    elif mode == "random walk":
        step_max = max(1, (hi - lo) // 20)
        arr = [random.randint(lo, hi)]
        for _ in range(size - 1):
            arr.append(Cl(arr[-1] + random.randint(-step_max, step_max)))
        return arr
    elif mode == "random walk biased up":
        step_max = max(1, (hi - lo) // 20)
        arr = [Cl(lo + (hi - lo) // 4)]
        for _ in range(size - 1):
            arr.append(Cl(arr[-1] + random.randint(-step_max // 2, step_max)))
        return arr
    elif mode == "random walk biased down":
        step_max = max(1, (hi - lo) // 20)
        arr = [Cl(hi - (hi - lo) // 4)]
        for _ in range(size - 1):
            arr.append(Cl(arr[-1] + random.randint(-step_max, step_max // 2)))
        return arr
    elif mode == "random walk with resets":
        step_max = max(1, (hi - lo) // 20)
        reset_val = random.randint(lo, hi)
        arr = [reset_val]
        for _ in range(size - 1):
            if random.random() < 0.05:
                arr.append(Cl(random.randint(lo, hi)))
            else:
                arr.append(Cl(arr[-1] + random.randint(-step_max, step_max)))
        return arr
    elif mode == "sinusoidal-like":
        rng = (hi - lo) / 2
        center = lo + rng
        freq = random.uniform(0.5, 3.0) * math.pi / max(size, 1)
        return [Cl(int(center + rng * math.sin(freq * i))) for i in range(size)]
    elif mode == "powers of 2":
        pows = [1 << k for k in range(63) if lo <= (1 << k) <= hi]
        if not pows: pows = [Cl(1)]
        return [random.choice(pows) for _ in range(size)]
    elif mode == "powers of 2 minus 1":
        pows = [(1 << k) - 1 for k in range(1, 64) if lo <= (1 << k) - 1 <= hi]
        if not pows: pows = [Cl(1)]
        return [random.choice(pows) for _ in range(size)]
    elif mode == "powers of 2 plus 1":
        pows = [(1 << k) + 1 for k in range(63) if lo <= (1 << k) + 1 <= hi]
        if not pows: pows = [Cl(2)]
        return [random.choice(pows) for _ in range(size)]
    elif mode == "multiples of k":
        k = random.randint(2, max(2, min(1000, max(1, (hi - lo) // max(size, 1)))))
        lo_m = math.ceil(lo / k)
        hi_m = math.floor(hi / k)
        if lo_m > hi_m:
            return [lo] * size
        return [random.randint(lo_m, hi_m) * k for _ in range(size)]
    elif mode == "divisors spread":
        base_lo = max(1, lo)
        base_hi = min(hi, 10**12)
        if base_lo > base_hi:
            return [lo] * size
        base = random.randint(base_lo, min(base_hi, base_lo + 10**6))
        divs = _safe_divisors(base, lo, hi)
        if not divs:
            divs = [Cl(base)]
        return [random.choice(divs) for _ in range(size)]
    elif mode == "prime-like (odd)":
        return [rand_prime_like(lo, hi) for _ in range(size)]
    elif mode == "fibonacci-like":
        cap = Cl(lo + max(1, (hi - lo) // 4))
        a, b = Cl(random.randint(lo, cap)), Cl(random.randint(lo, cap))
        arr = [a, b]
        while len(arr) < size:
            nxt = Cl(arr[-1] + arr[-2])
            arr.append(nxt)
        return arr[:size]
    elif mode == "arithmetic sequence":
        if hi == lo:
            return [lo] * size
        d = random.randint(0, max(0, (hi - lo) // max(size - 1, 1)))
        max_start = hi - d * max(size - 1, 0)
        start = random.randint(lo, max(lo, Cl(max_start)))
        return [Cl(start + d * i) for i in range(size)]
    elif mode == "geometric sequence":
        if lo <= 0 and hi >= 0:
            start = random.randint(max(lo, 1), max(1, hi // 4 if hi > 0 else 1))
        else:
            start = Cl(max(1, lo))
        r_num = random.randint(2, 3)
        arr = [start]
        for _ in range(size - 1):
            nxt = Cl(arr[-1] * r_num)
            arr.append(nxt)
            if nxt == hi:
                arr.extend([hi] * (size - len(arr)))
                break
        return arr[:size]
    elif mode == "squares (i*i)":
        base = max(0, int(math.isqrt(max(0, lo))))
        arr = []
        for i in range(base, base + size * 2):
            v = i * i
            if lo <= v <= hi:
                arr.append(v)
            if len(arr) >= size:
                break
        while len(arr) < size:
            arr.append(random.randint(lo, hi))
        random.shuffle(arr)
        return arr[:size]
    elif mode == "triangular numbers":
        start_n = 0
        while start_n * (start_n + 1) // 2 < lo:
            start_n += 1
        tris = []
        n = start_n
        while len(tris) < size * 2 and n * (n + 1) // 2 <= hi:
            tris.append(n * (n + 1) // 2)
            n += 1
        if not tris:
            tris = [lo]
        return [random.choice(tris) for _ in range(size)]
    elif mode == "cubes (i*i*i)":
        base = max(0, int(round(max(0, lo) ** (1/3))))
        arr = []
        for i in range(max(0, base - 1), base + size * 2):
            v = i * i * i
            cv = Cl(v)
            arr.append(cv)
            if len(arr) >= size:
                break
        while len(arr) < size:
            arr.append(random.randint(lo, hi))
        random.shuffle(arr)
        return arr[:size]
    elif mode == "factorials clamped":
        facts = []
        f = 1
        for i in range(1, 21):
            f *= i
            v = Cl(f)
            facts.append(v)
            if v == hi:
                break
        facts = [v for v in facts if lo <= v <= hi] or [lo]
        return [random.choice(facts) for _ in range(size)]
    elif mode == "duplicates heavy (2 vals)":
        a, b = random.randint(lo, hi), random.randint(lo, hi)
        return [random.choice([a, b]) for _ in range(size)]
    elif mode == "duplicates heavy (3 vals)":
        vals = [random.randint(lo, hi) for _ in range(3)]
        return [random.choice(vals) for _ in range(size)]
    elif mode == "few distinct values":
        k = random.randint(2, max(2, min(10, hi - lo + 1)))
        vals = [random.randint(lo, hi) for _ in range(k)]
        return [random.choice(vals) for _ in range(size)]
    elif mode == "one dominant value":
        dom = random.randint(lo, hi)
        other = random.randint(lo, hi)
        return [dom if random.random() < 0.9 else other for _ in range(size)]
    elif mode == "exactly one duplicate pair":
        if size < 2:
            return [random.randint(lo, hi)]
        span = hi - lo + 1
        if span >= size:
            arr = sorted(random.sample(range(lo, hi + 1), size - 1))
            dup = random.choice(arr)
            arr.append(dup)
        else:
            arr = list(range(lo, lo + size - 1)) + [lo]
        random.shuffle(arr)
        return arr
    elif mode == "all distinct":
        span = hi - lo + 1
        if span >= size:
            return random.sample(range(lo, hi + 1), size)
        return [(lo + i) % (span if span > 0 else 1) + lo for i in range(size)]
    elif mode == "k distinct values uniform":
        k = random.randint(2, max(2, min(size, min(20, hi - lo + 1))))
        vals = random.sample(range(lo, hi + 1), k)
        arr = []
        for i in range(size):
            arr.append(vals[i % k])
        random.shuffle(arr)
        return arr
    elif mode == "single spike max":
        arr = [lo] * size; arr[random.randint(0, size - 1)] = hi; return arr
    elif mode == "single spike min":
        arr = [hi] * size; arr[random.randint(0, size - 1)] = lo; return arr
    elif mode == "single spike mid":
        arr = [random.randint(lo, Cl(mid - 1)) for _ in range(size)]
        arr[random.randint(0, size - 1)] = hi; return arr
    elif mode == "two spikes":
        arr = [random.randint(lo, hi) for _ in range(size)]
        arr[0] = hi; arr[-1] = lo; return arr
    elif mode == "spikes at both ends":
        arr = [random.randint(lo, hi) for _ in range(size)]
        arr[0] = hi; arr[-1] = hi; return arr
    elif mode == "spike at index 0":
        arr = [random.randint(lo, Cl(lo + (hi - lo) // 2)) for _ in range(size)]
        arr[0] = hi; return arr
    elif mode == "spike at last index":
        arr = [random.randint(lo, Cl(lo + (hi - lo) // 2)) for _ in range(size)]
        arr[-1] = hi; return arr
    elif mode == "random spikes scattered":
        arr = [lo] * size
        num_spikes = max(1, size // 10)
        for _ in range(num_spikes):
            arr[random.randint(0, size - 1)] = hi
        return arr
    elif mode == "valley at index 0":
        arr = [random.randint(Cl(mid), hi) for _ in range(size)]
        arr[0] = lo; return arr
    elif mode == "valley at last index":
        arr = [random.randint(Cl(mid), hi) for _ in range(size)]
        arr[-1] = lo; return arr
    elif mode == "palindrome":
        half = [random.randint(lo, hi) for _ in range(size // 2)]
        mid_v = [random.randint(lo, hi)] if size % 2 else []
        return half + mid_v + half[::-1]
    elif mode == "peak in middle":
        left = sorted(random.randint(lo, hi) for _ in range(size // 2 + 1))
        right = sorted((random.randint(lo, hi) for _ in range(size - size // 2 - 1)), reverse=True)
        return left + right
    elif mode == "valley in middle":
        left = sorted((random.randint(lo, hi) for _ in range(size // 2 + 1)), reverse=True)
        right = sorted(random.randint(lo, hi) for _ in range(size - size // 2 - 1))
        return left + right
    elif mode == "W shape":
        q = size // 4
        su = lambda n: sorted(random.randint(lo, hi) for _ in range(n))
        sd = lambda n: sorted((random.randint(lo, hi) for _ in range(n)), reverse=True)
        return sd(q) + su(q) + sd(q) + su(size - 3 * q)
    elif mode == "M shape":
        q = size // 4
        su = lambda n: sorted(random.randint(lo, hi) for _ in range(n))
        sd = lambda n: sorted((random.randint(lo, hi) for _ in range(n)), reverse=True)
        return su(q) + sd(q) + su(q) + sd(size - 3 * q)
    elif mode == "staircase up":
        steps = max(2, min(size, 10))
        step_h = (hi - lo) // steps
        arr = []
        for s in range(steps):
            count = size // steps + (1 if s < size % steps else 0)
            arr.extend([Cl(lo + s * step_h)] * count)
        return arr[:size]
    elif mode == "staircase down":
        steps = max(2, min(size, 10))
        step_h = (hi - lo) // steps
        arr = []
        for s in range(steps - 1, -1, -1):
            count = size // steps + (1 if s < size % steps else 0)
            arr.extend([Cl(lo + s * step_h)] * count)
        return arr[:size]
    elif mode == "interleaved small large":
        small_top = Cl(lo + (hi - lo) // 3)
        large_bot = Cl(hi - (hi - lo) // 3)
        return [random.randint(lo, small_top) if i % 2 == 0
                else random.randint(large_bot, hi) for i in range(size)]
    elif mode == "interleaved large small":
        small_top = Cl(lo + (hi - lo) // 3)
        large_bot = Cl(hi - (hi - lo) // 3)
        return [random.randint(large_bot, hi) if i % 2 == 0
                else random.randint(lo, small_top) for i in range(size)]
    elif mode == "two sorted halves (unsorted overall)":
        half = size // 2
        a = sorted(random.randint(lo, hi) for _ in range(half))
        b = sorted(random.randint(lo, hi) for _ in range(size - half))
        return b + a
    elif mode == "prefix max array":
        arr = [random.randint(lo, hi) for _ in range(size)]
        for i in range(1, size):
            arr[i] = max(arr[i], arr[i - 1])
        return arr
    elif mode == "suffix min array":
        arr = [random.randint(lo, hi) for _ in range(size)]
        for i in range(size - 2, -1, -1):
            arr[i] = min(arr[i], arr[i + 1])
        return arr
    elif mode == "prefix min array":
        arr = [random.randint(lo, hi) for _ in range(size)]
        for i in range(1, size):
            arr[i] = min(arr[i], arr[i - 1])
        return arr
    elif mode == "suffix max array":
        arr = [random.randint(lo, hi) for _ in range(size)]
        for i in range(size - 2, -1, -1):
            arr[i] = max(arr[i], arr[i + 1])
        return arr
    elif mode == "random with negatives":
        return [random.randint(lo, hi) for _ in range(size)]
    elif mode == "all negative":
        hi2 = min(-1, hi)
        if lo > hi2: return [lo] * size
        return [random.randint(lo, hi2) for _ in range(size)]
    elif mode == "mixed sign":
        return [Cl(-abs(v) if random.random() < 0.5 else abs(v))
                for v in (random.randint(lo, hi) for _ in range(size))]
    elif mode == "abs values then negated":
        return [Cl(-abs(random.randint(lo, hi))) for _ in range(size)]
    elif mode == "sign alternating":
        arr = sorted(abs(random.randint(lo, hi)) for _ in range(size))
        return [Cl(-v if i % 2 == 0 else v) for i, v in enumerate(arr)]
    elif mode == "near INT_MAX":
        base = min(hi, 2**31 - 1)
        return [Cl(base - random.randint(0, 5)) for _ in range(size)]
    elif mode == "near LLONG_MAX":
        base = min(hi, 2**63 - 1)
        return [Cl(base - random.randint(0, 5)) for _ in range(size)]
    elif mode == "near INT_MIN":
        base = max(lo, -(2**31))
        return [Cl(base + random.randint(0, 5)) for _ in range(size)]
    elif mode == "near LLONG_MIN":
        base = max(lo, -(2**63))
        return [Cl(base + random.randint(0, 5)) for _ in range(size)]
    elif mode == "near INT_MAX and INT_MIN mixed":
        vmax = min(hi, 2**31 - 1); vmin = max(lo, -(2**31))
        pool = [Cl(vmax - random.randint(0, 5)), Cl(vmin + random.randint(0, 5))]
        return [random.choice(pool) for _ in range(size)]
    elif mode == "near LLONG_MAX and LLONG_MIN mixed":
        vmax = min(hi, 2**63 - 1); vmin = max(lo, -(2**63))
        pool = [Cl(vmax - random.randint(0, 3)), Cl(vmin + random.randint(0, 3))]
        return [random.choice(pool) for _ in range(size)]
    elif mode == "permutation of 1..n":
        arr = list(range(1, size + 1)); random.shuffle(arr); return arr
    elif mode == "identity permutation":
        return list(range(1, size + 1))
    elif mode == "reverse permutation":
        return list(range(size, 0, -1))
    elif mode == "almost identity (few swaps)":
        arr = list(range(1, size + 1))
        for _ in range(max(1, size // 20)):
            i, j = random.randint(0, size - 1), random.randint(0, size - 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif mode == "cycle permutation":
        arr = list(range(1, size + 1))
        k = random.randint(1, max(1, size - 1))
        return arr[k:] + arr[:k]
    elif mode == "random derangement":
        arr = list(range(1, size + 1))
        for i in range(size - 1, 0, -1):
            j = random.randint(0, i - 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif mode == "binary (0/1)":
        a, b = Cl(0), Cl(1)
        return [random.randint(a, b) for _ in range(size)]
    elif mode == "binary heavy zeros":
        a, b = Cl(0), Cl(1)
        return [a if random.random() < 0.85 else b for _ in range(size)]
    elif mode == "binary heavy ones":
        a, b = Cl(0), Cl(1)
        return [b if random.random() < 0.85 else a for _ in range(size)]
    elif mode == "popcount spread":
        rng = hi - lo + 1
        return [lo + bin(random.randint(lo if lo >= 0 else 0, max(lo if lo >= 0 else 0, hi))).count('1') % rng
                for _ in range(size)]
    elif mode == "alternating bits":
        v1 = Cl(int("01" * 32, 2))
        v2 = Cl(int("10" * 32, 2))
        return [v1 if i % 2 == 0 else v2 for i in range(size)]
    elif mode == "all bits set values":
        vals = [(1 << k) - 1 for k in range(1, 64) if lo <= (1 << k) - 1 <= hi]
        if not vals:
            vals = [Cl(hi)]
        return [random.choice(vals) for _ in range(size)]
    elif mode == "zero heavy":
        z = 0 if lo <= 0 <= hi else lo
        return [z if random.random() < 0.8 else random.randint(lo, hi) for _ in range(size)]
    elif mode == "one heavy":
        v = 1 if lo <= 1 <= hi else lo
        return [v if random.random() < 0.8 else random.randint(lo, hi) for _ in range(size)]
    elif mode == "two values alternating random":
        a, b = random.randint(lo, hi), random.randint(lo, hi)
        return [a if i % 2 == 0 else b for i in range(size)]
    elif mode == "random then sorted tail":
        split = size // 2
        return [random.randint(lo, hi) for _ in range(split)] + \
               sorted(random.randint(lo, hi) for _ in range(size - split))
    elif mode == "sorted then random tail":
        split = size // 2
        return sorted(random.randint(lo, hi) for _ in range(split)) + \
               [random.randint(lo, hi) for _ in range(size - split)]
    elif mode == "exactly one inversion":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        if size >= 2:
            i = random.randint(0, size - 2)
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
        return arr
    elif mode == "max prefix sums":
        arr = [random.randint(lo, hi)]
        for _ in range(size - 1):
            arr.append(random.randint(max(lo, 0 if lo <= 0 else lo), hi))
        return arr
    elif mode == "non-decreasing with plateaus":
        arr = sorted(random.randint(lo, hi) for _ in range(size))
        for i in range(0, size - 1, 3):
            arr[i + 1] = arr[i] if i + 1 < size else arr[i]
        return arr
    elif mode == "non-increasing with plateaus":
        arr = sorted((random.randint(lo, hi) for _ in range(size)), reverse=True)
        for i in range(0, size - 1, 3):
            arr[i + 1] = arr[i] if i + 1 < size else arr[i]
        return arr
    elif mode == "sqrt-like values":
        scale = (hi - lo) / max(1, math.sqrt(size))
        return [Cl(lo + int(math.sqrt(i + 1) * scale)) for i in range(size)]
    elif mode == "log-like values":
        scale = (hi - lo) / max(1, math.log(size + 1))
        return [Cl(lo + int(math.log(i + 1) * scale)) for i in range(size)]
    elif mode == "random with forced lo":
        arr = [random.randint(lo, hi) for _ in range(size)]
        arr[random.randint(0, size - 1)] = lo
        return arr
    elif mode == "random with forced hi":
        arr = [random.randint(lo, hi) for _ in range(size)]
        arr[random.randint(0, size - 1)] = hi
        return arr
    elif mode == "random with forced lo and hi":
        arr = [random.randint(lo, hi) for _ in range(size)]
        arr[0] = lo
        arr[-1] = hi
        return arr
    elif mode == "increasing then decreasing":
        half = size // 2
        left = sorted(random.randint(lo, hi) for _ in range(half))
        right = sorted((random.randint(lo, hi) for _ in range(size - half)), reverse=True)
        return left + right
    elif mode == "decreasing then increasing":
        half = size // 2
        left = sorted((random.randint(lo, hi) for _ in range(half)), reverse=True)
        right = sorted(random.randint(lo, hi) for _ in range(size - half))
        return left + right

    return [random.randint(lo, hi) for _ in range(size)]


# ─────────────────────────────────────────────
#  String Generator
# ─────────────────────────────────────────────
def generate_string(length, mode):
    if length == 0 or mode == "empty string":
        return ""
    if mode == "length 1":
        return random.choice(string.ascii_lowercase)
    lc = string.ascii_lowercase

    if mode == "random":
        mode = random.choice(STRING_MODES[1:])

    if mode == "random lowercase":
        return ''.join(random.choices(lc, k=length))
    elif mode == "random uppercase":
        return ''.join(random.choices(string.ascii_uppercase, k=length))
    elif mode == "random mixed case":
        return ''.join(random.choices(string.ascii_letters, k=length))
    elif mode == "random alphanumeric":
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    elif mode == "random digits only":
        return ''.join(random.choices(string.digits, k=length))
    elif mode == "random printable":
        return ''.join(random.choices(string.printable.strip(), k=length))
    elif mode == "random whitespace-free printable":
        chars = [c for c in string.printable if not c.isspace()]
        return ''.join(random.choices(chars, k=length))
    elif mode == "all 'a'":
        return 'a' * length
    elif mode == "all same char (random)":
        return random.choice(lc) * length
    elif mode == "all 'z'":
        return 'z' * length
    elif mode == "binary string (ab)":
        return ''.join(random.choices("ab", k=length))
    elif mode == "binary string (01)":
        return ''.join(random.choices("01", k=length))
    elif mode == "binary heavy zeros":
        return ''.join('0' if random.random() < 0.85 else '1' for _ in range(length))
    elif mode == "binary heavy ones":
        return ''.join('1' if random.random() < 0.85 else '0' for _ in range(length))
    elif mode == "alternating ab":
        return ''.join('a' if i % 2 == 0 else 'b' for i in range(length))
    elif mode == "alternating aabb":
        return ''.join("aabb"[i % 4] for i in range(length))
    elif mode == "alternating abab":
        return ''.join("abab"[i % 4] for i in range(length))
    elif mode == "periodic short":
        period = random.randint(1, 3)
        base = ''.join(random.choices(lc, k=period))
        return (base * (length // period + 1))[:length]
    elif mode == "periodic medium":
        period = random.randint(4, max(4, length // 4))
        base = ''.join(random.choices(lc, k=period))
        return (base * (length // period + 1))[:length]
    elif mode == "periodic long":
        period = max(1, length // 2)
        base = ''.join(random.choices(lc, k=period))
        return (base * 2)[:length]
    elif mode == "run-length encoded feel":
        s = []
        while len(s) < length:
            c = random.choice(lc)
            run = random.randint(1, max(1, (length - len(s)) // 3 + 1))
            s.extend([c] * run)
        return ''.join(s[:length])
    elif mode == "palindrome":
        half = ''.join(random.choices(lc, k=length // 2))
        mid = random.choice(lc) if length % 2 else ""
        return half + mid + half[::-1]
    elif mode == "almost palindrome (1 flip)":
        half = ''.join(random.choices(lc, k=length // 2))
        mid = random.choice(lc) if length % 2 else ""
        s = list(half + mid + half[::-1])
        s[random.randint(0, len(s) - 1)] = random.choice(lc)
        return ''.join(s)
    elif mode == "almost palindrome (2 flips)":
        half = ''.join(random.choices(lc, k=length // 2))
        mid = random.choice(lc) if length % 2 else ""
        s = list(half + mid + half[::-1])
        for _ in range(2):
            s[random.randint(0, len(s) - 1)] = random.choice(lc)
        return ''.join(s)
    elif mode == "palindrome with center spike":
        half = ''.join(random.choices(lc[:5], k=length // 2))
        mid = 'z' if length % 2 else ""
        return half + mid + half[::-1]
    elif mode == "palindrome all same char":
        c = random.choice(lc)
        return c * length
    elif mode == "sorted asc (chars)":
        return ''.join(sorted(random.choices(lc, k=length)))
    elif mode == "sorted desc (chars)":
        return ''.join(sorted(random.choices(lc, k=length), reverse=True))
    elif mode == "almost sorted chars":
        s = list(sorted(random.choices(lc, k=length)))
        for _ in range(max(1, length // 20)):
            i, j = random.randint(0, length - 1), random.randint(0, length - 1)
            s[i], s[j] = s[j], s[i]
        return ''.join(s)
    elif mode == "rotated sorted string":
        s = sorted(random.choices(lc, k=length))
        k = random.randint(1, max(1, length - 1))
        return ''.join(s[k:] + s[:k])
    elif mode == "prefix repeat":
        plen = max(1, length // 4)
        base = ''.join(random.choices(lc, k=plen))
        return (base * (length // plen + 1))[:length]
    elif mode == "suffix repeat":
        slen = max(1, length // 4)
        suffix = ''.join(random.choices(lc, k=slen))
        rest_len = length - slen
        rest = ''.join(random.choices(lc, k=rest_len))
        return rest + suffix
    elif mode == "single char repeated with spike":
        c = random.choice(lc)
        spike = random.choice([ch for ch in lc if ch != c])
        s = [c] * length
        s[random.randint(0, length - 1)] = spike
        return ''.join(s)
    elif mode == "two chars, one spike":
        a, b = random.sample(lc, 2)
        s = [random.choice([a, b]) for _ in range(length)]
        s[random.randint(0, length - 1)] = 'z'
        return ''.join(s)
    elif mode == "period-2 with one break":
        a, b = random.sample(lc, 2)
        s = [a if i % 2 == 0 else b for i in range(length)]
        if length > 2:
            pos = random.randint(1, length - 2)
            s[pos] = random.choice([c for c in lc if c not in (a, b)])
        return ''.join(s)
    elif mode == "random DNA (ACGT)":
        return ''.join(random.choices("ACGT", k=length))
    elif mode == "random RNA (ACGU)":
        return ''.join(random.choices("ACGU", k=length))
    elif mode == "random hex lowercase":
        return ''.join(random.choices("0123456789abcdef", k=length))
    elif mode == "random hex uppercase":
        return ''.join(random.choices("0123456789ABCDEF", k=length))
    elif mode == "random base64 chars":
        return ''.join(random.choices(string.ascii_letters + string.digits + "+/", k=length))
    elif mode == "only vowels":
        return ''.join(random.choices("aeiou", k=length))
    elif mode == "no vowels / only consonants":
        cons = [c for c in lc if c not in "aeiou"]
        return ''.join(random.choices(cons, k=length))
    elif mode == "parentheses random":
        return ''.join(random.choices("()", k=length))
    elif mode == "balanced parentheses":
        return make_balanced_parens(length)
    elif mode == "brackets mixed (()[]{} random)":
        return ''.join(random.choices("()[]{}", k=length))
    elif mode == "balanced brackets":
        return make_balanced_brackets(length)
    elif mode == "nested brackets deep":
        depth = length // 2
        return '(' * depth + ')' * depth
    elif mode == "unbalanced extra open":
        s = list(make_balanced_parens(max(2, length - 2)))
        s += ['('] * (length - len(s))
        return ''.join(s[:length])
    elif mode == "unbalanced extra close":
        s = list(make_balanced_parens(max(2, length - 2)))
        s += [')'] * (length - len(s))
        return ''.join(s[:length])
    elif mode == "camelCase-like":
        s = []
        while len(s) < length:
            word = ''.join(random.choices(lc, k=random.randint(1, 6)))
            if s: word = word[0].upper() + word[1:]
            s.extend(list(word))
        return ''.join(s[:length])
    elif mode == "snake_case-like":
        s = []
        while len(s) < length:
            if s: s.append('_')
            s.extend(list(''.join(random.choices(lc, k=random.randint(1, 6)))))
        return ''.join(s[:length])
    elif mode == "random punctuation":
        return ''.join(random.choices(string.punctuation, k=length))
    elif mode == "random with spaces":
        return (''.join(random.choices(lc + " ", k=length)).strip() or 'a')
    elif mode == "increasing chars (a to z wrap)":
        return ''.join(chr(ord('a') + i % 26) for i in range(length))
    elif mode == "decreasing chars (z to a wrap)":
        return ''.join(chr(ord('z') - i % 26) for i in range(length))
    elif mode == "all distinct chars (if short enough)":
        if length <= 26:
            return ''.join(random.sample(lc, length))
        base = list(lc); random.shuffle(base)
        return ''.join((base * (length // 26 + 1))[:length])
    elif mode == "max distinct chars":
        base = list(lc); random.shuffle(base)
        extra = random.choices(lc, k=max(0, length - 26))
        full = base[:min(26, length)] + extra
        random.shuffle(full)
        return ''.join(full[:length])
    elif mode == "single char then all different":
        if length <= 1:
            return random.choice(lc)
        first = random.choice(lc)
        rest = random.sample([c for c in lc if c != first], min(25, length - 1))
        rest += random.choices(lc, k=max(0, length - 1 - len(rest)))
        return first + ''.join(rest[:length - 1])
    elif mode == "two halves different chars":
        h1 = length // 2; h2 = length - h1
        chars1 = random.choices(lc[:13], k=h1)
        chars2 = random.choices(lc[13:], k=h2)
        return ''.join(chars1) + ''.join(chars2)
    elif mode == "border string (prefix = suffix)":
        if length < 2:
            return random.choice(lc) * length
        blen = random.randint(1, max(1, length // 3))
        border = ''.join(random.choices(lc, k=blen))
        middle = ''.join(random.choices(lc, k=max(0, length - 2 * blen)))
        return (border + middle + border)[:length]
    elif mode == "no repeated adjacent chars":
        if length == 0: return ""
        s = [random.choice(lc)]
        for _ in range(length - 1):
            choices = [c for c in lc if c != s[-1]]
            s.append(random.choice(choices))
        return ''.join(s)
    elif mode == "all repeated adjacent pairs":
        s = []
        while len(s) < length:
            c = random.choice(lc)
            s.extend([c, c])
        return ''.join(s[:length])

    return ''.join(random.choices(lc, k=length))


# ─────────────────────────────────────────────
#  Tree Generator
# ─────────────────────────────────────────────
def generate_tree(n, mode, weighted=False, w_lo=1, w_hi=100, directed=False):
    if mode == "single node (n=1)": n = 1
    elif mode == "two nodes (n=2)": n = max(n, 2)
    elif mode == "three nodes (n=3)": n = max(n, 3)

    if n <= 1:
        return [], n

    edges = []

    def add(u, v):
        w = f" {random.randint(w_lo, w_hi)}" if weighted else ""
        edges.append(f"{u} {v}{w}")

    if mode == "random":
        mode = random.choice(TREE_MODES[1:])

    if mode in ("bamboo (path)", "maximum depth (bamboo)", "zigzag path"):
        for i in range(1, n): add(i, i + 1)
    elif mode in ("star", "minimum depth (star)"):
        for i in range(2, n + 1): add(1, i)
    elif mode == "caterpillar":
        spine = max(2, n // 2)
        for i in range(1, spine): add(i, i + 1)
        idx = spine + 1
        for i in range(1, spine + 1):
            if idx > n: break
            add(i, idx); idx += 1
    elif mode == "double star":
        half = max(2, n // 2)
        add(1, 2)
        for i in range(3, half + 1): add(1, i)
        for i in range(half + 1, n + 1): add(2, i)
    elif mode in ("perfect binary tree", "complete binary tree"):
        for i in range(2, n + 1): add(i // 2, i)
    elif mode == "random binary tree":
        for i in range(2, n + 1):
            add(random.randint(max(1, i // 2 - 1), i - 1), i)
    elif mode == "balanced k-ary tree":
        k = random.randint(2, 4)
        for i in range(2, n + 1): add((i - 2) // k + 1, i)
    elif mode == "heavy path":
        heavy = max(1, int(n * 0.7))
        for i in range(1, heavy): add(i, i + 1)
        for i in range(heavy + 1, n + 1): add(random.randint(1, heavy), i)
    elif mode == "random high depth":
        for i in range(2, n + 1): add(random.randint(max(1, i - 3), i - 1), i)
    elif mode == "random low depth":
        for i in range(2, n + 1): add(random.randint(1, max(1, i // 3 + 1)), i)
    elif mode == "broom (chain + star end)":
        handle = max(1, n // 2)
        for i in range(1, handle): add(i, i + 1)
        for i in range(handle + 1, n + 1): add(handle, i)
    elif mode == "spider (multi legs from root)":
        legs = random.randint(2, max(2, min(6, n - 1)))
        idx = 2
        for _ in range(legs):
            prev = 1
            while idx <= n:
                add(prev, idx); prev = idx; idx += 1
                if random.random() < 0.4: break
        while idx <= n: add(random.randint(1, idx - 1), idx); idx += 1
    elif mode == "two chains joined at root":
        half = n // 2
        for i in range(2, half + 1): add(i - 1, i)
        add(1, half + 1)
        for i in range(half + 2, n + 1): add(i - 1, i)
    elif mode == "three chains joined at root":
        t = n // 3
        for i in range(2, t + 1): add(i - 1, i)
        add(1, t + 1)
        for i in range(t + 2, 2*t + 1): add(i - 1, i)
        add(1, 2*t + 1)
        for i in range(2*t + 2, n + 1): add(i - 1, i)
    elif mode == "chain with random subtrees":
        spine = max(2, n // 2)
        for i in range(1, spine): add(i, i + 1)
        for i in range(spine + 1, n + 1): add(random.randint(1, spine), i)
    elif mode == "random with one heavy node":
        heavy = random.randint(1, n)
        for i in range(2, n + 1):
            if i != heavy and random.random() < 0.4: add(heavy, i)
            else: add(random.randint(1, i - 1), i)
    elif mode == "Prufer random":
        if n == 2:
            add(1, 2)
        else:
            prufer = [random.randint(1, n) for _ in range(n - 2)]
            degree = [1] * (n + 1)
            for x in prufer: degree[x] += 1
            for x in prufer:
                for leaf in range(1, n + 1):
                    if degree[leaf] == 1:
                        add(leaf, x); degree[leaf] -= 1; degree[x] -= 1; break
            last = [i for i in range(1, n + 1) if degree[i] == 1]
            if len(last) >= 2: add(last[0], last[1])
    elif mode == "almost bamboo (few branches)":
        for i in range(1, n - 1): add(i, i + 1)
        if n > 2: add(random.randint(1, n - 1), n)
    elif mode == "almost star (few chains)":
        half = max(3, n // 2)
        for i in range(2, half + 1): add(1, i)
        prev = half
        for i in range(half + 1, n + 1): add(prev, i); prev = i
    elif mode == "right-skewed binary":
        for i in range(2, n + 1): add(i - 1, i)
    elif mode == "left-skewed binary":
        for i in range(2, n + 1):
            parent = max(1, i - 2) if i % 2 == 0 else i - 1
            add(parent, i)
    elif mode == "complete ternary tree":
        for i in range(2, n + 1): add((i - 2) // 3 + 1, i)
    elif mode == "centipede (chain of chains)":
        main_len = max(2, n // 2)
        for i in range(1, main_len): add(i, i + 1)
        leaf_idx = main_len + 1
        for i in range(1, main_len + 1):
            if leaf_idx > n: break
            add(i, leaf_idx); leaf_idx += 1
        while leaf_idx <= n: add(random.randint(1, leaf_idx - 1), leaf_idx); leaf_idx += 1
    elif mode == "forest-like (star of stars)":
        k = random.randint(2, max(2, min(6, n // 3)))
        for i in range(2, k + 2): add(1, i)
        idx = k + 2
        for star_root in range(2, k + 2):
            while idx <= n:
                add(star_root, idx); idx += 1
                if random.random() < 0.4: break
        while idx <= n: add(random.randint(1, idx - 1), idx); idx += 1
    elif mode in ("single node (n=1)", "two nodes (n=2)", "three nodes (n=3)"):
        for i in range(2, n + 1): add(i - 1, i)
    else:
        for i in range(2, n + 1): add(random.randint(1, i - 1), i)

    return edges, n


# ─────────────────────────────────────────────
#  Graph Generator
# ─────────────────────────────────────────────
def generate_graph(n, m, mode, directed=False, weighted=False, w_lo=1, w_hi=100, allow_self=False, allow_multi=False):
    if n <= 0: return 0, 0, []

    edge_set = set()
    edges = []

    def try_add(u, v):
        if not allow_self and u == v: return False
        key = (u, v) if directed else (min(u, v), max(u, v))
        if not allow_multi and key in edge_set: return False
        edge_set.add(key)
        w = f" {random.randint(w_lo, w_hi)}" if weighted else ""
        edges.append(f"{u} {v}{w}")
        return True

    def fill(target):
        att = 0
        while len(edges) < target and att < target * 30:
            try_add(random.randint(1, n), random.randint(1, n)); att += 1

    if mode == "random":
        mode = random.choice(GRAPH_MODES[1:])

    if mode == "single node": n = 1
    elif mode == "two nodes": n = max(n, 2)
    elif mode == "empty (no edges)": return n, 0, []

    if mode == "random sparse":
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
        fill(min(m, n + n // 2))
    elif mode == "random medium density":
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
        fill(min(m, n * max(1, int(math.log2(n + 1)))))
    elif mode == "random dense":
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
        fill(min(m, n * (n - 1) // 2))
    elif mode == "complete graph":
        for u in range(1, n + 1):
            for v in range(u + 1, n + 1): try_add(u, v)
    elif mode == "tree (connected acyclic)":
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
    elif mode == "connected random":
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
        fill(m)
    elif mode == "disconnected (2 components)":
        half = max(1, n // 2)
        for i in range(2, half + 1): try_add(random.randint(1, i - 1), i)
        for i in range(half + 2, n + 1): try_add(random.randint(half + 1, i - 1), i)
    elif mode == "disconnected (many components)":
        comp = random.randint(3, max(3, n // 3))
        sz = max(1, n // comp)
        for c in range(comp):
            base = c * sz + 1; top = min(base + sz - 1, n)
            for i in range(base + 1, top + 1): try_add(random.randint(base, i - 1), i)
    elif mode == "single isolated node + rest connected":
        iso = random.randint(1, n)
        others = [i for i in range(1, n + 1) if i != iso]
        for i in range(1, len(others)):
            try_add(others[random.randint(0, i - 1)], others[i])
        fill(m)
    elif mode == "path graph":
        for i in range(1, n): try_add(i, i + 1)
    elif mode == "cycle graph":
        for i in range(1, n): try_add(i, i + 1)
        if n >= 2: try_add(n, 1)
    elif mode == "wheel graph":
        for i in range(2, n + 1): try_add(1, i)
        for i in range(2, n): try_add(i, i + 1)
        if n >= 3: try_add(n, 2)
    elif mode == "grid graph":
        cols = max(1, int(n ** 0.5))
        for node in range(1, n + 1):
            c = (node - 1) % cols
            if c + 1 < cols and node + 1 <= n: try_add(node, node + 1)
            if node + cols <= n: try_add(node, node + cols)
    elif mode == "ladder graph":
        half = max(2, n // 2)
        for i in range(1, half): try_add(i, i + 1)
        for i in range(half + 1, n): try_add(i, i + 1)
        for i in range(1, min(half, n - half) + 1): try_add(i, i + half)
    elif mode == "petersen-like":
        outer = max(3, n // 2); inner = n - outer
        for i in range(1, outer): try_add(i, i + 1)
        try_add(outer, 1)
        for i in range(outer + 1, n + 1): try_add(outer + 1, i)
        for i in range(1, min(outer, inner) + 1): try_add(i, outer + i)
    elif mode == "tournament (directed complete)":
        for u in range(1, n + 1):
            for v in range(u + 1, n + 1):
                if random.random() < 0.5: try_add(u, v)
                else: try_add(v, u)
    elif mode == "bipartite random":
        half = max(1, n // 2)
        att = 0
        while len(edges) < m and att < m * 20:
            try_add(random.randint(1, half), random.randint(half + 1, n)); att += 1
    elif mode == "bipartite complete":
        half = max(1, n // 2)
        for u in range(1, half + 1):
            for v in range(half + 1, n + 1): try_add(u, v)
    elif mode == "bipartite unbalanced":
        left = max(1, n // 4)
        for u in range(1, left + 1):
            for v in range(left + 1, n + 1):
                if random.random() < 0.6: try_add(u, v)
    elif mode == "DAG random":
        for _ in range(m):
            u, v = random.randint(1, n - 1), random.randint(2, n)
            if u < v: try_add(u, v)
    elif mode == "DAG layered":
        layers = random.randint(2, max(2, min(6, n)))
        lsz = max(1, n // layers)
        for u in range(1, n + 1):
            for v in range(u + 1, min(u + lsz + 1, n + 1)):
                if random.random() < 0.5: try_add(u, v)
    elif mode == "DAG single source":
        for i in range(2, n + 1): try_add(1, i)
        fill(m)
    elif mode == "DAG single sink":
        for i in range(1, n): try_add(i, n)
        fill(m)
    elif mode == "sparse with one hub":
        for i in range(2, n + 1): try_add(1, i)
        fill(min(m, n + n // 3))
    elif mode == "multiple hubs":
        hubs = random.randint(2, max(2, min(5, n // 3)))
        for h in range(1, hubs + 1):
            for i in range(hubs + 1, n + 1):
                if random.random() < 0.4: try_add(h, i)
        fill(m)
    elif mode == "two nodes":
        try_add(1, 2)
    elif mode == "self loops only":
        for i in range(1, n + 1): edges.append(f"{i} {i}")
    elif mode == "multi edges only":
        if n >= 2:
            for _ in range(m): edges.append(f"1 2")
    elif mode == "graph with bridge":
        half = max(2, n // 2)
        for i in range(2, half + 1): try_add(random.randint(1, i - 1), i)
        try_add(half, half + 1)
        for i in range(half + 2, n + 1): try_add(random.randint(half + 1, i - 1), i)
    elif mode == "graph with articulation point":
        mid = random.randint(2, max(2, n - 1))
        for i in range(2, mid): try_add(random.randint(1, i - 1), i)
        for i in range(mid + 1, n + 1): try_add(mid, i)
        try_add(1, mid)
    elif mode == "source-sink layered":
        layers = random.randint(2, max(2, min(5, n)))
        lsz = max(1, n // layers)
        lo_f = lambda u: (u - 1) // lsz
        for u in range(1, n + 1):
            for v in range(u + 1, n + 1):
                if lo_f(v) == lo_f(u) + 1 and random.random() < 0.5: try_add(u, v)
    elif mode == "clique + path tail":
        clique_sz = max(2, n // 2)
        for u in range(1, clique_sz + 1):
            for v in range(u + 1, clique_sz + 1): try_add(u, v)
        for i in range(clique_sz + 1, n + 1): try_add(i - 1, i)
    elif mode == "two cliques connected by bridge":
        half = max(2, n // 2)
        for u in range(1, half + 1):
            for v in range(u + 1, half + 1): try_add(u, v)
        for u in range(half + 1, n + 1):
            for v in range(u + 1, n + 1): try_add(u, v)
        try_add(half, half + 1)
    elif mode == "random planar-like":
        cols = max(1, int(n ** 0.5))
        for node in range(1, n + 1):
            c = (node - 1) % cols
            if c + 1 < cols and node + 1 <= n: try_add(node, node + 1)
            if node + cols <= n: try_add(node, node + cols)
        fill(min(m, n + n // 2))
    elif mode == "star of cliques":
        k = random.randint(2, max(2, min(5, n // 3)))
        clique_sz = max(2, (n - 1) // k)
        center = 1
        idx = 2
        for _ in range(k):
            clique_start = idx
            for i in range(clique_sz):
                if idx > n: break
                try_add(center, idx)
                for j in range(clique_start, idx): try_add(j, idx)
                idx += 1
        while idx <= n: try_add(random.randint(1, idx - 1), idx); idx += 1
    else:
        for i in range(2, n + 1): try_add(random.randint(1, i - 1), i)
        fill(m)

    return n, len(edges), edges


# ─────────────────────────────────────────────
#  Compile helpers
# ─────────────────────────────────────────────
def compile_cpp(code, name):
    tmp = tempfile.gettempdir()
    cpp_path = os.path.join(tmp, f"{name}.cpp")
    exe_path = os.path.join(tmp, name)
    with open(cpp_path, "w",encoding="utf-8") as f: f.write(code)
    res = subprocess.run(["g++", "-std=c++17", "-O2", "-o", exe_path, cpp_path],
                         capture_output=True, text=True)
    return exe_path, res

def run_exe(exe, stdin_data, timeout=5):
    try:
        res = subprocess.run([exe], input=stdin_data, text=True,
                             capture_output=True, timeout=timeout)
        return res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return "TLE", ""
    except Exception as e:
        return f"ERROR: {e}", ""


# ─────────────────────────────────────────────
#  PARALLEL runner: run both programs at once
# ─────────────────────────────────────────────
def run_pair(run1, run2, stdin_data):
    """Run both solutions in parallel threads. Returns (out1,err1,out2,err2)."""
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(run1, stdin_data)
        f2 = ex.submit(run2, stdin_data)
        o1, e1 = f1.result()
        o2, e2 = f2.result()
    return o1, e1, o2, e2


# ─────────────────────────────────────────────
#  BINARY SEARCH isolation  (O(log T) runs)
#
#  Strategy:
#    1. Split bodies into left half and right half.
#    2. Run the full left half as "len(left)\nbody1body2...".
#    3. If mismatch is in left → recurse left; else recurse right.
#    4. Base case: single body → that's the culprit.
#
#  Each level does ONE pair of runs (parallelised), so total cost is
#  O(log T) paired runs instead of O(T) sequential runs.
# ─────────────────────────────────────────────
def _make_multi(bodies):
    """Pack a list of pre-generated bodies into a valid multi-TC string."""
    return f"{len(bodies)}\n" + "".join(bodies)

def isolate_failing_tc_binary(bodies, run1_fn, run2_fn):
    """
    Binary-search for the first failing test case body.
    Returns (tc_index_1based, body, o1, e1, o2, e2) or None if flaky.
    Uses O(log T) parallel run-pairs.
    """
    lo, hi = 0, len(bodies) - 1

    while lo < hi:
        mid = (lo + hi) // 2
        left_bodies = bodies[lo: mid + 1]

        left_input = _make_multi(left_bodies)
        o1, e1, o2, e2 = run_pair(run1_fn, run2_fn, left_input)

        if o1 != o2:
            hi = mid        # failure is in left half
        else:
            lo = mid + 1    # failure must be in right half

    # lo == hi: single candidate
    body = bodies[lo]
    single = f"1\n{body}"
    o1, e1, o2, e2 = run_pair(run1_fn, run2_fn, single)

    if o1 != o2:
        return lo + 1, body, o1, e1, o2, e2   # 1-based index
    return None   # flaky


# ─────────────────────────────────────────────
#  Helper: code input widget (paste or file)
# ─────────────────────────────────────────────
def code_input_widget(label, key, placeholder=""):
    input_mode = st.radio(
        f"Input mode",
        ["✏️ Paste code", "📂 Upload file"],
        horizontal=True,
        key=f"{key}_mode",
        label_visibility="collapsed",
    )
    code = ""
    if input_mode == "✏️ Paste code":
        code = st.text_area(label, height=280, key=f"{key}_paste",
                            placeholder=placeholder, label_visibility="collapsed")
    else:
        uploaded = st.file_uploader(
            f"Upload {label}",
            type=["cpp", "py", "txt", "java", "go", "rs"],
            key=f"{key}_file",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                code = uploaded.read().decode("utf-8")
                st.code(code[:3000] + ("…" if len(code) > 3000 else ""),
                        language="cpp" if uploaded.name.endswith(".cpp") else "python")
            except Exception as e:
                st.error(f"Could not read file: {e}")
        else:
            st.caption("No file chosen — drop a `.cpp`, `.py`, or `.txt` file above.")
    return code


# ─────────────────────────────────────────────
#  UI — Programs
# ─────────────────────────────────────────────
st.markdown("## 💻 Programs")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Brute Force**")
    code1 = code_input_widget("Brute Force", key="code1", placeholder="// brute force")
with col2:
    st.markdown("**Optimized**")
    code2 = code_input_widget("Optimized", key="code2", placeholder="// optimized")
lang = st.selectbox("Language", ["C++17", "Python3"])

# ─────────────────────────────────────────────
#  UI — Components
# ─────────────────────────────────────────────
st.markdown("## 🧩 Test Components")
tabs = st.tabs(["🔢 Integers", "📊 Arrays", "🔤 Strings", "🌳 Trees", "🕸️ Graphs", "⚙️ Custom"])

# Tab 0: Scalars
with tabs[0]:
    st.markdown("### Scalar Variables  *(space-separated on line 1)*")
    num_vars = st.slider("Count", 0, 10, 2, key="sv_count")
    var_defs = []
    for i in range(num_vars):
        c1, c2, c3 = st.columns(3)
        with c1: vname = st.text_input("Name", value=["n","m","k","q","t","x","y","z","a","b"][i] if i < 10 else f"v{i}", key=f"sv_name_{i}")
        with c2: vlo = st.number_input("Min", value=1, key=f"sv_lo_{i}")
        with c3: vhi = st.number_input("Max", value=10**5, key=f"sv_hi_{i}")
        var_defs.append((vname, int(vlo), int(vhi)))

# Tab 1: Arrays
with tabs[1]:
    st.markdown("### Integer Arrays")
    num_arrays = st.slider("Count", 0, 8, 1, key="arr_count")
    array_defs = []
    for i in range(num_arrays):
        with st.expander(f"Array {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                sz_from = st.selectbox("Size from", ["scalar variable", "fixed value"], key=f"arr_sz_from_{i}")
                if sz_from == "scalar variable" and var_defs:
                    sz_var = st.selectbox("Variable", [v[0] for v in var_defs], key=f"arr_sz_var_{i}")
                    sz_fixed = None
                else:
                    sz_var = None
                    sz_fixed = num_input("Fixed size", f"arr_sz_fixed_{i}", default=10, min_val=0)
            with c2:
                arr_lo = st.number_input("Min value", value=1, key=f"arr_lo_{i}")
                arr_hi = st.number_input("Max value", value=10**9, key=f"arr_hi_{i}")
            with c3:
                arr_mode = st.selectbox("Distribution", INT_MODES, key=f"arr_mode_{i}")
            print_sz = st.checkbox("Print size on separate line before array", value=False, key=f"arr_print_sz_{i}")
            array_defs.append((sz_from, sz_var, sz_fixed, int(arr_lo), int(arr_hi), arr_mode, print_sz))

# Tab 2: Strings
with tabs[2]:
    st.markdown("### Strings")
    num_strings = st.slider("Count", 0, 6, 0, key="str_count")
    string_defs = []
    for i in range(num_strings):
        with st.expander(f"String {i+1}", expanded=(i == 0)):
            c1, c2 = st.columns(2)
            with c1:
                str_sz_from = st.selectbox("Length from", ["scalar variable", "fixed value"], key=f"str_sz_from_{i}")
                if str_sz_from == "scalar variable" and var_defs:
                    str_sz_var = st.selectbox("Variable", [v[0] for v in var_defs], key=f"str_sz_var_{i}")
                    str_sz_fixed = None
                else:
                    str_sz_var = None
                    str_sz_fixed = num_input("Fixed length", f"str_sz_fixed_{i}", default=10, min_val=0)
            with c2:
                str_mode = st.selectbox("Distribution", STRING_MODES, key=f"str_mode_{i}")
            print_len = st.checkbox("Print length before string", value=False, key=f"str_print_len_{i}")
            string_defs.append((str_sz_from, str_sz_var, str_sz_fixed, str_mode, print_len))

# Tab 3: Trees
with tabs[3]:
    st.markdown("### Trees")
    num_trees = st.slider("Count", 0, 3, 0, key="tr_count")
    tree_defs = []
    for i in range(num_trees):
        with st.expander(f"Tree {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                tr_n_from = st.selectbox("N from", ["scalar variable", "fixed value"], key=f"tr_n_from_{i}")
                if tr_n_from == "scalar variable" and var_defs:
                    tr_n_var = st.selectbox("Variable", [v[0] for v in var_defs], key=f"tr_n_var_{i}")
                    tr_n_fixed = None
                else:
                    tr_n_var = None
                    tr_n_fixed = num_input("Fixed N", f"tr_n_fixed_{i}", default=10, min_val=1)
            with c2:
                tr_mode = st.selectbox("Shape", TREE_MODES, key=f"tr_mode_{i}")
                tr_directed = st.checkbox("Directed edges", key=f"tr_dir_{i}")
            with c3:
                tr_weighted = st.checkbox("Weighted", key=f"tr_w_{i}")
                tr_wlo = int(st.number_input("Weight min", value=1, key=f"tr_wlo_{i}")) if tr_weighted else 1
                tr_whi = int(st.number_input("Weight max", value=100, key=f"tr_whi_{i}")) if tr_weighted else 100
            print_n = st.checkbox("Print N before edges", value=True, key=f"tr_print_n_{i}")
            shuffle_e = st.checkbox("Shuffle edge order", value=True, key=f"tr_shuffle_{i}")
            flip_e = st.checkbox("Randomly flip edge direction (undirected)", value=True, key=f"tr_flip_{i}")
            tree_defs.append((tr_n_from, tr_n_var, tr_n_fixed, tr_mode, tr_directed,
                               tr_weighted, tr_wlo, tr_whi, print_n, shuffle_e, flip_e))

# Tab 4: Graphs
with tabs[4]:
    st.markdown("### Graphs")
    num_graphs = st.slider("Count", 0, 3, 0, key="gr_count")
    graph_defs = []
    for i in range(num_graphs):
        with st.expander(f"Graph {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                gr_n_from = st.selectbox("N from", ["scalar variable", "fixed value"], key=f"gr_n_from_{i}")
                if gr_n_from == "scalar variable" and var_defs:
                    gr_n_var = st.selectbox("N variable", [v[0] for v in var_defs], key=f"gr_n_var_{i}")
                    gr_n_fixed = None
                else:
                    gr_n_var = None
                    gr_n_fixed = num_input("Fixed N", f"gr_n_fixed_{i}", default=5, min_val=1)
                gr_m_from = st.selectbox("M from", ["scalar variable", "fixed value"], key=f"gr_m_from_{i}")
                if gr_m_from == "scalar variable" and var_defs:
                    gr_m_var = st.selectbox("M variable", [v[0] for v in var_defs], key=f"gr_m_var_{i}")
                    gr_m_fixed = None
                else:
                    gr_m_var = None
                    gr_m_fixed = num_input("Fixed M", f"gr_m_fixed_{i}", default=7, min_val=0)
            with c2:
                gr_mode = st.selectbox("Structure", GRAPH_MODES, key=f"gr_mode_{i}")
                gr_directed = st.checkbox("Directed", key=f"gr_dir_{i}")
            with c3:
                gr_weighted = st.checkbox("Weighted", key=f"gr_w_{i}")
                gr_wlo = int(st.number_input("Weight min", value=1, key=f"gr_wlo_{i}")) if gr_weighted else 1
                gr_whi = int(st.number_input("Weight max", value=100, key=f"gr_whi_{i}")) if gr_weighted else 100
                gr_self = st.checkbox("Allow self-loops", key=f"gr_self_{i}")
                gr_multi = st.checkbox("Allow multi-edges", key=f"gr_multi_{i}")
            print_nm = st.checkbox("Print N M before edges", value=True, key=f"gr_print_nm_{i}")
            graph_defs.append((gr_n_from, gr_n_var, gr_n_fixed, gr_m_from, gr_m_var, gr_m_fixed,
                                gr_mode, gr_directed, gr_weighted, gr_wlo, gr_whi,
                                gr_self, gr_multi, print_nm))

# Tab 5: Custom
with tabs[5]:
    st.markdown("### Custom Python Snippet")
    st.caption("Append to `test`. You have: `random`, `math`, `var_values` dict, and all scalar vars by name.")
    custom_gen = st.text_area("Code", height=200, placeholder=
"""# example: generate Q queries after the main input
# for _ in range(var_values.get('q', 3)):
#     l = random.randint(1, var_values.get('n', 10))
#     r = random.randint(l, var_values.get('n', 10))
#     test += f"{l} {r}\\n"
""")

# ─────────────────────────────────────────────
#  Run Settings
# ─────────────────────────────────────────────
st.markdown("## ⚙️ Settings")
c1, c2, c3 = st.columns(3)
with c1:
    num_tests = num_input("Number of tests (files)", "num_tests", default=100, min_val=1)
with c2:
    timeout_sec = int(st.number_input("Timeout per test (s)", min_value=1, max_value=60, value=5))
with c3:
    stop_on_first = st.checkbox("Stop on first mismatch", value=True)
    show_passing = st.checkbox("Show live pass count", value=True)

# ── Multi-test case wrapper ───────────────────
with st.expander("📦 Multi-test case mode  *(problems with T test cases per input)*", expanded=False):
    st.caption(
        "When enabled every input file starts with **T** followed by T independent test cases. "
        "On mismatch the runner uses **binary search** to isolate the single failing test case "
        "in **O(log T) run-pairs** instead of O(T) — both programs run in parallel each step."
    )
    mtc_enabled = st.checkbox("Enable multi-test case mode", value=False, key="mtc_on")
    mc1, mc2 = st.columns(2)
    with mc1:
        mtc_t_min = int(st.number_input("T min", min_value=1, value=2, key="mtc_tmin"))
        mtc_t_max = int(st.number_input("T max", min_value=1, value=10, key="mtc_tmax"))
    with mc2:
        st.markdown("")
        st.markdown("")
        st.info(
            "Each test case body uses **exactly the same component configuration** "
            "defined in the tabs above — scalars, arrays, strings, trees, graphs, custom snippet."
        )

run_btn = st.button("🚀 RUN STRESS TEST", use_container_width=True)

# ─────────────────────────────────────────────
#  Build one test-case body  (no T wrapper)
# ─────────────────────────────────────────────
def build_test(var_defs, array_defs, string_defs, tree_defs, graph_defs, custom_gen):
    test = ""
    var_values = {}

    for (vname, vlo, vhi) in var_defs:
        var_values[vname] = random.randint(vlo, vhi)
    if var_defs:
        test += " ".join(str(var_values[v[0]]) for v in var_defs) + "\n"

    def resolve(from_mode, var, fixed):
        if from_mode == "scalar variable" and var and var in var_values:
            return max(0, var_values[var])
        return fixed if fixed is not None else 10

    for (sz_from, sz_var, sz_fixed, alo, ahi, amode, print_sz) in array_defs:
        sz = resolve(sz_from, sz_var, sz_fixed)
        arr = generate_int_array(sz, alo, ahi, amode)
        if print_sz: test += f"{sz}\n"
        test += " ".join(map(str, arr)) + "\n"

    for (sz_from, sz_var, sz_fixed, smode, print_len) in string_defs:
        sz = resolve(sz_from, sz_var, sz_fixed)
        s = generate_string(sz, smode)
        if print_len: test += f"{sz}\n"
        test += s + "\n"

    for (n_from, n_var, n_fixed, tmode, directed, weighted, wlo, whi,
         print_n, shuffle_edges, flip_edge) in tree_defs:
        n = max(1, resolve(n_from, n_var, n_fixed))
        edges, actual_n = generate_tree(n, tmode, weighted, wlo, whi, directed)
        if shuffle_edges: random.shuffle(edges)
        if flip_edge and not directed:
            flipped = []
            for e in edges:
                parts = e.split()
                if random.random() < 0.5:
                    parts[0], parts[1] = parts[1], parts[0]
                flipped.append(" ".join(parts))
            edges = flipped
        if print_n: test += f"{actual_n}\n"
        for e in edges: test += e + "\n"

    for (n_from, n_var, n_fixed, m_from, m_var, m_fixed,
         gmode, directed, weighted, wlo, whi, allow_self, allow_multi, print_nm) in graph_defs:
        n = max(1, resolve(n_from, n_var, n_fixed))
        m = max(0, resolve(m_from, m_var, m_fixed))
        actual_n, actual_m, gedges = generate_graph(n, m, gmode, directed, weighted, wlo, whi, allow_self, allow_multi)
        if print_nm: test += f"{actual_n} {actual_m}\n"
        for e in gedges: test += e + "\n"

    if custom_gen.strip():
        try:
            local_vars = {"test": test, "random": random, "math": math,
                          "var_values": var_values, **var_values}
            exec(custom_gen, local_vars)
            test = local_vars.get("test", test)
        except Exception as ex:
            test += f"# CUSTOM GEN ERROR: {ex}\n"

    return test


# ─────────────────────────────────────────────
#  Build a multi-TC file: "T\n<tc1><tc2>..."
#  Returns (full_input_str, list_of_individual_tc_bodies)
# ─────────────────────────────────────────────
def build_multi_test(t_count, var_defs, array_defs, string_defs,
                     tree_defs, graph_defs, custom_gen):
    bodies = [
        build_test(var_defs, array_defs, string_defs, tree_defs, graph_defs, custom_gen)
        for _ in range(t_count)
    ]
    full = f"{t_count}\n" + "".join(bodies)
    return full, bodies


# ─────────────────────────────────────────────
#  Run
# ─────────────────────────────────────────────
if run_btn:
    if not code1.strip() or not code2.strip():
        st.warning("⚠️ Provide both programs!"); st.stop()

    st.markdown("---")
    st.info("🔧 Compiling...")

    if lang == "C++17":
        exe1, res1 = compile_cpp(code1, "brute")
        exe2, res2 = compile_cpp(code2, "optim")
        if res1.returncode != 0:
            st.error("❌ Brute force compilation failed"); st.code(res1.stderr); st.stop()
        if res2.returncode != 0:
            st.error("❌ Optimized compilation failed"); st.code(res2.stderr); st.stop()
        st.success("✅ Compiled successfully")
        run1 = lambda t: run_exe(exe1, t, timeout_sec)
        run2 = lambda t: run_exe(exe2, t, timeout_sec)
    else:
        tmp = tempfile.gettempdir()
        p1 = os.path.join(tmp, "brute.py"); p2 = os.path.join(tmp, "optim.py")
        with open(p1, "w") as f: f.write(code1)
        with open(p2, "w") as f: f.write(code2)
        def run_py(path, t):
            try:
                r = subprocess.run(["python3", path], input=t, text=True,
                                   capture_output=True, timeout=timeout_sec)
                return r.stdout.strip(), r.stderr.strip()
            except subprocess.TimeoutExpired:
                return "TLE", ""
        run1 = lambda t: run_py(p1, t)
        run2 = lambda t: run_py(p2, t)
        st.success("✅ Ready (Python — no compilation)")

    progress = st.progress(0)
    status_txt = st.empty()
    passed = 0
    mismatches = []

    for i in range(1, num_tests + 1):
        if mtc_enabled:
            t_count = random.randint(
                min(mtc_t_min, mtc_t_max),
                max(mtc_t_min, mtc_t_max)
            )
            full_input, bodies = build_multi_test(
                t_count, var_defs, array_defs, string_defs,
                tree_defs, graph_defs, custom_gen
            )
            # ── Run both solutions in parallel ──
            out1, err1, out2, err2 = run_pair(run1, run2, full_input)
        else:
            full_input = build_test(var_defs, array_defs, string_defs,
                                    tree_defs, graph_defs, custom_gen)
            # ── Run both solutions in parallel ──
            out1, err1, out2, err2 = run_pair(run1, run2, full_input)
            bodies = None

        progress.progress(i / num_tests)
        if show_passing:
            status_txt.text(f"Test {i}/{num_tests}  |  ✅ Passed: {passed}")

        if out1 != out2:
            if mtc_enabled and bodies:
                status_txt.text(
                    f"Test {i}/{num_tests}  |  ✅ Passed: {passed}  |  "
                    f"🔍 Binary-searching failing TC (≤{math.ceil(math.log2(len(bodies)+1))} steps)..."
                )
                result = isolate_failing_tc_binary(bodies, run1, run2)
                if result:
                    tc_idx, bad_body, b_o1, b_e1, b_o2, b_e2 = result
                    mismatches.append((i, tc_idx, t_count, bad_body, b_o1, b_e1, b_o2, b_e2))
                else:
                    mismatches.append((i, None, t_count, full_input, out1, err1, out2, err2))
            else:
                mismatches.append((i, None, None, full_input, out1, err1, out2, err2))

            if stop_on_first:
                break
        else:
            passed += 1

    progress.progress(1.0)

    if mismatches:
        st.error(f"❌ {len(mismatches)} mismatch(es) found!  (Passed: {passed})")
        for idx, record in enumerate(mismatches):
            file_i, tc_idx, t_count, body, o1, e1, o2, e2 = record
            if mtc_enabled and tc_idx is not None:
                title = f"🔴 Mismatch #{idx+1} — File {file_i}, TC {tc_idx}/{t_count}"
                note  = (f"*(isolated via binary search from a {t_count}-TC file "
                         f"in ≤{math.ceil(math.log2(t_count+1))} run-pairs — showing only the failing case)*")
            elif mtc_enabled and tc_idx is None:
                title = f"🔴 Mismatch #{idx+1} — File {file_i}  *(flaky — could not isolate)*"
                note  = "Both programs disagreed on the full file but agreed when re-run per case."
            else:
                title = f"🔴 Mismatch #{idx+1} — Test {file_i}"
                note  = ""

            with st.expander(title, expanded=(idx == 0)):
                if note:
                    st.caption(note)
                st.subheader("Input")
                st.code(body)
                ca, cb = st.columns(2)
                with ca:
                    st.subheader("Brute Output"); st.code(o1 or "(empty)")
                    if e1: st.caption(f"stderr: {e1[:400]}")
                with cb:
                    st.subheader("Optimized Output"); st.code(o2 or "(empty)")
                    if e2: st.caption(f"stderr: {e2[:400]}")
    else:
        st.success(f"🎉 All {num_tests} tests passed! Both programs agree.")
        st.balloons()
