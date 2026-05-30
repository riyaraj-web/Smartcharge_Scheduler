"""
Quick test script to verify the scheduler works.
"""

from scheduler import load_all_scenarios, ChargingScheduler

def test_scenario(scenario):
    print(f"\n{'='*60}")
    print(f"Testing: {scenario.name}")
    print(f"{'='*60}")
    print(f"Buses: {len(scenario.buses)}")
    print(f"Weights: individual={scenario.weights.individual}, operator={scenario.weights.operator}, overall={scenario.weights.overall}")
    
    scheduler = ChargingScheduler(time_limit_seconds=30)
    schedule = scheduler.build_schedule(scenario)
    
    print(f"\nResults:")
    print(f"  Total delay: {schedule.get_total_delay()} minutes")
    print(f"  Max individual delay: {schedule.get_max_individual_delay()} minutes")
    print(f"  Operator delays: {schedule.get_max_operator_delay()}")
    
    # Check for overlaps
    for station_id, events in schedule.station_schedules.items():
        for i in range(len(events) - 1):
            if events[i].end_time_min > events[i+1].start_time_min:
                print(f"  ⚠️ WARNING: Overlap at station {station_id}")
                return False
    
    print(f"  ✅ No overlaps detected")
    return True

if __name__ == "__main__":
    scenarios = load_all_scenarios("scenarios")
    print(f"Loaded {len(scenarios)} scenarios\n")
    
    for scenario in scenarios[:2]:  # Test first 2 scenarios
        success = test_scenario(scenario)
        if not success:
            print("Test failed!")
            break
    
    print("\n" + "="*60)
    print("Testing complete!")
