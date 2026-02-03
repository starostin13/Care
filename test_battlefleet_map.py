#!/usr/bin/env python3
"""
Test script for battlefleet map generation.
"""
import sys
import os

# Add CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Import the function we want to test
from mission_helper import generate_battlefleet_map, generate_new_one

def test_map_generation():
    """Test that map generation works correctly."""
    print("Testing battlefleet map generation...\n")
    
    # Generate 3 maps to see variety
    for i in range(3):
        print(f"=== Map #{i+1} ===")
        map_desc = generate_battlefleet_map()
        print(map_desc)
        print("\n")
    
    print("✅ Map generation test completed successfully!")

def test_mission_generation():
    """Test that mission generation includes map."""
    print("\nTesting battlefleet mission generation...\n")
    
    mission_tuple = generate_new_one("battlefleet")
    
    print(f"Mission tuple length: {len(mission_tuple)}")
    print(f"Deploy: {mission_tuple[0]}")
    print(f"Rules: {mission_tuple[1]}")
    print(f"Cell: {mission_tuple[2]}")
    print(f"Description: {mission_tuple[3]}")
    print(f"Winner bonus: {mission_tuple[4]}")
    
    if len(mission_tuple) > 5 and mission_tuple[5]:
        print(f"\nMap description:\n{mission_tuple[5]}")
        print("\n✅ Mission generation includes map description!")
    else:
        print("\n❌ Mission generation does NOT include map description!")
        return False
    
    return True

if __name__ == "__main__":
    test_map_generation()
    success = test_mission_generation()
    sys.exit(0 if success else 1)
