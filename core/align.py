"""
Phoneme-level alignment between an expected phoneme sequence and an actual
(recognized) one, using classic Needleman-Wunsch / edit-distance dynamic
programming with traceback.

Each aligned pair is tagged as one of:
  - "match"  : expected phone == produced phone
  - "sub"    : expected phone was replaced by a different produced phone
  - "omit"   : expected phone was dropped entirely (nothing produced for it)
  - "add"    : an extra phone was produced that wasn't expected

This is the same idea as Word Error Rate, one level down at the phoneme
level, which is what actually catches misarticulations (word-level ASR
tends to "autocorrect" a mispronounced word back to the intended one).
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PhonemeOp:
    expected: Optional[str]
    actual: Optional[str]
    op: str  # "match" | "sub" | "omit" | "add"


def align_phonemes(expected: List[str], actual: List[str]) -> List[PhonemeOp]:
    n, m = len(expected), len(actual)

    # dp[i][j] = edit distance between expected[:i] and actual[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if expected[i - 1] == actual[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],  # substitution
                    dp[i - 1][j],      # omission (expected phone dropped)
                    dp[i][j - 1],      # addition (extra produced phone)
                )

    # Traceback from (n, m) to (0, 0)
    i, j = n, m
    ops: List[PhonemeOp] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and expected[i - 1] == actual[j - 1] and dp[i][j] == dp[i - 1][j - 1]:
            ops.append(PhonemeOp(expected[i - 1], actual[j - 1], "match"))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append(PhonemeOp(expected[i - 1], actual[j - 1], "sub"))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(PhonemeOp(expected[i - 1], None, "omit"))
            i -= 1
        else:
            ops.append(PhonemeOp(None, actual[j - 1], "add"))
            j -= 1

    ops.reverse()
    return ops


def accuracy(ops: List[PhonemeOp]) -> float:
    expected_count = sum(1 for o in ops if o.expected is not None)
    matches = sum(1 for o in ops if o.op == "match")
    return matches / expected_count if expected_count else 0.0


def errors_only(ops: List[PhonemeOp]) -> List[PhonemeOp]:
    return [o for o in ops if o.op != "match"]


if __name__ == "__main__":
    # Classic /r/ -> /w/ substitution: "rabbit" said as "wabbit"
    expected = ["ɹ", "æ", "b", "ɪ", "t"]
    actual = ["w", "æ", "b", "ɪ", "t"]
    result = align_phonemes(expected, actual)
    for o in result:
        print(o)
    print("accuracy:", accuracy(result))
    print("errors:", errors_only(result))

    print()
    # Omission: "thumb" said without the initial "th" -> "um"
    expected2 = ["θ", "ʌ", "m"]
    actual2 = ["ʌ", "m"]
    result2 = align_phonemes(expected2, actual2)
    for o in result2:
        print(o)
    print("accuracy:", accuracy(result2))
