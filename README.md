# Bus Charging Scheduler

An intelligent scheduling system for electric bus charging stations using constraint optimization.

## Overview

This system schedules charging for 20 electric buses traveling between Bengaluru and Kochi, optimizing for individual bus delays, operator fleet performance, and overall network efficiency.

## Technologies

- **Python 3.8+**
- **Streamlit**: Web UI framework
- **OR-Tools**: Google's constraint programming solver
- **Pandas**: Data manipulation
- **JSON**: Scenario data format

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

 
## Assumptions

1. **Speed**: Buses travel at 60 km/h consistently
2. **Charging**: Always charges to full (240 km range) in exactly 25 minutes
3. **Station selection**: Scheduler chooses optimal stations for each bus
4. **Wait handling**: Buses wait in queue if charger is occupied
5. **No preemption**: Once charging starts, it cannot be interrupted
6. **Route order**: Buses visit stations in route order (no backtracking)
