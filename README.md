# Bus Charging Scheduler

An intelligent scheduling system for electric bus charging stations using constraint optimization.

## Overview

This system schedules charging for 20 electric buses traveling between Bengaluru and Kochi, optimizing for individual bus delays, operator fleet performance, and overall network efficiency.

## 🚀 Quick Start

**New to the project?** Start here: [QUICKSTART.md](QUICKSTART.md)

### Local Development

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the app**
```bash
streamlit run app.py
```

3. **Open browser**
The app will automatically open at `http://localhost:8501`

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive and design decisions
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy to Streamlit Cloud
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview

## How to Use

1. Select a scenario from the dropdown
2. View the scenario input data (buses, departure times, weights)
3. Click "Generate Schedule" to run the optimizer
4. Review results:
   - Per-bus timetables showing charging stops and wait times
   - Per-station views showing charging order
   - Summary metrics

## Changing Weights

Weights control the optimization priorities:
- **individual**: Minimize maximum delay for any single bus
- **operator**: Minimize maximum delay for any operator's fleet
- **overall**: Minimize total delay across all buses

### Method 1: Edit scenario files directly

Edit `scenarios/scenario_X.json` and modify the `weights` section:

```json
{
  "weights": {
    "individual": 1.0,
    "operator": 2.0,
    "overall": 1.0
  }
}
```

### Method 2: Programmatically

```python
from scheduler.scenario_loader import load_scenario

scenario = load_scenario("scenarios/scenario_1.json")
scenario.weights.individual = 1.5
scenario.weights.operator = 2.0
scenario.weights.overall = 1.0
```

## Adding a New Rule

The system uses OR-Tools CP-SAT solver with a modular constraint architecture.

### Example: Add priority for buses with long wait times

Edit `scheduler/optimizer.py`:

```python
def _add_priority_constraints(self, model, bus_vars, scenario):
    """Give priority to buses that have waited longer"""
    for bus in scenario.buses:
        for station_idx, station in enumerate(scenario.route.stations):
            # Calculate wait time at this station
            wait_time = bus_vars[bus.id]['wait'][station_idx]
            
            # Add soft constraint: penalize long waits
            # This integrates with existing objective function
            model.Add(wait_time <= 60)  # Hard limit: max 60 min wait
```

Then call it in `build_schedule()`:

```python
self._add_priority_constraints(model, bus_vars, scenario)
```

### Example: Add time-of-day electricity pricing

1. Add pricing data to scenario:

```json
{
  "electricity_pricing": {
    "peak_hours": [[19, 21]],
    "peak_multiplier": 1.5
  }
}
```

2. Add constraint in optimizer:

```python
def _add_electricity_cost_constraints(self, model, bus_vars, scenario):
    """Prefer charging during off-peak hours"""
    if not hasattr(scenario, 'electricity_pricing'):
        return
    
    for bus in scenario.buses:
        for station_idx, station in enumerate(scenario.route.stations):
            charge_start = bus_vars[bus.id]['charge_start'][station_idx]
            
            # Add cost penalty for peak hours
            for peak_start, peak_end in scenario.electricity_pricing['peak_hours']:
                # Soft constraint: avoid peak hours when possible
                is_peak = model.NewBoolVar(f'{bus.id}_peak_{station_idx}')
                model.Add(charge_start >= peak_start * 60).OnlyEnforceIf(is_peak)
                model.Add(charge_start < peak_end * 60).OnlyEnforceIf(is_peak)
```

## Project Structure

```
.
├── app.py                      # Streamlit UI
├── scheduler/
│   ├── __init__.py
│   ├── models.py              # Data models (Bus, Station, Route, etc.)
│   ├── optimizer.py           # Core scheduling engine (OR-Tools)
│   ├── scenario_loader.py     # Load and validate scenarios
│   └── utils.py               # Helper functions
├── scenarios/
│   ├── scenario_1.json        # Even spacing
│   ├── scenario_2.json        # Bunched start
│   ├── scenario_3.json        # Asymmetric load
│   ├── scenario_4.json        # Operator-heavy
│   └── scenario_5.json        # Worst case convergence
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## Assumptions

1. **Speed**: Buses travel at 60 km/h consistently
2. **Charging**: Always charges to full (240 km range) in exactly 25 minutes
3. **Station selection**: Scheduler chooses optimal stations for each bus
4. **Wait handling**: Buses wait in queue if charger is occupied
5. **No preemption**: Once charging starts, it cannot be interrupted
6. **Route order**: Buses visit stations in route order (no backtracking)

## Technologies

- **Python 3.8+**
- **Streamlit**: Web UI framework
- **OR-Tools**: Google's constraint programming solver
- **Pandas**: Data manipulation
- **JSON**: Scenario data format

## License

MIT
