#!/usr/bin/env python3
"""
Check Logs for Errors and Issues
"""

import json
import sys
import os
from datetime import datetime

def check_logs():
    """Check logs for errors and issues"""
    
    print("🔍 CHECKING LOGS FOR ERRORS")
    print("=" * 40)
    
    try:
        # Read the most recent log file
        with open('logs/processing.json', 'r') as f:
            lines = f.readlines()
        
        print(f"📊 Total log entries: {len(lines)}")
        
        # Parse recent logs
        recent_logs = []
        for line in lines[-1000:]:  # Check last 1000 entries
            if line.strip():
                try:
                    log = json.loads(line)
                    recent_logs.append(log)
                except json.JSONDecodeError:
                    continue
        
        print(f"📋 Parsed recent logs: {len(recent_logs)}")
        
        # Check for errors
        errors = [log for log in recent_logs if log.get('level') == 'ERROR']
        warnings = [log for log in recent_logs if log.get('level') == 'WARNING']
        
        print(f"\n🚨 ERRORS: {len(errors)}")
        if errors:
            print("Recent errors:")
            for error in errors[:5]:
                print(f"  - {error.get('message', 'No message')[:80]}...")
        else:
            print("  ✅ No errors found!")
        
        print(f"\n⚠️  WARNINGS: {len(warnings)}")
        if warnings:
            print("Recent warnings:")
            for warning in warnings[:5]:
                print(f"  - {warning.get('message', 'No message')[:80]}...")
        else:
            print("  ✅ No warnings found!")
        
        # Check for processing issues
        processing_issues = []
        for log in recent_logs:
            message = log.get('message', '').lower()
            if any(keyword in message for keyword in ['failed', 'timeout', 'exception', 'error', 'traceback']):
                processing_issues.append(log)
        
        print(f"\n🔧 PROCESSING ISSUES: {len(processing_issues)}")
        if processing_issues:
            print("Recent processing issues:")
            for issue in processing_issues[:5]:
                print(f"  - {issue.get('message', 'No message')[:80]}...")
        else:
            print("  ✅ No processing issues found!")
        
        # Check processing status distribution
        status_counts = {}
        for log in recent_logs:
            if 'processing_status' in log:
                status = log.get('processing_status')
                status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            print(f"\n📈 RECENT PROCESSING STATUS:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
        
        # Check for API rate limiting or quota issues
        api_issues = []
        for log in recent_logs:
            message = log.get('message', '').lower()
            if any(keyword in message for keyword in ['rate limit', 'quota', '429', 'too many requests']):
                api_issues.append(log)
        
        print(f"\n🌐 API ISSUES: {len(api_issues)}")
        if api_issues:
            print("Recent API issues:")
            for issue in api_issues[:3]:
                print(f"  - {issue.get('message', 'No message')[:80]}...")
        else:
            print("  ✅ No API issues found!")
        
        # Overall assessment
        print(f"\n📋 OVERALL ASSESSMENT:")
        if not errors and not warnings and not processing_issues and not api_issues:
            print("  ✅ All systems appear to be running smoothly!")
        else:
            print("  ⚠️  Some issues detected - review recommended")
        
    except FileNotFoundError:
        print("❌ Log file not found!")
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    check_logs() 