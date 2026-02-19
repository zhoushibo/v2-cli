# -*- coding: utf-8 -*-
"""
测试服务管理功能（简化版 - 无 emoji）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.gateway_service import GatewayService, KnowledgeBaseService

def test_gateway():
    print("=" * 80)
    print("TEST: Gateway Service")
    print("=" * 80)
    
    gateway = GatewayService()
    
    # Check status
    print("\n[1] Check current status:")
    status = gateway.get_status()
    print(f"    Name: {status['name']}")
    print(f"    Port: {status['port']}")
    print(f"    URL: {status['url']}")
    print(f"    Running: {'YES' if status['running'] else 'NO'}")
    
    # Test start
    if not status['running']:
        print("\n[2] Start service:")
        result = gateway.start()
        print(f"    Success: {result['success']}")
        print(f"    Message: {result['message']}")
        
        import time
        time.sleep(2)
        
        print("\n[3] Check after start:")
        print(f"    Running: {'YES' if gateway.is_running() else 'NO'}")
    else:
        print("\n[2] Service already running, skip start test")
    
    # Test stop
    if gateway.is_running():
        print("\n[4] Stop service:")
        result = gateway.stop()
        print(f"    Success: {result['success']}")
        print(f"    Message: {result['message']}")
        
        print("\n[5] Check after stop:")
        print(f"    Running: {'YES' if not gateway.is_running() else 'NO'}")
    else:
        print("\n[4] Service already stopped, skip stop test")
    
    print("\n" + "=" * 80)
    print("Gateway Service TEST COMPLETE")
    print("=" * 80)

def test_kb():
    print("\n" + "=" * 80)
    print("TEST: Knowledge Base Web UI")
    print("=" * 80)
    
    kb = KnowledgeBaseService()
    
    # Check status
    print("\n[1] Check current status:")
    status = kb.get_status()
    print(f"    Name: {status['name']}")
    print(f"    Port: {status['port']}")
    print(f"    URL: {status['url']}")
    print(f"    Running: {'YES' if status['running'] else 'NO'}")
    
    # Test start
    if not status['running']:
        print("\n[2] Start service:")
        result = kb.start()
        print(f"    Success: {result['success']}")
        print(f"    Message: {result['message']}")
        
        import time
        time.sleep(3)
        
        print("\n[3] Check after start:")
        print(f"    Running: {'YES' if kb.is_running() else 'NO'}")
    else:
        print("\n[2] Service already running, skip start test")
    
    # Test stop
    if kb.is_running():
        print("\n[4] Stop service:")
        result = kb.stop()
        print(f"    Success: {result['success']}")
        print(f"    Message: {result['message']}")
        
        print("\n[5] Check after stop:")
        print(f"    Running: {'YES' if not kb.is_running() else 'NO'}")
    else:
        print("\n[4] Service already stopped, skip stop test")
    
    print("\n" + "=" * 80)
    print("Knowledge Base Web UI TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SERVICE MANAGEMENT TEST SUITE")
    print("=" * 80 + "\n")
    
    test_gateway()
    print()
    test_kb()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Switch to 'Service Management' tab in GUI")
    print("  2. Click 'Start' buttons to test GUI control")
    print("  3. Visit http://localhost:8501 for Knowledge Base Web UI")
    print("  4. Continue P0 optimizations (UI beautification + Log viewer)")
    print()
