#!/usr/bin/env python3
"""
Manual Session Test - Create session with correct format and test queries
"""

import sys
from datetime import datetime
import uuid

print("=" * 70)
print("MANUAL SESSION TEST")
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

# Check current sessions
print("\n2. Current sessions in database...")
try:
    sessions = db_handler.db.fetchall("SELECT * FROM sessions")
    print(f"   Total sessions: {len(sessions)}")

    if sessions:
        print("\n   Existing session timestamps:")
        for s in sessions[:3]:
            print(f"     - {s.get('created_at')}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Create a test session with EXACT correct format
print("\n3. Creating test session with correct ISO format...")
try:
    # Get user
    users = db_handler.db.fetchall("SELECT user_id, username FROM users LIMIT 1")
    if not users:
        print("   ✗ No users found! Create a user first.")
        sys.exit(1)

    user_id = users[0]['user_id']
    username = users[0]['username']
    print(f"   Using user: {username} ({user_id})")

    # Create session with ISO format
    session_id = f"test-{str(uuid.uuid4())}"
    now = datetime.now().isoformat()  # This is the key - must be ISO format

    print(f"   Creating session with timestamp: {now}")
    print(f"   Format check: ISO 8601? {bool('T' in now)}")

    # Insert
    db_handler.db.execute("""
        INSERT INTO sessions (session_id, user_id, created_at, updated_at, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (session_id, user_id, now, now))

    print(f"   ✓ Created session: {session_id[:20]}...")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test the queries immediately
print("\n4. Testing queries with new session...")

# Test 1: Count today
print("\n   A. Count distinct users today:")
try:
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    print(f"      Looking for sessions >= {today_start}")

    result = db_handler.db.fetchone(
        "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE created_at >= ?",
        (today_start,)
    )
    count = result['count'] if result else 0
    print(f"      Result: {count} users")

    if count > 0:
        print("      ✓ SUCCESS! Query found the session!")
    else:
        print("      ✗ FAILED! Query still returns 0")
        print("      This means there's a timestamp comparison issue")

        # Debug the comparison
        print("\n      Debugging timestamp comparison:")
        all_sessions = db_handler.db.fetchall(
            "SELECT session_id, created_at FROM sessions ORDER BY created_at DESC LIMIT 3"
        )
        for s in all_sessions:
            s_time = s['created_at']
            print(f"        Session: {s['session_id'][:20]}...")
            print(f"          created_at: {s_time}")
            print(f"          >= today?   {s_time >= today_start}")

except Exception as e:
    print(f"      ✗ Error: {e}")

# Test 2: Get active sessions
print("\n   B. Get active sessions with users:")
try:
    active = db_handler.db.fetchall("""
        SELECT s.*, u.username 
        FROM sessions s
        LEFT JOIN users u ON s.user_id = u.user_id
        WHERE s.status = 'active'
        ORDER BY s.updated_at DESC
        LIMIT 5
    """)
    print(f"      Result: {len(active)} active sessions")

    if active:
        print("      ✓ SUCCESS! Found active sessions:")
        for a in active[:3]:
            print(f"        - {a.get('username', 'N/A')}: {a.get('session_id', 'N/A')[:20]}...")
    else:
        print("      ✗ FAILED! No active sessions found")

except Exception as e:
    print(f"      ✗ Error: {e}")

# Test 3: Total users
print("\n   C. Count total users:")
try:
    result = db_handler.db.fetchone("SELECT COUNT(*) as count FROM users")
    count = result['count'] if result else 0
    print(f"      Result: {count} users")

    if count > 0:
        print("      ✓ SUCCESS!")
    else:
        print("      ✗ FAILED! No users found")

except Exception as e:
    print(f"      ✗ Error: {e}")

# Test monitoring service
print("\n5. Testing MonitoringService directly...")
try:
    from monitoring.monitoring_service import MonitoringService

    monitoring = MonitoringService()

    stats = monitoring.get_user_stats()

    print("   Results:")
    print(f"     - today: {stats.get('today')}")
    print(f"     - last_7_days: {stats.get('last_7_days')}")
    print(f"     - total: {stats.get('total')}")
    print(f"     - active_sessions: {len(stats.get('active_sessions', []))}")
    print(f"     - user_stats: {len(stats.get('user_stats', []))}")

    if stats.get('today') > 0:
        print("\n   ✓✓✓ SUCCESS! MonitoringService returns data!")
        print("   The backend is working correctly!")
        print("   If monitoring page still shows empty, it's a browser/JavaScript issue.")
    else:
        print("\n   ✗ MonitoringService still returns 0")
        print("   There's an issue with the time range calculation")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("\nIf you see SUCCESS messages above:")
print("  → Backend is working correctly")
print("  → Problem is in the browser (JavaScript/API)")
print("  → Check browser console (F12) for errors")
print("  → Verify /api/monitoring/users returns non-zero data")

print("\nIf you see FAILED messages:")
print("  → There's a timestamp format or comparison issue")
print("  → Share the output above for debugging")

print("\nNext steps:")
print("  1. If backend SUCCESS: Check browser console and BROWSER_DEBUG_GUIDE.md")
print("  2. If backend FAILED: Share this output")
print("  3. Check: curl http://localhost:5000/api/monitoring/users")

print("=" * 70)