import re
import random
import string
from collections import Counter


# ============================================================
# BASIC TEXT HELPERS
# ============================================================

def _word_count(text: str) -> int:
    """Return the number of words in text."""
    return len(re.findall(r"\b[\w'-]+\b", text))


def _sentence_list(text: str) -> list[str]:
    """Split text into sentences."""
    if not text or not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def _summarize_stats(original: str, summary: str) -> dict:
    """Return statistics comparing original and summary."""
    original_words = _word_count(original)
    summary_words = _word_count(summary)

    original_sentences = len(_sentence_list(original))
    summary_sentences = len(_sentence_list(summary))

    original_chars = len(original)
    summary_chars = len(summary)

    if original_words > 0:
        reduction = ((original_words - summary_words) / original_words) * 100
    else:
        reduction = 0

    return {
        "original_words": original_words,
        "summary_words": summary_words,
        "reduction_percent": round(max(0, reduction), 1),
        "original_sentences": original_sentences,
        "summary_sentences": summary_sentences,
        "original_characters": original_chars,
        "summary_characters": summary_chars,
    }


# ============================================================
# TEXT SUMMARIZER
# ============================================================

def text_summarizer(text: str, sentence_count: int = 3) -> dict:
    """
    Simple extractive text summarizer.

    It selects important sentences based on word frequency.
    """

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    if sentence_count < 1:
        sentence_count = 1

    sentences = _sentence_list(text)

    if not sentences:
        return {
            "success": False,
            "error": "Could not find any sentences."
        }

    # Very short text does not need summarization
    if len(sentences) <= sentence_count:
        summary = " ".join(sentences)

        return {
            "success": True,
            "summary": summary,
            "stats": _summarize_stats(text, summary)
        }

    stop_words = {
        "the", "a", "an", "and", "or", "but", "if",
        "is", "are", "was", "were", "be", "been",
        "to", "of", "in", "on", "for", "with",
        "as", "by", "at", "from", "that", "this",
        "it", "its", "their", "they", "them",
        "he", "she", "his", "her", "we", "our",
        "you", "your", "i", "my", "me",
        "can", "could", "would", "should",
        "has", "have", "had",
        "will", "may", "might",
        "do", "does", "did"
    }

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    filtered_words = [
        word for word in words
        if word not in stop_words
    ]

    frequency = Counter(filtered_words)

    if not frequency:
        summary = " ".join(sentences[:sentence_count])

        return {
            "success": True,
            "summary": summary,
            "stats": _summarize_stats(text, summary)
        }

    # Normalize frequency scores
    max_frequency = max(frequency.values())

    word_scores = {
        word: count / max_frequency
        for word, count in frequency.items()
    }

    sentence_scores = []

    for index, sentence in enumerate(sentences):
        sentence_words = re.findall(
            r"\b[a-zA-Z]+\b",
            sentence.lower()
        )

        if not sentence_words:
            score = 0
        else:
            score = sum(
                word_scores.get(word, 0)
                for word in sentence_words
            )

            # Small bonus for important positions
            if index == 0:
                score *= 1.15

        sentence_scores.append((index, score))

    # Select highest scoring sentences
    best_sentences = sorted(
        sentence_scores,
        key=lambda item: item[1],
        reverse=True
    )[:sentence_count]

    # Restore original sentence order
    best_indexes = sorted(
        index for index, _ in best_sentences
    )

    summary = " ".join(
        sentences[index]
        for index in best_indexes
    )

    return {
        "success": True,
        "summary": summary,
        "stats": _summarize_stats(text, summary)
    }


# ============================================================
# TEXT ANALYZER
# ============================================================

def _special_symbol_stats(text: str) -> dict:
    """Count special characters."""
    symbols = re.findall(r"[^a-zA-Z0-9\s]", text)

    return {
        "special_characters": len(symbols),
        "unique_special_characters": len(set(symbols))
    }


def text_analyzer(text: str) -> dict:
    """Analyze basic text statistics."""

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = _sentence_list(text)
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    characters_without_spaces = len(
        re.sub(r"\s", "", text)
    )

    stats = _special_symbol_stats(text)

    return {
        "success": True,
        "words": len(words),
        "characters": len(text),
        "characters_without_spaces": characters_without_spaces,
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        **stats
    }


# ============================================================
# KEYWORD EXTRACTOR
# ============================================================

