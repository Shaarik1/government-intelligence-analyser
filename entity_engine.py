import re

def extract_hard_facts(text):
    """
    Extracts Hard Data using Regex Patterns.
    Fast, Auditable, and works on any Python version.
    """
    
    # 1. EXTRACT MONEY
    # Looks for: $ followed by numbers, commas, dots, and words like 'million/billion'
    # Example matches: $50,000 | $10.5 million | $500k
    money_pattern = r"\$\s?\d+(?:,\d+)*(?:\.\d+)?(?:\s?(?:million|billion|trillion|k|m|b))?"
    money_matches = re.findall(money_pattern, text, re.IGNORECASE)
    
    # 2. EXTRACT LAWS / ACTS
    # Looks for: Capitalized Words followed by "Act" and a Year (4 digits)
    # Example matches: "Migration Act 1958", "Privacy Act 1988"
    law_pattern = r"(?i)([A-Z][a-z]+(?:\s[A-Z][a-z]+)*\sAct\s\d{4})"
    law_matches = re.findall(law_pattern, text)
    
    # 3. EXTRACT SECTIONS
    # Example matches: "Section 24", "Clause 12"
    section_pattern = r"(?i)(section\s\d+|clause\s\d+)"
    section_matches = re.findall(section_pattern, text)

    # 4. EXTRACT DATES
    # Looks for standard date formats: "24 January 2025", "Jan 24, 2025"
    date_pattern = r"(?i)\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{1,2},?\s\d{4}"
    date_matches = re.findall(date_pattern, text)

    return {
        "budget_mentions": list(set(money_matches)), # set() removes duplicates
        "legal_references": list(set(law_matches + section_matches)),
        "important_dates": list(set(date_matches))
    }

# Test it immediately
if __name__ == "__main__":
    test_text = """
    The Migration Act 1958 was updated on Jan 24, 2025.
    The total cost is $15.5 million allocated under Section 42.
    """
    print(extract_hard_facts(test_text))