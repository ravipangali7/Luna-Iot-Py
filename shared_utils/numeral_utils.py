"""
Utility functions for normalizing between Nepali (Devanagari) and English numerals.
Enables bidirectional search functionality.
"""

# Numeral mapping: English -> Nepali
ENGLISH_TO_NEPALI = {
    '0': '०',
    '1': '१',
    '2': '२',
    '3': '३',
    '4': '४',
    '5': '५',
    '6': '६',
    '7': '७',
    '8': '८',
    '9': '९',
}

# Numeral mapping: Nepali -> English
NEPALI_TO_ENGLISH = {v: k for k, v in ENGLISH_TO_NEPALI.items()}


def normalize_to_english(text: str) -> str:
    """
    Convert Nepali numerals to English numerals in the given text.
    
    Args:
        text: Input string that may contain Nepali numerals
        
    Returns:
        String with Nepali numerals converted to English numerals
        
    Example:
        normalize_to_english("६७८९") -> "6789"
    """
    if not text:
        return text
    
    result = []
    for char in text:
        result.append(NEPALI_TO_ENGLISH.get(char, char))
    return ''.join(result)


def normalize_to_nepali(text: str) -> str:
    """
    Convert English numerals to Nepali numerals in the given text.
    
    Args:
        text: Input string that may contain English numerals
        
    Returns:
        String with English numerals converted to Nepali numerals
        
    Example:
        normalize_to_nepali("6789") -> "६७८९"
    """
    if not text:
        return text
    
    result = []
    for char in text:
        result.append(ENGLISH_TO_NEPALI.get(char, char))
    return ''.join(result)


def normalize_numerals_bidirectional(text: str) -> tuple[str, str]:
    """
    Generate both English and Nepali normalized versions of the input text.
    This enables bidirectional search - searching with either numeral system
    will find matches regardless of which system is used in stored data.
    
    Args:
        text: Input string that may contain numerals in either system
        
    Returns:
        Tuple of (english_normalized, nepali_normalized) versions
        
    Example:
        normalize_numerals_bidirectional("6789") -> ("6789", "६७८९")
        normalize_numerals_bidirectional("६७८९") -> ("6789", "६७८९")
    """
    if not text:
        return text, text
    
    english_version = normalize_to_english(text)
    nepali_version = normalize_to_nepali(text)
    
    return english_version, nepali_version


def get_search_variants(text: str) -> list[str]:
    """
    Get all search variants for a given text (original, English normalized, Nepali normalized).
    Useful for building search queries that match regardless of numeral system used.
    
    Args:
        text: Input search query
        
    Returns:
        List of search variants (original, english, nepali)
        
    Example:
        get_search_variants("6789") -> ["6789", "6789", "६७८९"]
        get_search_variants("६७८९") -> ["६७८९", "6789", "६७८९"]
    """
    if not text:
        return [text]
    
    english_version, nepali_version = normalize_numerals_bidirectional(text)
    
    # Return unique variants
    variants = {text, english_version, nepali_version}
    return list(variants)