def _extract_keywords(text: str, count: int = 10) -> list[str]:
    """Extract keywords using simple word frequency."""

    if not text or not text.strip():
        return []

    stop_words = {
        "the", "a", "an", "and", "or", "but",
        "is", "are", "was", "were", "be", "been",
        "to", "of", "in", "on", "for", "with",
        "as", "by", "at", "from", "that", "this",
        "it", "its", "their", "they", "them",
        "he", "she", "his", "her",
        "we", "our", "you", "your",
        "i", "my", "me",
        "has", "have", "had",
        "will", "would", "could",
        "should", "can", "may",
        "do", "does", "did"
    }

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z'-]*\b",
        text.lower()
    )

    filtered = [
        word
        for word in words
        if word not in stop_words and len(word) > 2
    ]

    frequencies = Counter(filtered)

    return [
        word
        for word, _ in frequencies.most_common(count)
    ]


def keyword_extractor(text: str, count: int = 10) -> dict:
    """Return extracted keywords."""

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    keywords = _extract_keywords(text, count)

    return {
        "success": True,
        "keywords": keywords
    }


# ============================================================
# SENTIMENT ANALYZER
# ============================================================

def _analyze_sentiment(text: str) -> dict:
    """Simple rule-based sentiment analysis."""

    positive_words = {
        "good", "great", "excellent", "amazing",
        "happy", "love", "wonderful", "best",
        "success", "successful", "nice", "perfect",
        "helpful", "awesome", "fantastic"
    }

    negative_words = {
        "bad", "terrible", "awful", "sad",
        "hate", "worst", "poor", "failure",
        "failed", "problem", "wrong", "difficult",
        "angry", "horrible", "useless"
    }

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    positive_count = sum(
        1 for word in words
        if word in positive_words
    )

    negative_count = sum(
        1 for word in words
        if word in negative_words
    )

    if positive_count > negative_count:
        sentiment = "Positive"

    elif negative_count > positive_count:
        sentiment = "Negative"

    else:
        sentiment = "Neutral"

    return {
        "sentiment": sentiment,
        "positive_words": positive_count,
        "negative_words": negative_count
    }


def sentiment_analyzer(text: str) -> dict:
    """Analyze sentiment."""

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    return {
        "success": True,
        **_analyze_sentiment(text)
    }


def sentiment_keyword_analyzer(text: str, count: int = 10) -> dict:
    """Detect sentiment and extract keywords from the same text."""

    sentiment = sentiment_analyzer(text)
    if not sentiment.get("success"):
        return sentiment

    keywords = keyword_extractor(text, count)
    if not keywords.get("success"):
        return keywords

    return {
        "success": True,
        "sentiment": sentiment["sentiment"],
        "positive_words": sentiment["positive_words"],
        "negative_words": sentiment["negative_words"],
        "keywords": keywords["keywords"],
    }


# ============================================================
# PASSWORD GENERATOR
# ============================================================

def password_generator(
    length: int = 12,
    include_digits: bool = True,
    include_symbols: bool = True
) -> dict:
    """Generate a random password."""

    try:
        length = int(length)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Length must be a number."
        }

    if length < 4:
        return {
            "success": False,
            "error": "Password length must be at least 4."
        }

    characters = string.ascii_letters

    if include_digits:
        characters += string.digits

    if include_symbols:
        characters += string.punctuation

    password = "".join(
        random.choice(characters)
        for _ in range(length)
    )

    return {
        "success": True,
        "password": password,
        "length": length
    }


# ============================================================
# EMAIL VALIDATOR
# ============================================================

def email_validator(email: str) -> dict:
    """Validate an email address."""

    if not email or not email.strip():
        return {
            "success": False,
            "error": "Email is required."
        }

    email = email.strip()

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    valid = bool(
        re.match(pattern, email)
    )

    return {
        "success": True,
        "email": email,
        "valid": valid
    }


# ============================================================
# TEXT CASE CONVERTER
# ============================================================

def text_case_converter(
    text: str,
    case: str = "lower"
) -> dict:
    """Convert text to different cases."""

    if not text:
        return {
            "success": False,
            "error": "Text is required."
        }

    case = case.lower().strip()

    if case == "upper":
        result = text.upper()

    elif case == "lower":
        result = text.lower()

    elif case == "title":
        result = text.title()

    elif case == "capitalize":
        result = text.capitalize()

    elif case == "swap":
        result = text.swapcase()

    else:
        return {
            "success": False,
            "error": (
                "Invalid case. Use: "
                "upper, lower, title, capitalize, or swap."
            )
        }

    return {
        "success": True,
        "result": result,
        "case": case
    }


# ============================================================
# TEXT CLEANER
# ============================================================

