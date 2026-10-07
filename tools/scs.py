"""Independent shortest-common-superstring baselines.

`greedy_superstring` repeatedly merges the pair with the largest prefix-suffix
overlap. Ties keep the smallest left index, then the smallest right index.

`exact_superstring` deletes strings that are already contiguous substrings of
another input (one copy of a duplicated string is kept) and then solves the
resulting overlap Hamiltonian path by dynamic programming. On a substring-free
instance that path has the same optimum as the original SCS problem.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass


def overlap(left: str, right: str) -> int:
    """Largest k with left[-k:] == right[:k], including a full swallow."""
    limit = min(len(left), len(right))
    for k in range(limit, 0, -1):
        if left[-k:] == right[:k]:
            return k
    return 0


def merge(left: str, right: str, k: int | None = None) -> str:
    if k is None:
        k = overlap(left, right)
    return left + right[k:]


def remove_contained(strings: list[str]) -> list[str]:
    """Drop a string when it already occurs inside a different input.

    Equal copies: the later copy is dropped, so one remains.
    """
    kept: list[str] = []
    for index, string in enumerate(strings):
        redundant = False
        for other_index, other in enumerate(strings):
            if index == other_index:
                continue
            if string in other and (string != other or index > other_index):
                redundant = True
                break
        if not redundant:
            kept.append(string)
    return kept


def greedy_superstring(strings: list[str]) -> str:
    pool = list(strings)
    if not pool:
        return ""
    while len(pool) > 1:
        best: tuple[int, int, int] | None = None
        for i in range(len(pool)):
            for j in range(len(pool)):
                if i == j:
                    continue
                score = overlap(pool[i], pool[j])
                cand = (score, -i, -j)
                if best is None or cand > best:
                    best = cand
        assert best is not None
        score, neg_i, neg_j = best
        i, j = -neg_i, -neg_j
        merged = merge(pool[i], pool[j], score)
        if i < j:
            del pool[j]
            pool[i] = merged
        else:
            del pool[i]
            pool[j] = merged
    return pool[0]


@dataclass(frozen=True)
class ExactResult:
    superstring: str
    length: int


def exact_superstring(strings: list[str]) -> ExactResult:
    """Optimum SCS via subset DP. Practical for roughly n <= 15 kept strings."""
    core = remove_contained(strings)
    if not core:
        return ExactResult("", 0)
    n = len(core)
    if n > 20:
        raise ValueError(f"exact SCS refused: {n} strings after containment filtering")
    overlaps = [[overlap(core[i], core[j]) for j in range(n)] for i in range(n)]
    size = 1 << n
    inf = sum(len(s) for s in core) + 1
    dp = [[inf] * n for _ in range(size)]
    parent: list[list[int | None]] = [[None] * n for _ in range(size)]
    for i, string in enumerate(core):
        dp[1 << i][i] = len(string)
    for mask in range(size):
        for i in range(n):
            if dp[mask][i] >= inf or (mask & (1 << i)) == 0:
                continue
            for j in range(n):
                if mask & (1 << j):
                    continue
                nxt = mask | (1 << j)
                cand = dp[mask][i] + len(core[j]) - overlaps[i][j]
                if cand < dp[nxt][j]:
                    dp[nxt][j] = cand
                    parent[nxt][j] = i
    full = size - 1
    end = min(range(n), key=lambda i: dp[full][i])
    order = [end]
    mask = full
    while parent[mask][order[-1]] is not None:
        prev = parent[mask][order[-1]]
        assert prev is not None
        mask ^= 1 << order[-1]
        order.append(prev)
    order.reverse()
    text = core[order[0]]
    for prev, nxt in zip(order, order[1:]):
        text = merge(text, core[nxt], overlaps[prev][nxt])
    return ExactResult(text, len(text))


def brute_opt_length(strings: list[str], search_cap: int = 50_000) -> int | None:
    """Length of a shortest superstring by enumerating candidates.

    Returns None when the alphabet is large enough that the next length would
    exceed `search_cap` candidates. Used only to test the DP.
    """
    if all(s == "" for s in strings):
        return 0
    alphabet = sorted(set("".join(strings)))
    if not alphabet:
        return 0
    upper = sum(len(s) for s in remove_contained(strings))
    for length in range(upper + 1):
        space = len(alphabet) ** length if length else 1
        if space > search_cap:
            return None
        if length == 0:
            if all(s in "" for s in strings):
                return 0
            continue
        for chars in itertools.product(alphabet, repeat=length):
            text = "".join(chars)
            if all(s in text for s in strings):
                return length
    return upper
