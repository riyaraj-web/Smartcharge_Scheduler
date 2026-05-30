"""
Project verification script.
Checks that all components are working correctly before deployment.
"""

import sys
from pathlib import Path

def check_files():
    """Verify all required files exist."""
    print("Checking project files...")
    
    required_files = [
        "app.py",
        "requirements.txt",
        "README.md",
        "ARCHITECTURE.md",
        "DEPLOYMENT.md",
        "scheduler/__init__.py",
        "scheduler/models.py",
        "scheduler/optimizer.py",
        "scheduler/scenario_loader.py",
        "scheduler/utils.py",
        "scenarios/scenario_1.json",
        "scenarios/scenario_2.json",
        "scenarios/scenario_3.json",
        "scenarios/scenario_4.json",
        "scenarios/scenario_5.json",
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"  ❌ Missing files: {missing}")
        return False
    
    print(f"  ✅ All {len(required_files)} required files present")
    return True


def check_imports():
    """Verify all imports work."""
    print("\nChecking imports...")
    
    try:
        import streamlit
        print("  ✅ streamlit")
    except ImportError as e:
        print(f"  ❌ streamlit: {e}")
        return False
    
    try:
        import ortools
        print("  ✅ ortools")
    except ImportError as e:
        print(f"  ❌ ortools: {e}")
        return False
    
    try:
        import pandas
        print("  ✅ pandas")
    except ImportError as e:
        print(f"  ❌ pandas: {e}")
        return False
    
    try:
        from scheduler import load_all_scenarios, ChargingScheduler
        print("  ✅ scheduler package")
    except ImportError as e:
        print(f"  ❌ scheduler package: {e}")
        return False
    
    return True


def check_scenarios():
    """Verify scenarios load correctly."""
    print("\nChecking scenarios...")
    
    try:
        from scheduler import load_all_scenarios
        scenarios = load_all_scenarios("scenarios")
        
        if len(scenarios) != 5:
            print(f"  ❌ Expected 5 scenarios, found {len(scenarios)}")
            return False
        
        print(f"  ✅ Loaded {len(scenarios)} scenarios")
        
        # Check each scenario
        for scenario in scenarios:
            if not scenario.buses:
                print(f"  ❌ Scenario {scenario.id} has no buses")
                return False
            
            if not scenario.route.stations:
                print(f"  ❌ Scenario {scenario.id} has no stations")
                return False
        
        print("  ✅ All scenarios valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading scenarios: {e}")
        return False


def check_optimizer():
    """Verify optimizer works on a simple scenario."""
    print("\nChecking optimizer...")
    
    try:
        from scheduler import load_all_scenarios, ChargingScheduler
        
        scenarios = load_all_scenarios("scenarios")
        scenario = scenarios[0]  # Test with first scenario
        
        print(f"  Testing with: {scenario.name}")
        print(f"  Buses: {len(scenario.buses)}")
        
        scheduler = ChargingScheduler(time_limit_seconds=10)
        schedule = scheduler.build_schedule(scenario)
        
        if not schedule.bus_schedules:
            print("  ❌ No bus schedules generated")
            return False
        
        print(f"  ✅ Generated schedule for {len(schedule.bus_schedules)} buses")
        
        # Check for overlaps
        for station_id, events in schedule.station_schedules.items():
            for i in range(len(events) - 1):
                if events[i].end_time_min > events[i+1].start_time_min:
                    print(f"  ❌ Overlap detected at station {station_id}")
                    return False
        
        print("  ✅ No overlaps detected")
        
        # Check metrics
        total_delay = schedule.get_total_delay()
        max_delay = schedule.get_max_individual_delay()
        
        print(f"  Total delay: {total_delay} min")
        print(f"  Max individual delay: {max_delay} min")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Optimizer error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_data_models():
    """Verify data models work correctly."""
    print("\nChecking data models...")
    
    try:
        from scheduler.models import Bus, Station, Route, RouteSegment, Weights, Scenario
        
        # Create test objects
        bus = Bus(
            id="test-bus",
            operator="kpn",
            direction="Bengaluru->Kochi",
            departure_time="19:00"
        )
        
        station = Station(id="A", chargers=1, charging_time_min=25)
        
        segment = RouteSegment(from_point="Bengaluru", to_point="A", distance_km=100)
        
        route = Route(
            name="Test Route",
            segments=[segment],
            stations=[station],
            battery_range_km=240,
            speed_kmh=60
        )
        
        weights = Weights(individual=1.0, operator=1.0, overall=1.0)
        
        scenario = Scenario(
            id="test",
            name="Test Scenario",
            description="Test",
            route=route,
            buses=[bus],
            weights=weights
        )
        
        # Test methods
        assert bus.get_departure_minutes() == 19 * 60
        assert bus.is_forward_direction() == True
        assert scenario.get_all_operators() == ["kpn"]
        
        print("  ✅ All data models working")
        return True
        
    except Exception as e:
        print(f"  ❌ Data model error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("Bus Charging Scheduler - Project Verification")
    print("="*60)
    
    checks = [
        ("Files", check_files),
        ("Imports", check_imports),
        ("Data Models", check_data_models),
        ("Scenarios", check_scenarios),
        ("Optimizer", check_optimizer),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All checks passed! Project is ready for deployment.")
        print("="*60)
        print("\nNext steps:")
        print("1. Test locally: streamlit run app.py")
        print("2. Commit to Git: git add . && git commit -m 'Initial commit'")
        print("3. Deploy: Follow DEPLOYMENT.md")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
