#!/usr/bin/env python3
"""
Advanced Diagnostic - Sessions exist but monitoring shows empty
Run this to find out exactly what's wrong
"""

import sys
from datetime import datetime, timedelta
import json

print("=" * 70)
print("ADVANCED DIAGNOSTIC - Sessions Exist But Cards Empty")
print("=" * 70)

# Import database handler
print("\n1. Importing database handler...")
try:
    from db.database_call_handler import get_database_handler

    db_handler = get_database_handler()
    print("   ✓ Database handler loaded")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Check sessions exist
print("\n2. Checking sessions table...")
try:
    sessions = db_handler.db.fetchall("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 5")
    print(f"   Found {len(sessions)} sessions")

    if sessions:
        print("\n   Recent sessions:")
        for session in sessions:
            print(f"     - Session ID: {session.get('session_id', 'N/A')[:8]}...")
            print(f"       User ID: {session.get('user_id', 'N/A')}")
            print(f"       Created: {session.get('created_at', 'N/A')}")
            print(f"       Updated: {session.get('updated_at', 'N/A')}")
            print(f"       Status: {session.get('status', 'N/A')}")
            print()
    else:
        print("   ✗ No sessions found!")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Check what monitoring methods return
print("\n3. Testing monitoring methods...")

# Test count_distinct_users_in_sessions
print("\n   A. Testing count_distinct_users_in_sessions()...")
try:
    # Get today's timestamp
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_iso = today.isoformat()

    print(f"      Looking for sessions since: {today_iso}")

    # Test the actual query
    result = db_handler.db.fetchone(
        "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE created_at >= ?",
        (today_iso,)
    )
    count = result['count'] if result else 0
    print(f"      Result: {count} users")

    if count == 0:
        print("      ⚠ Query returned 0! Let's investigate...")

        # Check all sessions
        all_sessions = db_handler.db.fetchall("SELECT created_at FROM sessions")
        print(f"      Total sessions in table: {len(all_sessions)}")

        if all_sessions:
            print("      Session created_at values:")
            for s in all_sessions[:5]:
                print(f"        - {s.get('created_at', 'N/A')}")

            # Try comparing the timestamps
            print(f"\n      Comparing timestamps:")
            print(f"        Query looking for >= {today_iso}")
            print(f"        Session created_at:     {all_sessions[0].get('created_at', 'N/A')}")

            # Check if it's a format issue
            session_time = all_sessions[0].get('created_at')
            print(f"\n      Attempting to parse session timestamp...")
            try:
                parsed = datetime.fromisoformat(session_time.replace('Z', '+00:00'))
                print(f"        Parsed successfully: {parsed}")
                print(f"        Today cutoff:        {today}")
                print(f"        Is session >= today? {parsed >= today}")
            except Exception as e:
                print(f"        ✗ Parse failed: {e}")

except Exception as e:
    print(f"      ✗ Error: {e}")
    import traceback

    traceback.print_exc()

# Test count_total_users
print("\n   B. Testing count_total_users()...")
try:
    total = db_handler.count_total_users()
    print(f"      Result: {total} users")
except Exception as e:
    print(f"      ✗ Error: {e}")

# Test get_active_sessions_with_users
print("\n   C. Testing get_active_sessions_with_users()...")
try:
    active = db_handler.get_active_sessions_with_users(limit=5)
    print(f"      Result: {len(active)} active sessions")

    if len(active) == 0:
        print("      ⚠ No active sessions found!")

        # Check session statuses
        statuses = db_handler.db.fetchall("SELECT status, COUNT(*) as count FROM sessions GROUP BY status")
        print("      Session status breakdown:")
        for status in statuses:
            print(f"        - {status['status']}: {status['count']}")
    else:
        print("      Active sessions:")
        for s in active[:3]:
            print(f"        - {s}")
except Exception as e:
    print(f"      ✗ Error: {e}")

# Test the monitoring service directly
print("\n4. Testing MonitoringService.get_user_stats()...")
try:
    from monitoring.monitoring_service import MonitoringService

    monitoring = MonitoringService()

    stats = monitoring.get_user_stats()

    print("   Results from get_user_stats():")
    print(f"     - today: {stats.get('today')}")
    print(f"     - last_7_days: {stats.get('last_7_days')}")
    print(f"     - total: {stats.get('total')}")
    print(f"     - hourly_data points: {len(stats.get('hourly_data', []))}")
    print(f"     - active_sessions: {len(stats.get('active_sessions', []))}")
    print(f"     - user_stats: {len(stats.get('user_stats', []))}")

    if stats.get('today') == 0:
        print("\n   ⚠ 'today' is still 0! Let's check the time ranges...")
        times = monitoring.get_time_ranges()
        print(f"     Time ranges used:")
        print(f"       - today: {times.get('today')}")
        print(f"       - week_ago: {times.get('week_ago')}")
        print(f"       - hour_ago: {times.get('hour_ago')}")

        # Manually test the query with the exact time range
        today_time = times.get('today')
        print(f"\n     Testing query with today time: {today_time}")
        test_result = db_handler.db.fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE created_at >= ?",
            (today_time,)
        )
        print(f"     Query result: {test_result}")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback

    traceback.print_exc()

# Test the API endpoint
print("\n5. Testing API endpoint /api/monitoring/users...")
try:
    # Try to import Flask app
    try:
        from app import app
    except:
        try:
            from main import app
        except:
            print("   ⚠ Could not import Flask app, skipping API test")
            app = None

    if app:
        with app.test_client() as client:
            response = client.get('/api/monitoring/users')
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()
                print(f"   Response data:")
                print(json.dumps(data, indent=2, default=str))
            else:
                print(f"   Error response: {response.get_data(as_text=True)}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check browser console
print("\n6. Browser-side checks...")
print("   Please check the following in your browser:")
print("   1. Open /monitoring/users")
print("   2. Press F12 to open Developer Tools")
print("   3. Go to Console tab - any JavaScript errors?")
print("   4. Go to Network tab")
print("   5. Refresh the page")
print("   6. Click on the /api/monitoring/users request")
print("   7. Check the Response - what does it show?")
print()
print("   Common issues:")
print("   - Response shows all zeros? API is working but query/date issue")
print("   - Response shows 'null' or error? API is crashing")
print("   - No /api/monitoring/users request? JavaScript isn't running")
print("   - Request is red/failed? API endpoint not found")

# Summary
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)

print("\nQuick checklist:")
sessions_exist = len(db_handler.db.fetchall("SELECT * FROM sessions")) > 0
print(f"  [{'✓' if sessions_exist else '✗'}] Sessions exist in database")

try:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_count = db_handler.db.fetchone(
        "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE created_at >= ?",
        (today,)
    )['count']
    print(f"  [{'✓' if today_count > 0 else '✗'}] Query for today's sessions returns: {today_count}")
except:
    print(f"  [✗] Query for today's sessions failed")

print("\n" + "=" * 70)
print("\nNext steps:")
print("1. Check the output above for any ✗ marks")
print("2. Look for timestamp format issues")
print("3. Check browser console (F12) for errors")
print("4. Share this output if you need more help")
print("=" * 70)