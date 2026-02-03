#!/usr/bin/env python3
"""
Standalone test for battlefleet map generation logic.
"""
import random

# Battlefleet Gothica celestial phenomena generators
BATTLEZONE_GENERATORS = {
    1: {  # Asteroid Field
        1: "Dense Asteroid Cluster - Ships moving through reduce speed by 2\"",
        2: "Asteroid Belt - Provides cover, enemies get -1 to hit",
        3: "Scattered Debris - No effect on movement",
        4: "Mining Operation - Abandoned structures provide partial cover",
        5: "Ice Field - Sensors reduced, -2\" to detection range",
        6: "Metallic Asteroids - Interferes with targeting systems"
    },
    2: {  # Nebula Zone
        1: "Gas Cloud - Reduces weapon range by 6\"",
        2: "Plasma Storm - Random energy discharges, roll for damage each turn",
        3: "Dust Cloud - All ships count as obscured",
        4: "Ion Nebula - Shields reduced by 1",
        5: "Radiation Field - Crew take 1 damage per turn inside",
        6: "Clear Zone - No effect"
    },
    3: {  # Gravity Wells
        1: "Massive Gravity Well - All movement reduced by 3\"",
        2: "Unstable Gravity - Random direction pull each turn",
        3: "Black Hole Proximity - Ships within 12\" pulled 2\" towards center",
        4: "Tidal Forces - Ships take 1 hull damage if moving at full speed",
        5: "Gravitational Anomaly - Unpredictable sensor readings",
        6: "Stable Orbit Zone - +1 to hit for ships not moving"
    },
    4: {  # Solar Phenomena
        1: "Solar Flare - All shields at -2 this turn",
        2: "Radiation Burst - Communications disrupted",
        3: "Electromagnetic Pulse - Ordnance weapons gain +1 strength",
        4: "Corona Discharge - Energy weapons reduced range by 6\"",
        5: "Stellar Wind - All ships pushed 3\" in random direction",
        6: "Magnetic Storm - Torpedoes may veer off course"
    },
    5: {  # Debris Field
        1: "Ship Wreckage - Provides full cover",
        2: "Battle Debris - Hazardous terrain, moving ships roll for damage",
        3: "Ancient Hulk - Can be used as cover or boarded",
        4: "Orbital Wreckage - Scattered debris, no effect",
        5: "Minefield Remnants - Roll D6 when entering, 5+ takes 1 damage",
        6: "Salvage Field - No combat effect"
    },
    6: {  # Planetary Bodies
        1: "Moon - Provides cover and gravity well",
        2: "Small Planet - Can use for slingshot maneuvers",
        3: "Gas Giant - Obscures sensors within 6\"",
        4: "Planetary Ring - Counts as asteroid field",
        5: "Barren Rock - Blocks line of sight",
        6: "Space Station - Neutral fortification"
    }
}


def generate_battlefleet_map():
    """Generate celestial phenomena map for Battlefleet Gothica missions.
    
    Based on Setting Up Celestial Phenomena: Method 2
    Divides table into 60cm square areas and generates phenomena.
    
    Returns:
        str: Formatted map description with celestial phenomena
    """
    # Standard table is typically 120cm x 180cm, giving us 2x3 = 6 areas of 60cm each
    # We'll use a simpler 2x3 grid (6 areas total)
    areas = []
    
    # First, determine which battlezone generator to use (D6 roll)
    generator_type = random.randint(1, 6)
    generator_name = {
        1: "Asteroid Field",
        2: "Nebula Zone", 
        3: "Gravity Wells",
        4: "Solar Phenomena",
        5: "Debris Field",
        6: "Planetary Bodies"
    }[generator_type]
    
    selected_generator = BATTLEZONE_GENERATORS[generator_type]
    
    # Check each area (6 total in 2x3 grid)
    area_labels = [
        "Top-Left", "Top-Center", "Top-Right",
        "Bottom-Left", "Bottom-Center", "Bottom-Right"
    ]
    
    for label in area_labels:
        # Roll D6 for each area - on 4+ it contains phenomena
        roll = random.randint(1, 6)
        if roll >= 4:
            # Generate phenomena from the selected generator
            phenomena_roll = random.randint(1, 6)
            phenomena = selected_generator[phenomena_roll]
            areas.append(f"  • {label}: {phenomena}")
        else:
            areas.append(f"  • {label}: Empty space")
    
    # Build the final map description
    map_desc = f"🗺️ BATTLEFLEET MAP - {generator_name.upper()}\n\n"
    map_desc += "Celestial Phenomena (60cm grid areas):\n"
    map_desc += "\n".join(areas)
    map_desc += "\n\n📋 Note: Position phenomena anywhere within each area, but don't overlap them."
    
    return map_desc


def main():
    print("Testing battlefleet map generation...\n")
    
    # Generate 5 maps to show variety
    for i in range(5):
        print(f"=== Map #{i+1} ===")
        map_desc = generate_battlefleet_map()
        print(map_desc)
        print("\n")
    
    print("✅ Map generation test completed successfully!")
    print("Each map randomly selects a battlezone type (1-6) and")
    print("generates phenomena for each 60cm area (on 4+ roll).")

if __name__ == "__main__":
    main()
