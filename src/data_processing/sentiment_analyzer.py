"""
Sentiment analysis for tweets using TextBlob.
"""

from textblob import TextBlob
from typing import Dict, Tuple
from loguru import logger


class SentimentAnalyzer:
    """Analyze sentiment of tweet text."""

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """
        Analyze sentiment of text using TextBlob.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment label and scores
        """
        if not text:
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0
            }

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Determine sentiment label
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity
            }

        except Exception as e:
            logger.debug(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0
            }

    @staticmethod
    def get_sentiment_label(polarity: float) -> str:
        """
        Convert polarity score to sentiment label.

        Args:
            polarity: Polarity score (-1 to 1)

        Returns:
            Sentiment label (positive, negative, neutral)
        """
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'

    @staticmethod
    def get_sentiment_strength(polarity: float) -> str:
        """
        Get sentiment strength description.

        Args:
            polarity: Polarity score (-1 to 1)

        Returns:
            Strength description
        """
        abs_polarity = abs(polarity)

        if abs_polarity >= 0.7:
            return 'very strong'
        elif abs_polarity >= 0.5:
            return 'strong'
        elif abs_polarity >= 0.3:
            return 'moderate'
        elif abs_polarity >= 0.1:
            return 'weak'
        else:
            return 'neutral'

    @staticmethod
    def analyze_sentiment_detailed(text: str) -> Dict:
        """
        Perform detailed sentiment analysis.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with detailed sentiment information
        """
        basic_sentiment = SentimentAnalyzer.analyze_sentiment(text)

        polarity = basic_sentiment['polarity']
        subjectivity = basic_sentiment['subjectivity']

        return {
            **basic_sentiment,
            'strength': SentimentAnalyzer.get_sentiment_strength(polarity),
            'is_objective': subjectivity < 0.5,
            'is_subjective': subjectivity >= 0.5,
            'is_very_positive': polarity > 0.5,
            'is_very_negative': polarity < -0.5,
        }

    @staticmethod
    def batch_analyze(texts: list) -> list:
        """
        Analyze sentiment for multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment dictionaries
        """
        results = []
        for text in texts:
            results.append(SentimentAnalyzer.analyze_sentiment(text))
        return results

    @staticmethod
    def get_average_sentiment(sentiments: list) -> Dict:
        """
        Calculate average sentiment from multiple sentiment analyses.

        Args:
            sentiments: List of sentiment dictionaries

        Returns:
            Dictionary with average sentiment
        """
        if not sentiments:
            return {
                'avg_polarity': 0.0,
                'avg_subjectivity': 0.0,
                'sentiment': 'neutral'
            }

        avg_polarity = sum(s.get('polarity', 0) for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s.get('subjectivity', 0) for s in sentiments) / len(sentiments)

        return {
            'avg_polarity': avg_polarity,
            'avg_subjectivity': avg_subjectivity,
            'sentiment': SentimentAnalyzer.get_sentiment_label(avg_polarity)
        }
