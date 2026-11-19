"""Conservative English label splitter; preserves raw text and parsing warnings."""
import re
from html import unescape


def _is_water_mineral_profile(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not re.fullmatch(r'(?:eau de source|spring water|mineral water)(?: [\w -]+)?', lines[0], re.I):
        return False
    mineral_row = r'[^,;]+?\s+[<>≤]?\s*\d+(?:[.,]\d+)?\s*mg\s*/\s*l'
    ph_row = r'pH\s+\d+(?:[.,]\d+)?'
    return (
        sum(bool(re.fullmatch(mineral_row, line, re.I)) for line in lines[1:]) >= 2
        and all(re.fullmatch(f'(?:{mineral_row}|{ph_row})', line, re.I) for line in lines[1:])
    )


def parse_label(text):
    if not isinstance(text, str):
        raise ValueError('Ingredient label must be text.')
    raw = text
    text = unescape(text)
    if _is_water_mineral_profile(text):
        return {
            'original_label': raw,
            'candidates': [],
            'warnings': ['The product record contains water mineral measurements. Verify the package for an ingredient list.'],
        }
    text = re.sub(r'^\s*ingredients\s*:\s*', '', text, flags=re.I)
    # Allergen statements are not additional ingredient lists.
    text = re.split(r'\b(?:may contain|contains allergens|allergen information)\b', text, maxsplit=1, flags=re.I)[0]
    warnings = []
    stack = []
    for character in text:
        if character in '([':
            stack.append(character)
        elif character in ')]':
            if not stack or stack.pop() != ( '(' if character == ')' else '['):
                warnings.append('Unbalanced ingredient grouping; verify the original label.')
    if stack:
        warnings.append('Unbalanced ingredient grouping; verify the original label.')
    if re.search(r'\b(?:and/or|or|less than|contains?\s+\d|\d.*%)\b', text, re.I):
        warnings.append('Amounts or alternative ingredients require label review.')
    # A standalone purpose annotation is not a subingredient.
    text = re.sub(r'\(\s*for\s+colou?r\s*\)|\[\s*for\s+colou?r\s*\]', '', text, flags=re.I)
    text = re.sub(r'[\(\[]\s*source of [a-z][a-z -]*\s*[\)\]]', ',', text, flags=re.I)
    # Keep the specific sweetener name when the label identifies its stevia family.
    text = re.sub(r'\b(reb(?:audioside)?\s+m)\s*\(\s*stevia\s*\)', r'\1', text, flags=re.I)
    # Split conjunctions in explicitly introduced treatment lists only.
    text = re.sub(
        r'(?<=[(\[])\s*treated\s+with\s+([^()[\]]+)(?=[)\]])',
        lambda match: re.sub(r'\s+and\s+', ', ', match[1], flags=re.I),
        text,
        flags=re.I,
    )
    text = re.sub(r'(?<=[(\[])\s*with\s+', '', text, flags=re.I)
    # Keep compound names and their subingredients as separate candidates.
    candidates = []
    quantities = {}
    seen = set()
    upper_bound = None
    position = 0
    depth = 0
    previous = None
    for part in re.split(r'([,;()\[\]\n])', text):
        if part in ('(', '['):
            depth += 1
            continue
        if part in (')', ']'):
            depth = max(0, depth - 1)
            continue
        part = re.sub(r'\s+to\s+preserve\s+colou?r\s*\.?\s*$', '', part, flags=re.I)
        term = part.strip().strip(' .:').strip()
        if not term or term in (',', ';'):
            continue
        limit = re.match(r'contains?\s+(?:less than\s+)?(\d+(?:\.\d+)?)\s*%(?:\s+or less)?\s+of\b\s*:?', term, re.I)
        if depth == 0 and limit and float(limit[1]) <= 100:
            upper_bound = float(limit[1])
            term = term[limit.end():].strip()
        amount = re.fullmatch(r'(.*?)\s*([<≤]?)\s*(\d+(?:\.\d+)?)\s*(%|mg|g)(\s+per serving)?', term, re.I)
        disclosed = None
        if amount and (amount[4] == '%' or (amount[5] and not amount[2])):
            value = float(amount[3])
            if amount[4] != '%' or value <= 100:
                if not amount[1] and not amount[2] and depth == 1 and previous:
                    quantities[previous].update(status='disclosed', value=value, unit=amount[4].lower())
                    continue
                if amount[1]:
                    term = amount[1].strip()
                    disclosed = (
                        {'status': 'label_clue', 'upper_bound_percent': value}
                        if amount[2] and amount[4] == '%'
                        else {'status': 'disclosed', 'value': value, 'unit': amount[4].lower()}
                    )
        if not term:
            continue
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(term)
        quantity = {'status': 'unknown'}
        if depth == 0:
            position += 1
            quantity = {'status': 'label_clue', 'label_position': position}
            if upper_bound is not None:
                quantity['upper_bound_percent'] = upper_bound
        if disclosed:
            quantity.update(disclosed)
        quantities[term] = quantity
        previous = term if depth == 0 else None
    if not candidates:
        warnings.append('No ingredients available.')
    return {'original_label': raw, 'candidates': candidates, 'warnings': list(dict.fromkeys(warnings)),
            'quantities': quantities}
