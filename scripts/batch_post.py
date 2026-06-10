#!/usr/bin/env python3
"""
Batch runner: post N blogs to each platform with delays.
Usage: python3 scripts/batch_post.py [count_per_platform=5]
"""
import subprocess, sys, time

count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
script = "scripts/social_poster.py"

for i in range(count):
    print(f"\n{'='*50}")
    print(f"  BATCH {i+1}/{count}")
    print(f"{'='*50}")
    
    result = subprocess.run(
        ["python3", script, "--platform", "fb"],
        capture_output=True, text=True, timeout=45
    )
    print(result.stdout.strip())
    if result.stderr:
        print(f"ERR: {result.stderr.strip()[-200:]}")
    
    if i < count - 1:
        print(f"  ⏳ Waiting 30s...")
        time.sleep(30)

print(f"\n✅ FB batch done: {count} posts")

for i in range(count):
    print(f"\n{'='*50}")
    print(f"  BATCH {i+1}/{count}")
    print(f"{'='*50}")
    
    result = subprocess.run(
        ["python3", script, "--platform", "ig"],
        capture_output=True, text=True, timeout=90
    )
    print(result.stdout.strip())
    if result.stderr:
        print(f"ERR: {result.stderr.strip()[-200:]}")
    
    if i < count - 1:
        print(f"  ⏳ Waiting 30s...")
        time.sleep(30)

print(f"\n✅ IG batch done: {count} posts")
print("🎉 All done!")