def text_cleaner(text: str) -> dict:
    """Clean unnecessary spaces and duplicated punctuation."""

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    cleaned = text.strip()

    # Convert multiple spaces/tabs/newlines to one space
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Remove spaces before punctuation
    cleaned = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        cleaned
    )

    # Remove repeated punctuation
    cleaned = re.sub(
        r"([.!?]){2,}",
        r"\1",
        cleaned
    )

    return {
        "success": True,
        "original": text,
        "cleaned": cleaned
    }


# ============================================================
# SLUG GENERATOR
# ============================================================

def slug_generator(text: str) -> dict:
    """Convert text into a URL-friendly slug."""

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    slug = text.lower().strip()

    slug = re.sub(
        r"[^a-z0-9\s-]",
        "",
        slug
    )

    slug = re.sub(
        r"[\s-]+",
        "-",
        slug
    )

    slug = slug.strip("-")

    return {
        "success": True,
        "slug": slug
    }


# ============================================================
# RANDOM TEXT GENERATOR
# ============================================================

def random_text_generator(
    word_count: int = 50
) -> dict:
    """Generate random placeholder text."""

    try:
        word_count = int(word_count)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Word count must be a number."
        }

    if word_count < 1:
        return {
            "success": False,
            "error": "Word count must be greater than 0."
        }

    sample_words = [
        "technology", "software", "development",
        "python", "website", "application",
        "system", "data", "design", "project",
        "digital", "business", "solution",
        "modern", "simple", "powerful",
        "creative", "information", "platform",
        "service"
    ]

    words = [
        random.choice(sample_words)
        for _ in range(word_count)
    ]

    text = " ".join(words)

    return {
        "success": True,
        "text": text,
        "word_count": word_count
    }


# ============================================================
# AI LIKELIHOOD DETECTOR
# ============================================================

def detect_ai_likelihood(text: str) -> dict:
    """
    Estimate whether text contains patterns commonly associated
    with AI-generated writing.

    IMPORTANT:
    This is a heuristic estimate, not proof of AI authorship.
    """

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    sentences = _sentence_list(text)
    words = re.findall(
        r"\b[a-zA-Z]+\b",
        text.lower()
    )

    if not words:
        return {
            "success": False,
            "error": "No readable words found."
        }

    score = 0

    # --------------------------------------------------------
    # Common AI-style phrases
    # --------------------------------------------------------

    ai_phrases = [
        "in today's world",
        "in the modern world",
        "it is important to note",
        "it is worth noting",
        "plays a crucial role",
        "plays an important role",
        "in conclusion",
        "furthermore",
        "moreover",
        "additionally",
        "overall",
        "in summary",
        "as mentioned earlier",
        "it is essential to",
        "one of the key"
    ]

    lower_text = text.lower()

    phrase_matches = sum(
        1
        for phrase in ai_phrases
        if phrase in lower_text
    )

    score += min(
        phrase_matches * 7,
        35
    )

    # --------------------------------------------------------
    # Sentence length consistency
    # --------------------------------------------------------

    if sentences:
        sentence_lengths = [
            _word_count(sentence)
            for sentence in sentences
        ]

        average_length = sum(
            sentence_lengths
        ) / len(sentence_lengths)

        if 15 <= average_length <= 30:
            score += 10

        # Very similar sentence lengths
        if len(sentence_lengths) >= 4:
            max_length = max(sentence_lengths)
            min_length = min(sentence_lengths)

            if max_length - min_length <= 8:
                score += 10

    # --------------------------------------------------------
    # Repeated vocabulary
    # --------------------------------------------------------

    frequency = Counter(words)

    repeated_words = [
        word
        for word, count in frequency.items()
        if count >= 4 and len(word) > 4
    ]

    score += min(
        len(repeated_words) * 3,
        15
    )

    # --------------------------------------------------------
    # Formal transition words
    # --------------------------------------------------------

    formal_transitions = [
        "however",
        "therefore",
        "thus",
        "consequently",
        "furthermore",
        "moreover",
        "additionally"
    ]

    transition_count = sum(
        lower_text.count(word)
        for word in formal_transitions
    )

    score += min(
        transition_count * 3,
        15
    )

    score = min(
        max(score, 0),
        100
    )

    if score >= 60:
        likelihood = "High"

    elif score >= 30:
        likelihood = "Medium"

    else:
        likelihood = "Low"

    return {
        "success": True,
        "ai_likelihood": likelihood,
        "score": score,
        "note": (
            "This is a heuristic estimate and cannot reliably "
            "prove whether text was written by AI or a human."
        )
    }


