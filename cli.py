#!/usr/bin/env python3
"""
Interactive CLI for Twitter Community Scraper
"""

import requests
import json
import sys
from typing import Optional

API_BASE = "http://localhost:8000"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_api():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def scrape_community():
    """Scrape a Twitter community."""
    print_header("Scrape Twitter Community")

    print(f"{Colors.YELLOW}How to find Community ID:{Colors.END}")
    print("1. Go to the community on Twitter")
    print("2. URL looks like: twitter.com/i/communities/1234567890")
    print("3. The number at the end is the Community ID\n")

    community_id = input(f"{Colors.CYAN}Enter Community ID: {Colors.END}").strip()
    if not community_id:
        print_error("Community ID cannot be empty!")
        return

    print(f"\n{Colors.YELLOW}How many tweets to scrape?{Colors.END}")
    print("1. 100 tweets (fast)")
    print("2. 500 tweets")
    print("3. 1000 tweets")
    print("4. ALL tweets (may take a while)")
    print("5. Custom amount")

    choice = input(f"\n{Colors.CYAN}Select option [1-5]: {Colors.END}").strip()

    tweet_amounts = {
        "1": 100,
        "2": 500,
        "3": 1000,
        "4": None  # None = ALL tweets
    }

    if choice in tweet_amounts:
        max_tweets = tweet_amounts[choice]
    elif choice == "5":
        try:
            max_tweets = int(input(f"{Colors.CYAN}Enter number of tweets: {Colors.END}"))
        except ValueError:
            print_error("Invalid number!")
            return
    else:
        print_error("Invalid choice!")
        return

    if max_tweets is None:
        print_info(f"Scraping ALL tweets from community {community_id}...")
        print_info("This may take several minutes depending on community size...")
    else:
        print_info(f"Scraping {max_tweets} tweets from community {community_id}...")

    try:
        params = {}
        if max_tweets is not None:
            params['max_tweets'] = max_tweets

        response = requests.post(
            f"{API_BASE}/api/communities/{community_id}/scrape",
            params=params,
            timeout=600  # 10 minute timeout for large scrapes
        )

        if response.status_code in [200, 201]:
            data = response.json()
            tweets_scraped = data.get('tweets_scraped', 0)
            print_success(f"Successfully scraped {tweets_scraped} tweets!")
            print_info(f"Community ID: {community_id}")
            print_info("Use 'Export Data' to download the tweets")
        else:
            print_error(f"Failed to scrape: {response.text}")
    except requests.exceptions.Timeout:
        print_error("Request timed out. The scraping might still be running in the background.")
        print_info("Check 'View scraped tweets' to see if tweets were collected")
    except Exception as e:
        print_error(f"Error: {e}")

