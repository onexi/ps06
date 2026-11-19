"""Rank plausible label matches by text similarity for human review."""
from difflib import SequenceMatcher


def parse_match_threshold(value):
    if isinstance(value, str):
        value = int(value)
    if not isinstance(value, int) or not 1 <= value <= 100:
        raise ValueError('Match threshold must be a whole number from 1 to 100.')
    return value


def _is_single_letter_typo(left, right):
    shorter, longer = sorted((left, right), key=len)
    if len(shorter) < 5 or not shorter.isalpha() or not longer.isalpha():
        return False
    if len(shorter) == len(longer):
        differences = [index for index, (a, b) in enumerate(zip(shorter, longer)) if a != b]
        if len(differences) == 1:
            return True
        if len(differences) == 2:
            first, second = differences
            return second == first + 1 and shorter[first:second + 1] == longer[first:second + 1][::-1]
        return False
    if len(longer) != len(shorter) + 1:
        return False
    return any(longer[:index] + longer[index + 1:] == shorter for index in range(len(longer)))


def _is_plausible_match(term, candidate):
    # A complete label phrase can be part of a more specific name.
    if f' {term} ' in f' {candidate} ' or f' {candidate} ' in f' {term} ':
        return True
    words, candidate_words = term.split(), candidate.split()
    if len(words) != len(candidate_words):
        return False
    differences = [(left, right) for left, right in zip(words, candidate_words) if left != right]
    return len(differences) == 1 and _is_single_letter_typo(*differences[0])


def suggest_matches(term, reference_terms, threshold, *, limit=3):
    if not term:
        return []
    matches = []
    for candidate, reference_id, name, source_url in reference_terms:
        if not _is_plausible_match(term, candidate):
            continue
        score = int(100 * SequenceMatcher(None, term, candidate, autojunk=False).ratio())
        if score >= threshold:
            matches.append((score, candidate, reference_id, name, source_url))

    suggestions = []
    seen = set()
    for score, candidate, reference_id, name, source_url in sorted(matches, key=lambda row: (-row[0], row[1])):
        if reference_id in seen:
            continue
        seen.add(reference_id)
        suggestions.append({
            'matched_term': candidate,
            'reference_name': name,
            'similarity_percent': score,
            'source_url': source_url,
        })
        if len(suggestions) == limit:
            break
    return suggestions