# ============================================================
# TEXT HUMANIZER
# ============================================================

def humanize_text(text: str) -> dict:
    """
    Make text simpler and more natural using rule-based
    readability improvements.

    This does NOT guarantee that AI detectors will classify
    the text as human-written.
    """

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    result = text.strip()

    replacements = {
        r"\bin today's world\b": "today",
        r"\bin the modern world\b": "today",
        r"\bdue to the fact that\b": "because",
        r"\bin order to\b": "to",
        r"\bhas the ability to\b": "can",
        r"\bplays a crucial role in\b": "helps",
        r"\bplays an important role in\b": "helps",
        r"\ba large number of\b": "many",
        r"\bnumerous\b": "many",
        r"\bindividuals\b": "people",
        r"\bfacilitate\b": "help",
        r"\butilize\b": "use",
        r"\bapproximately\b": "about",
        r"\bcommence\b": "start",
        r"\bendeavor\b": "try",
        r"\bsubsequently\b": "later",
        r"\btherefore\b": "so",
        r"\bfurthermore\b": "also",
        r"\bmoreover\b": "also",
        r"\badditionally\b": "also",
        r"\bit is important to note that\b": "note that",
        r"\bit is worth noting that\b": "note that",
        r"\bit is essential to\b": "you should",
    }

    for pattern, replacement in replacements.items():
        result = re.sub(
            pattern,
            replacement,
            result,
            flags=re.IGNORECASE
        )

    # Clean whitespace
    result = re.sub(
        r"\s+",
        " ",
        result
    ).strip()

    # Remove unnecessary spaces before punctuation
    result = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        result
    )

    # Remove duplicated punctuation
    result = re.sub(
        r"([.!?]){2,}",
        r"\1",
        result
    )

    return {
        "success": True,
        "original": text,
        "humanized_text": result
    }


# ============================================================
# AI HUMANIZER + SUMMARIZER
# ============================================================

def human_summarizer(
    text: str,
    sentence_count: int = 3
) -> dict:
    """
    Complete AI Humanizer + Summarizer pipeline.

    Pipeline:
        1. Detect AI likelihood
        2. Humanize the text
        3. Summarize the humanized text
        4. Return statistics
    """

    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text is required."
        }

    # Step 1: AI likelihood
    ai_result = detect_ai_likelihood(text)
    if not ai_result.get("success"):
        return ai_result

    # Step 2: Humanize
    humanize_result = humanize_text(text)

    if not humanize_result["success"]:
        return humanize_result

    humanized_text = humanize_result["humanized_text"]

    # Step 3: Summarize
    summary_result = text_summarizer(
        humanized_text,
        sentence_count
    )

    if not summary_result["success"]:
        return summary_result

    summary = summary_result["summary"]

    # Step 4: Final statistics
    stats = _summarize_stats(
        text,
        summary
    )

    return {
        "success": True,

        "ai_likelihood": ai_result["ai_likelihood"],
        "ai_score": ai_result["score"],

        "humanized_text": humanized_text,

        "summary": summary,

        "stats": stats,

        "note": (
            "AI likelihood is an estimate based on writing patterns. "
            "It does not prove authorship."
        )
    }


# ============================================================
# AI TOOLS REGISTRY
# ============================================================

AI_TOOLS = {
    "text-summarizer": text_summarizer,

    "text-analyzer": text_analyzer,

    "keyword-extractor": sentiment_keyword_analyzer,

    "sentiment-analyzer": sentiment_keyword_analyzer,

    "password-generator": password_generator,

    "email-validator": email_validator,

    "text-case-converter": text_case_converter,

    "text-cleaner": text_cleaner,

    "slug-generator": slug_generator,

    "random-text-generator": random_text_generator,

    "ai-likelihood-detector": human_summarizer,

    "humanize-text": human_summarizer,

    "human-summarizer": human_summarizer,
}


# ============================================================
# OPTIONAL PROCESSOR
# ============================================================

def run_ai_tool(tool_name: str, **kwargs) -> dict:
    """
    Run a registered AI tool by its slug.

    Example:

        run_ai_tool(
            "text-summarizer",
            text="Long text...",
            sentence_count=3
        )
    """

    tool = AI_TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"Unknown AI tool: {tool_name}"
        }

    try:
        return tool(**kwargs)

    except TypeError as error:
        return {
            "success": False,
            "error": f"Invalid parameters: {error}"
        }

    except Exception as error:
        return {
            "success": False,
            "error": f"Tool execution failed: {error}"
        }