def track_community():
    """Track a community for automatic scraping."""
    print_header("Track Twitter Community")

    print(f"{Colors.YELLOW}How to find Community ID:{Colors.END}")
    print("1. Go to the community on Twitter")
    print("2. URL looks like: twitter.com/i/communities/1234567890")
    print("3. The number at the end is the Community ID\n")

    community_id = input(f"{Colors.CYAN}Enter Community ID: {Colors.END}").strip()
    if not community_id:
        print_error("Community ID cannot be empty!")
        return

    print(f"\n{Colors.YELLOW}Check intervals:{Colors.END}")
    print("1. Every 30 minutes (1800 seconds)")
    print("2. Every 1 hour (3600 seconds)")
    print("3. Every 6 hours (21600 seconds)")
    print("4. Every 24 hours (86400 seconds)")
    print("5. Custom interval")

    choice = input(f"\n{Colors.CYAN}Select interval [1-5]: {Colors.END}").strip()

    intervals = {
        "1": 1800,
        "2": 3600,
        "3": 21600,
        "4": 86400
    }

    if choice in intervals:
        interval = intervals[choice]
    elif choice == "5":
        try:
            interval = int(input(f"{Colors.CYAN}Enter interval in seconds: {Colors.END}"))
        except ValueError:
            print_error("Invalid interval!")
            return
    else:
        print_error("Invalid choice!")
        return

    print_info(f"Tracking community {community_id} with {interval} second interval...")

    try:
        response = requests.post(
            f"{API_BASE}/api/communities/{community_id}/track",
            params={"check_interval": interval},
            timeout=10
        )

        if response.status_code in [200, 201]:
            print_success(f"Started tracking community {community_id}")
            print_info(f"Will scrape every {interval} seconds ({interval//3600} hours)")
        else:
            print_error(f"Failed to track community: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_tracked_communities():
    """View all tracked communities."""
    print_header("Tracked Communities")

    try:
        response = requests.get(f"{API_BASE}/api/communities/", timeout=10)

        if response.status_code == 200:
            data = response.json()
            communities = data.get('communities', [])

            if not communities:
                print_info("No communities being tracked yet.")
                print_info("Use 'Track a community' to start tracking")
                return

            print(f"{'Community ID':<20} {'Name':<30} {'Members':<12} {'Last Scraped'}")
            print("-" * 80)

            for community in communities:
                last_scraped = community.get('last_scraped', 'Never')
                if last_scraped and last_scraped != 'Never':
                    last_scraped = last_scraped.split('T')[0]

                print(f"{community['community_id']:<20} {community.get('name', 'N/A'):<30} {community.get('member_count', 0):<12} {last_scraped}")

            print(f"\n{Colors.GREEN}Total: {len(communities)} communities{Colors.END}")
        else:
            print_error(f"Failed to fetch communities: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_community_tweets():
    """View tweets from a community."""
    print_header("View Community Tweets")

    community_id = input(f"{Colors.CYAN}Enter Community ID: {Colors.END}").strip()
    if not community_id:
        print_error("Community ID cannot be empty!")
        return

    limit = input(f"{Colors.CYAN}Number of tweets to show [default: 20]: {Colors.END}").strip() or "20"

    try:
        response = requests.get(
            f"{API_BASE}/api/communities/{community_id}/tweets",
            params={"limit": limit},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            tweets = data.get('tweets', [])

            if not tweets:
                print_info("No tweets found for this community.")
                print_info("Try scraping the community first")
                return

            print(f"\n{Colors.GREEN}Found {len(tweets)} tweets:{Colors.END}\n")

            for i, tweet in enumerate(tweets, 1):
                username = tweet.get('username', 'Unknown')
                text = tweet.get('text', '')[:100]
                likes = tweet.get('likes_count', 0)
                retweets = tweet.get('retweets_count', 0)
                replies = tweet.get('replies_count', 0)

                print(f"{Colors.BOLD}{i}. @{username}{Colors.END}")
                print(f"   {text}{'...' if len(tweet.get('text', '')) > 100 else ''}")
                print(f"   {Colors.YELLOW}❤ {likes}  🔄 {retweets}  💬 {replies}{Colors.END}")
                if tweet.get('tweet_url'):
                    print(f"   {Colors.BLUE}🔗 {tweet['tweet_url']}{Colors.END}")
                print()
        else:
            print_error(f"Failed to fetch tweets: {response.text}")

    except Exception as e:
        print_error(f"Error: {e}")

def export_community_data():
    """Export community tweets."""
    print_header("Export Community Data")

    community_id = input(f"{Colors.CYAN}Enter Community ID: {Colors.END}").strip()
    if not community_id:
        print_error("Community ID cannot be empty!")
        return

    print("\n1. Export to CSV (Excel-friendly)")
    print("2. Export to JSON (all fields)")

    choice = input(f"\n{Colors.CYAN}Select format [1-2]: {Colors.END}").strip()

    limit = input(f"{Colors.CYAN}Limit (max tweets) [default: 10000]: {Colors.END}").strip() or "10000"

    format_type = "csv" if choice == "1" else "json"

    try:
        response = requests.get(
            f"{API_BASE}/api/export/community/{format_type}",
            params={"community_id": community_id, "limit": limit},
            timeout=60
        )

        if response.status_code == 200:
            filename = f"community_{community_id}.{format_type}"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print_success(f"Exported to {filename}")

            if format_type == "csv":
                print_info("CSV fields: username, content, likes, retweets, comments, post_link, posted_at")
        else:
            print_error(f"Failed to export: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_dashboard():
    """Show API documentation URL."""
    print_header("API Documentation")
    print(f"\n{Colors.YELLOW}API Docs: http://localhost:8000/docs{Colors.END}")
    print(f"{Colors.YELLOW}ReDoc: http://localhost:8000/redoc{Colors.END}\n")
    print_info("Open these URLs in your browser to see all API endpoints")

def main_menu():
    """Display main menu."""
    print_header("Twitter Community Scraper - CLI")

    print(f"{Colors.BOLD}1.{Colors.END} Scrape a community (one-time)")
    print(f"{Colors.BOLD}2.{Colors.END} Track a community (automatic periodic scraping)")
    print(f"{Colors.BOLD}3.{Colors.END} View tracked communities")
    print(f"{Colors.BOLD}4.{Colors.END} View community tweets")
    print(f"{Colors.BOLD}5.{Colors.END} Export community data")
    print(f"{Colors.BOLD}6.{Colors.END} View API docs")
    print(f"{Colors.BOLD}7.{Colors.END} Exit")

    choice = input(f"\n{Colors.CYAN}Select option [1-7]: {Colors.END}").strip()

    return choice

def main():
    """Main CLI loop."""
    # Check if API is running
    if not check_api():
        print_error("API is not running!")
        print_info("Start with: docker compose up -d")
        sys.exit(1)

    print_success("Connected to API")

    while True:
        try:
            choice = main_menu()

            if choice == "1":
                scrape_community()
            elif choice == "2":
                track_community()
            elif choice == "3":
                view_tracked_communities()
            elif choice == "4":
                view_community_tweets()
            elif choice == "5":
                export_community_data()
            elif choice == "6":
                view_dashboard()
            elif choice == "7":
                print_info("Goodbye!")
                break
            else:
                print_error("Invalid choice!")

            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted. Exiting...{Colors.END}")
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
