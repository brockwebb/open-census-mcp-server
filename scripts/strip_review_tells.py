"""Strip condition tells from expert review form.

Removes phrases that would reveal which condition (Control/RAG/Pragmatics)
produced each response, ensuring proper blinding for expert review.

Usage:
    python scripts/strip_review_tells.py
"""

import re
from pathlib import Path


def strip_tells(text: str) -> str:
    """Remove all condition tells from text."""

    # Remove entire disclaimer sentences that contain tells
    # Pattern: sentence that starts with disclaimer and contains tells
    disclaimer_patterns = [
        r'I appreciate your question[^.]+but I need to clarify something important:[^.]+Census methodology documentation[^.]+\.',
        r'Based on general knowledge,[^.]+Census methodology documentation[^.]+\.',
        r'I don\'t have[^.]+in Census methodology documentation[^.]+\.',
        r'I don\'t have[^.]+in my (available )?reference materials[^.]+\.',
        r'I don\'t have[^.]+in the provided reference materials[^.]+\.',
        r'[^.]+Census methodology documentation I have available[^.]+\.',
        r'[^.]+handbooks that explain[^.]+\.',
        r'[^.]+methodology documents and handbooks[^.]+\.',
    ]

    for pattern in disclaimer_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove specific tell phrases (case insensitive)
    tell_phrases = [
        'Census methodology documentation focuses on',
        'Census methodology documentation',
        'in Census methodology documentation',
        'Census methodology documentation I have available',
        'in my available reference materials',
        'in my reference materials',
        'my available reference materials',
        'reference materials',
        'methodology documentation',
        'the provided reference materials',
        'provided reference materials',
        'documents I have',
        'handbooks that explain',
        'methodology documents and handbooks',
        'in the provided reference',
        'according to the methodology',
        'the methodology documentation',
        'methodology handbooks',
    ]

    for phrase in tell_phrases:
        # Replace with empty string
        text = re.sub(re.escape(phrase), '', text, flags=re.IGNORECASE)

    # Clean up resulting formatting issues
    # Remove "These documents explain:" orphaned headers
    text = re.sub(r'These documents explain:\s*-', '-', text, flags=re.IGNORECASE)

    # Remove orphaned "However," at start of sentence
    text = re.sub(r'\.\s*However,\s*I can guide', '. I can guide', text)

    # Remove "Based on general knowledge," when it starts a sentence awkwardly
    text = re.sub(r'Based on general knowledge,\s*I do not have current',
                  'To find current', text, flags=re.IGNORECASE)
    text = re.sub(r'Based on general knowledge,\s*real-time or current',
                  'To find current', text, flags=re.IGNORECASE)

    # Remove doubled words from replacements
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)

    # Clean up extra whitespace - preserve newlines
    # First protect newlines by temporarily replacing them
    text = re.sub(r'\n', '<<<NEWLINE>>>', text)
    # Now collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    # Restore newlines
    text = re.sub(r'<<<NEWLINE>>>', '\n', text)
    # Clean up multiple newlines to at most double
    text = re.sub(r'\n\n\n+', '\n\n', text)

    # Fix sentences that start with lowercase after a period
    text = re.sub(r'\.\s+([a-z])', lambda m: '. ' + m.group(1).upper(), text)

    return text.strip()


def main():
    form_path = Path('talks/fcsm_2026/expert_review_form.md')

    print("="*70)
    print("STRIPPING CONDITION TELLS FROM EXPERT REVIEW FORM")
    print("="*70)

    # Read file
    print(f"\nReading {form_path}...")
    with open(form_path) as f:
        content = f.read()

    # Strip tells
    print("Stripping tells...")
    cleaned = strip_tells(content)

    # Write back
    print(f"Writing cleaned content to {form_path}...")
    with open(form_path, 'w') as f:
        f.write(cleaned)

    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    # Check for remaining tells
    tell_check_patterns = [
        'reference material',
        'methodology documentation',
        'documents I have',
        'handbooks',
        'reference.*available',
        'Census methodology',
        'provided reference',
        'my available'
    ]

    print("\nChecking for remaining tells...")
    found_tells = []

    for pattern in tell_check_patterns:
        matches = list(re.finditer(pattern, cleaned, re.IGNORECASE))
        if matches:
            found_tells.append((pattern, len(matches)))
            for match in matches[:2]:  # Show first 2
                context_start = max(0, match.start() - 50)
                context_end = min(len(cleaned), match.end() + 50)
                context = cleaned[context_start:context_end]
                print(f"  ⚠️  Found '{pattern}': ...{context}...")

    if not found_tells:
        print("  ✅ No tells found!")
    else:
        print(f"\n  ❌ Found {len(found_tells)} types of tells still present")
        for pattern, count in found_tells:
            print(f"     - {pattern}: {count} matches")

    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Manually read Q1, Q5, Q10, Q15, Q20 to verify no tells remain")
    print("2. Verify responses are still coherent and substantive")
    print("3. If any tells remain, manually edit the file to remove them")


if __name__ == '__main__':
    main()
