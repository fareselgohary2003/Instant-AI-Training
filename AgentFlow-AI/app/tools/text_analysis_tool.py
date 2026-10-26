import re
from collections import Counter
from typing import Any

# Standard English stopwords for deterministic keyword extraction
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
}

POSITIVE_WORDS = {
    "great", "good", "excellent", "positive", "fortunate", "correct", "superior",
    "impressive", "best", "wonderful", "benefit", "success", "successful", "progress",
    "happy", "advantage", "growth", "high", "valuable", "effective", "clean", "reliable"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "poor", "negative", "unfortunate", "wrong", "inferior",
    "failure", "fail", "worse", "worst", "damage", "error", "defect", "flaw",
    "weak", "problem", "loss", "danger", "risky", "slow", "ineffective", "broken"
}

MAX_TEXT_LENGTH = 100_000  # 100KB limit for safety


def analyze_text(text: str, include_llm_summary: bool = False) -> dict[str, Any]:
    """Analyze text and return comprehensive deterministic statistics and keywords."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must not be empty.")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text exceeds maximum allowed length of {MAX_TEXT_LENGTH} characters.")

    cleaned_text = text.strip()

    # Extract words including hyphenated and apostrophe contractions
    words = re.findall(
        r"\b[\w]+(?:['’\-][\w]+)*\b",
        cleaned_text,
        flags=re.UNICODE,
    )

    # Extract sentences
    sentences = re.findall(
        r"[.!?]+(?=\s|$)",
        cleaned_text,
    )
    sentence_count = len(sentences) if sentences else (1 if words else 0)

    word_count = len(words)
    character_count = len(cleaned_text)

    # Average word length
    total_word_length = sum(len(w) for w in words)
    avg_word_length = round(total_word_length / word_count, 2) if word_count > 0 else 0.0

    # Deterministic keyword extraction (excluding stop words, min length 3)
    filtered_tokens = [
        w.lower() for w in words
        if len(w) > 2 and w.lower() not in STOPWORDS and not w.isnumeric()
    ]
    keyword_counts = Counter(filtered_tokens).most_common(5)
    keywords = [{"word": word, "frequency": count} for word, count in keyword_counts]

    # Deterministic sentiment analysis based on lexicon polarity
    pos_count = sum(1 for w in filtered_tokens if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in filtered_tokens if w in NEGATIVE_WORDS)

    if pos_count > neg_count:
        sentiment_label = "positive"
        score = round((pos_count - neg_count) / max(1, pos_count + neg_count), 2)
    elif neg_count > pos_count:
        sentiment_label = "negative"
        score = round((neg_count - pos_count) / max(1, pos_count + neg_count), 2)
    else:
        sentiment_label = "neutral"
        score = 0.0

    result: dict[str, Any] = {
        "word_count": word_count,
        "character_count": character_count,
        "sentence_count": sentence_count,
        "average_word_length": avg_word_length,
        "keywords": keywords,
        "deterministic_sentiment": {
            "label": sentiment_label,
            "polarity_score": score,
            "positive_terms": pos_count,
            "negative_terms": neg_count,
        },
    }

    if include_llm_summary and word_count > 30:
        try:
            from app.agent.llm import get_llm_response
            summary_prompt = [
                {"role": "system", "content": "Provide a concise 1-2 sentence executive summary of the provided text. Do not add commentary."},
                {"role": "user", "content": cleaned_text[:2000]},
            ]
            summary = get_llm_response(summary_prompt)
            result["llm_summary"] = summary.strip()
        except Exception:
            result["llm_summary"] = "LLM summarization was unavailable."

    return result
