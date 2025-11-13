#!/usr/bin/env python3
"""
Quick validation script to check if the system is properly set up.
Run this before deploying to ensure everything is configured correctly.
"""

import sys
import os

def check_files():
    """Check if all required files exist."""
    print("Checking files...")
    required_files = [
        'requirements.txt',
        'docker-compose.yml',
        '.env.example',
        'src/api/main.py',
        'src/scheduler/tasks.py',
        'src/nitter_manager/instance_manager.py',
        'src/scrapers/profile_scraper.py',
        'src/utils/models.py',
    ]

    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} MISSING")
            missing.append(file)

    return len(missing) == 0

def check_env():
    """Check if .env file exists."""
    print("\nChecking environment configuration...")
    if os.path.exists('.env'):
        print("  ✓ .env file exists")
        return True
    else:
        print("  ✗ .env file not found")
        print("  → Run: cp .env.example .env")
        return False

def check_docker():
    """Check if Docker is available."""
    print("\nChecking Docker...")
    result = os.system("docker --version > /dev/null 2>&1")
    if result == 0:
        print("  ✓ Docker is installed")

        result = os.system("docker-compose --version > /dev/null 2>&1")
        if result == 0:
            print("  ✓ Docker Compose is installed")
            return True
        else:
            print("  ✗ Docker Compose not found")
            return False
    else:
        print("  ✗ Docker not found")
        return False

def check_ports():
    """Check if required ports are available."""
    print("\nChecking ports...")
    import socket

    ports = {
        80: "HTTP (Nginx)",
        8000: "API (FastAPI)",
        5432: "PostgreSQL",
        6379: "Redis"
    }

    all_free = True
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        if result == 0:
            print(f"  ✗ Port {port} ({service}) is in use")
            all_free = False
        else:
            print(f"  ✓ Port {port} ({service}) is available")

    return all_free

def main():
    print("="*60)
    print("Nitter Scraper - System Validation")
    print("="*60)

    checks = {
        "Files": check_files(),
        "Environment": check_env(),
        "Docker": check_docker(),
        "Ports": check_ports()
    }

    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)

    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:20s} {status}")

    all_passed = all(checks.values())

    print("\n" + "="*60)
    if all_passed:
        print("✓ All checks passed! System is ready to deploy.")
        print("\nNext steps:")
        print("  1. Review and update .env file with your settings")
        print("  2. Run: ./run.sh")
        print("  3. Access dashboard at: http://localhost/dashboard")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
