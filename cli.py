#!/usr/bin/env python3
"""
Interactive CLI for Nitter Twitter Scraper
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

def track_user():
    """Track a Twitter user."""
    print_header("Track Twitter User")

    username = input(f"{Colors.CYAN}Enter username (without @): {Colors.END}").strip()
    if not username:
        print_error("Username cannot be empty!")
        return

    print(f"\n{Colors.YELLOW}Check intervals:{Colors.END}")
    print("1. Every 15 minutes (900 seconds)")
    print("2. Every 30 minutes (1800 seconds)")
    print("3. Every 1 hour (3600 seconds)")
    print("4. Every 6 hours (21600 seconds)")
    print("5. Custom interval")

    choice = input(f"\n{Colors.CYAN}Select interval [1-5]: {Colors.END}").strip()

    intervals = {
        "1": 900,
        "2": 1800,
        "3": 3600,
        "4": 21600
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

    print_info(f"Tracking @{username} with {interval} second interval...")

    try:
        response = requests.post(
            f"{API_BASE}/api/users/track",
            json={"username": username, "check_interval": interval},
            timeout=10
        )

        if response.status_code in [200, 201]:
            print_success(f"Started tracking @{username}")
            print_info("Scraping profile and timeline now...")
        else:
            print_error(f"Failed to track user: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_tracked_users():
    """View all tracked users."""
    print_header("Tracked Users")

    try:
        response = requests.get(f"{API_BASE}/api/users/tracked", timeout=10)

        if response.status_code == 200:
            users = response.json()

            if not users:
                print_info("No users being tracked yet.")
                return

            print(f"{'Username':<20} {'Followers':<12} {'Tweets':<10} {'Last Scraped'}")
            print("-" * 60)

            for user in users:
                last_scraped = user.get('last_scraped', 'Never')
                if last_scraped and last_scraped != 'Never':
                    last_scraped = last_scraped.split('T')[0]

                print(f"{user['username']:<20} {user['followers_count']:<12} {user['tweets_count']:<10} {last_scraped}")

            print(f"\n{Colors.GREEN}Total: {len(users)} users{Colors.END}")
        else:
            print_error(f"Failed to fetch users: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_tweets():
    """View scraped tweets."""
    print_header("View Tweets")

    print("1. View tweets from specific user")
    print("2. View all recent tweets")
    print("3. View tweets by sentiment")
    print("4. View tweets by hashtag")

    choice = input(f"\n{Colors.CYAN}Select option [1-4]: {Colors.END}").strip()

    try:
        if choice == "1":
            username = input(f"{Colors.CYAN}Enter username: {Colors.END}").strip()
            limit = input(f"{Colors.CYAN}Number of tweets [default: 10]: {Colors.END}").strip() or "10"

            response = requests.get(
                f"{API_BASE}/api/tweets/user/{username}",
                params={"limit": limit},
                timeout=10
            )

        elif choice == "2":
            limit = input(f"{Colors.CYAN}Number of tweets [default: 20]: {Colors.END}").strip() or "20"
            response = requests.get(
                f"{API_BASE}/api/tweets/",
                params={"limit": limit},
                timeout=10
            )

        elif choice == "3":
            print("\nSentiment types: positive, negative, neutral")
            sentiment = input(f"{Colors.CYAN}Enter sentiment: {Colors.END}").strip()

            response = requests.get(
                f"{API_BASE}/api/tweets/sentiment/{sentiment}",
                params={"limit": 20},
                timeout=10
            )

        elif choice == "4":
            hashtag = input(f"{Colors.CYAN}Enter hashtag (without #): {Colors.END}").strip()

            response = requests.get(
                f"{API_BASE}/api/tweets/hashtag/{hashtag}",
                timeout=10
            )

        else:
            print_error("Invalid choice!")
            return

        if response.status_code == 200:
            tweets = response.json()

            if not tweets:
                print_info("No tweets found.")
                return

            print(f"\n{Colors.GREEN}Found {len(tweets)} tweets:{Colors.END}\n")

            for i, tweet in enumerate(tweets, 1):
                username = tweet.get('username', 'Unknown')
                text = tweet.get('text', '')[:100]
                likes = tweet.get('likes_count', 0)
                retweets = tweet.get('retweets_count', 0)
                sentiment = tweet.get('sentiment', 'N/A')

                print(f"{Colors.BOLD}{i}. @{username}{Colors.END}")
                print(f"   {text}{'...' if len(tweet.get('text', '')) > 100 else ''}")
                print(f"   {Colors.YELLOW}❤ {likes}  🔄 {retweets}  😊 {sentiment}{Colors.END}")
                print()
        else:
            print_error(f"Failed to fetch tweets: {response.text}")

    except Exception as e:
        print_error(f"Error: {e}")

def search_tweets():
    """Search for tweets."""
    print_header("Search Tweets")

    query = input(f"{Colors.CYAN}Enter search query: {Colors.END}").strip()
    if not query:
        print_error("Query cannot be empty!")
        return

    print("\n1. Keyword search")
    print("2. Hashtag search")

    choice = input(f"\n{Colors.CYAN}Select type [1-2]: {Colors.END}").strip()

    search_type = "keyword" if choice == "1" else "hashtag"

    track = input(f"{Colors.CYAN}Track this search? [y/N]: {Colors.END}").strip().lower() == 'y'

    print_info(f"Searching for '{query}'...")

    try:
        response = requests.post(
            f"{API_BASE}/api/search/",
            json={
                "query": query,
                "search_type": search_type,
                "track": track,
                "check_interval": 3600
            },
            timeout=30
        )

        if response.status_code in [200, 201]:
            print_success(f"Search started for '{query}'")
            if track:
                print_info("Search will run every hour")
        else:
            print_error(f"Failed to search: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def view_jobs():
    """View scraping jobs."""
    print_header("Scraping Jobs")

    try:
        response = requests.get(f"{API_BASE}/api/jobs/stats/summary", timeout=10)

        if response.status_code == 200:
            stats = response.json()

            print(f"{Colors.BOLD}Job Statistics:{Colors.END}")
            print(f"  Total jobs: {stats['total_jobs']}")
            print(f"  {Colors.GREEN}✓ Completed: {stats['completed']}{Colors.END}")
            print(f"  {Colors.RED}✗ Failed: {stats['failed']}{Colors.END}")
            print(f"  {Colors.YELLOW}⟳ Running: {stats['running']}{Colors.END}")
            print(f"  {Colors.BLUE}⋯ Pending: {stats['pending']}{Colors.END}")
            print(f"  Success rate: {stats['success_rate']}%")
            print(f"  Items scraped: {stats['total_items_scraped']}")
            print(f"  Avg duration: {stats['avg_duration_seconds']:.2f}s")
        else:
            print_error(f"Failed to fetch jobs: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

def export_data():
    """Export scraped data."""
    print_header("Export Data")

    print("1. Export tweets to CSV")
    print("2. Export tweets to JSON")
    print("3. Export users to CSV")

    choice = input(f"\n{Colors.CYAN}Select option [1-3]: {Colors.END}").strip()

    if choice in ["1", "2"]:
        username = input(f"{Colors.CYAN}Username (leave empty for all): {Colors.END}").strip()
        limit = input(f"{Colors.CYAN}Limit [default: 1000]: {Colors.END}").strip() or "1000"

        format_type = "csv" if choice == "1" else "json"

        params = {"limit": limit}
        if username:
            params["username"] = username

        try:
            response = requests.get(
                f"{API_BASE}/api/export/tweets/{format_type}",
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                filename = f"tweets_{username or 'all'}.{format_type}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print_success(f"Exported to {filename}")
            else:
                print_error(f"Failed to export: {response.text}")
        except Exception as e:
            print_error(f"Error: {e}")

    elif choice == "3":
        try:
            response = requests.get(f"{API_BASE}/api/export/users/csv", timeout=30)

            if response.status_code == 200:
                filename = "users.csv"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print_success(f"Exported to {filename}")
            else:
                print_error(f"Failed to export: {response.text}")
        except Exception as e:
            print_error(f"Error: {e}")
    else:
        print_error("Invalid choice!")

def view_dashboard():
    """Open dashboard in browser."""
    print_header("Dashboard")
    print_info("Opening dashboard in browser...")
    print(f"\n{Colors.YELLOW}Dashboard URL: http://localhost:8000/dashboard{Colors.END}")
    print(f"{Colors.YELLOW}API Docs: http://localhost:8000/docs{Colors.END}\n")

def main_menu():
    """Display main menu."""
    print_header("Nitter Twitter Scraper - Interactive CLI")

    print(f"{Colors.BOLD}1.{Colors.END} Track a Twitter user")
    print(f"{Colors.BOLD}2.{Colors.END} View tracked users")
    print(f"{Colors.BOLD}3.{Colors.END} View scraped tweets")
    print(f"{Colors.BOLD}4.{Colors.END} Search for tweets")
    print(f"{Colors.BOLD}5.{Colors.END} View scraping jobs")
    print(f"{Colors.BOLD}6.{Colors.END} Export data")
    print(f"{Colors.BOLD}7.{Colors.END} View dashboard URLs")
    print(f"{Colors.BOLD}8.{Colors.END} Exit")

    choice = input(f"\n{Colors.CYAN}Select option [1-8]: {Colors.END}").strip()

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
                track_user()
            elif choice == "2":
                view_tracked_users()
            elif choice == "3":
                view_tweets()
            elif choice == "4":
                search_tweets()
            elif choice == "5":
                view_jobs()
            elif choice == "6":
                export_data()
            elif choice == "7":
                view_dashboard()
            elif choice == "8":
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
