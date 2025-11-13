"""
Engagement rate calculation utilities.
"""

from typing import Dict
from loguru import logger


class EngagementCalculator:
    """Calculate engagement metrics for tweets."""

    @staticmethod
    def calculate_engagement_rate(
        likes: int,
        retweets: int,
        replies: int,
        quotes: int,
        followers: int
    ) -> float:
        """
        Calculate engagement rate as percentage.

        Formula: (Total Engagements / Followers) * 100

        Args:
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            quotes: Number of quotes
            followers: Follower count

        Returns:
            Engagement rate as percentage
        """
        if followers == 0:
            return 0.0

        total_engagements = likes + retweets + replies + quotes
        engagement_rate = (total_engagements / followers) * 100

        return round(engagement_rate, 2)

    @staticmethod
    def calculate_simple_engagement_rate(
        likes: int,
        retweets: int,
        replies: int,
        impressions: int = 0
    ) -> float:
        """
        Calculate engagement rate based on impressions.

        Args:
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            impressions: Number of impressions (if known)

        Returns:
            Engagement rate as percentage
        """
        if impressions == 0:
            return 0.0

        total_engagements = likes + retweets + replies
        engagement_rate = (total_engagements / impressions) * 100

        return round(engagement_rate, 2)

    @staticmethod
    def calculate_engagement_score(
        likes: int,
        retweets: int,
        replies: int,
        quotes: int,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate weighted engagement score.

        Args:
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            quotes: Number of quotes
            weights: Custom weights for each engagement type

        Returns:
            Weighted engagement score
        """
        # Default weights (can be customized)
        if weights is None:
            weights = {
                'like': 1.0,
                'retweet': 2.0,
                'reply': 3.0,
                'quote': 2.5
            }

        score = (
            likes * weights['like'] +
            retweets * weights['retweet'] +
            replies * weights['reply'] +
            quotes * weights['quote']
        )

        return round(score, 2)

    @staticmethod
    def calculate_virality_score(
        retweets: int,
        likes: int,
        followers: int
    ) -> float:
        """
        Calculate virality score (how much the tweet spread beyond followers).

        Args:
            retweets: Number of retweets
            likes: Number of likes
            followers: Follower count

        Returns:
            Virality score
        """
        if followers == 0:
            return 0.0

        # Weight retweets more heavily than likes for virality
        viral_score = ((retweets * 3) + likes) / followers

        return round(viral_score, 2)

    @staticmethod
    def get_engagement_metrics(tweet_data: Dict, followers: int = 0) -> Dict:
        """
        Calculate all engagement metrics for a tweet.

        Args:
            tweet_data: Dictionary with tweet engagement data
            followers: Follower count (optional)

        Returns:
            Dictionary with all calculated metrics
        """
        likes = tweet_data.get('likes_count', 0)
        retweets = tweet_data.get('retweets_count', 0)
        replies = tweet_data.get('replies_count', 0)
        quotes = tweet_data.get('quotes_count', 0)

        metrics = {
            'total_engagements': likes + retweets + replies + quotes,
            'engagement_score': EngagementCalculator.calculate_engagement_score(
                likes, retweets, replies, quotes
            ),
        }

        if followers > 0:
            metrics['engagement_rate'] = EngagementCalculator.calculate_engagement_rate(
                likes, retweets, replies, quotes, followers
            )
            metrics['virality_score'] = EngagementCalculator.calculate_virality_score(
                retweets, likes, followers
            )

        return metrics

    @staticmethod
    def classify_engagement_level(engagement_rate: float) -> str:
        """
        Classify engagement level based on rate.

        Args:
            engagement_rate: Engagement rate percentage

        Returns:
            Classification (low, medium, high, viral)
        """
        if engagement_rate < 1:
            return 'low'
        elif engagement_rate < 5:
            return 'medium'
        elif engagement_rate < 10:
            return 'high'
        else:
            return 'viral'

    @staticmethod
    def get_best_performing_tweets(tweets: list, metric: str = 'likes_count', limit: int = 10) -> list:
        """
        Get top performing tweets by a specific metric.

        Args:
            tweets: List of tweet dictionaries
            metric: Metric to sort by
            limit: Number of tweets to return

        Returns:
            List of top tweets
        """
        try:
            sorted_tweets = sorted(
                tweets,
                key=lambda t: t.get(metric, 0),
                reverse=True
            )
            return sorted_tweets[:limit]
        except Exception as e:
            logger.error(f"Error getting best performing tweets: {e}")
            return []
