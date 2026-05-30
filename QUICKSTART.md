# Quick Start Guide

Get the Bus Charging Scheduler running in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for deployment)

## Local Setup

### 1. Clone or Download

If you have the code:
```bash
cd bus-charging-scheduler
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` - Web UI framework
- `ortools` - Google's optimization solver
- `pandas` - Data manipulation

### 3. Run the App

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

### 4. Use the App

1. **Select a scenario** from the dropdown (5 scenarios available)
2. **Review the input** - see buses, departure times, and weights
3. **Click "Generate Schedule"** - wait 5-60 seconds for optimization
4. **View results**:
   - Per-bus timetables showing charging stops and wait times
   - Per-station schedules showing charging order
   - Summary metrics (total delay, max delays)

## Testing

### Quick Test

```bash
python test_scheduler.py
```

This runs the optimizer on the first 2 scenarios and verifies:
- No overlapping charges at stations
- All buses complete their trips
- Optimization completes successfully

### Expected Output

```
Loaded 5 scenarios

============================================================
Testing: Even Spacing
============================================================
Buses: 20
Weights: individual=1.0, operator=1.0, overall=1.0

Results:
  Total delay: 1800 minutes
  Max individual delay: 180 minutes
  Operator delays: {'kpn': 660, 'freshbus': 600, 'flixbus': 540}
  ✅ No overlaps detected
```

## Understanding the Scenarios

### Scenario 1: Even Spacing
- **Purpose**: Baseline case
- **Pattern**: Buses depart every 15 minutes
- **Expected**: Moderate contention, balanced delays

### Scenario 2: Bunched Start
- **Purpose**: Test heavy early contention
- **Pattern**: Buses depart every 8 minutes initially
- **Expected**: Higher delays, more waiting

### Scenario 3: Asymmetric Load
- **Purpose**: Test uneven traffic
- **Pattern**: 10 buses one way, 4 the other
- **Expected**: Asymmetric station usage

### Scenario 4: Operator-Heavy
- **Purpose**: Test operator fairness
- **Pattern**: KPN has 8/10 buses in one direction
- **Expected**: Operator weight affects KPN's delays
- **Note**: Uses `operator=2.0` weight

### Scenario 5: Worst Case Convergence
- **Purpose**: Maximum stress test
- **Pattern**: All 20 buses in 72-minute window
- **Expected**: Highest delays, complex scheduling

## Modifying Scenarios

### Change Weights

Edit any `scenarios/scenario_X.json`:

```json
{
  "weights": {
    "individual": 2.0,  // Prioritize individual bus delays
    "operator": 1.0,    // Standard operator fairness
    "overall": 0.5      // Lower priority on total delay
  }
}
```

Higher weight = higher priority in optimization.

### Add a Bus

Edit `scenarios/scenario_X.json`:

```json
{
  "buses": [
    {
      "id": "bus-BK-11",
      "operator": "kpn",
      "direction": "Bengaluru->Kochi",
      "departure_time": "21:30"
    }
  ]
}
```

### Create New Scenario

Copy `scenarios/scenario_1.json` to `scenarios/scenario_6.json` and modify:

```json
{
  "id": "scenario_6",
  "name": "My Custom Scenario",
  "description": "Testing something specific",
  "route": "Bengaluru-Kochi",
  "weights": {
    "individual": 1.0,
    "operator": 1.0,
    "overall": 1.0
  },
  "buses": [
    // Your bus schedule here
  ]
}
```

The app will automatically detect and load it.

## Common Issues

### "No module named 'ortools'"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "No scenarios found"

**Solution**: Ensure you're in the project root directory and `scenarios/` folder exists
```bash
ls scenarios/  # Should show scenario_1.json through scenario_5.json
```

### Optimization takes too long

**Solution**: Reduce time limit in `app.py`:
```python
scheduler = ChargingScheduler(time_limit_seconds=30)  # Default is 60
```

### App won't start

**Solution**: Check Python version
```bash
python --version  # Should be 3.8 or higher
```

## Next Steps

### Learn More
- Read `README.md` for detailed usage
- Read `ARCHITECTURE.md` for technical deep dive
- Read `PROJECT_SUMMARY.md` for overview

### Deploy
- Follow `DEPLOYMENT.md` to deploy on Streamlit Cloud
- Get a public URL to share

### Extend
- Add new constraints in `scheduler/optimizer.py`
- Modify data models in `scheduler/models.py`
- Create custom scenarios in `scenarios/`

## Key Files

```
app.py                  # Main Streamlit UI - start here
scheduler/optimizer.py  # Core scheduling logic
scheduler/models.py     # Data structures
scenarios/*.json        # Test scenarios
```

## Getting Help

### Check Logs

Streamlit shows errors in the browser and terminal. Look for:
- Import errors → missing dependencies
- File not found → wrong directory
- Optimization errors → check scenario data

### Debug Mode

Run with verbose output:
```bash
streamlit run app.py --logger.level=debug
```

### Verify Installation

```bash
python -c "import streamlit, ortools, pandas; print('All dependencies installed!')"
```

## Performance Tips

### First Run
- First optimization may take longer (solver initialization)
- Subsequent runs are cached by Streamlit

### Large Scenarios
- 20 buses: ~5-10 seconds
- 50 buses: ~30-60 seconds
- 100+ buses: may need longer time limit

### Caching
- Scenarios are cached (reload only when files change)
- Schedules are cached (regenerate only when inputs change)

## Development Workflow

### 1. Make Changes
Edit code or scenarios

### 2. Test Locally
```bash
streamlit run app.py
```

### 3. Verify
- Load scenario
- Generate schedule
- Check results

### 4. Commit
```bash
git add .
git commit -m "Description of changes"
```

### 5. Deploy
```bash
git push
```

Streamlit Cloud auto-deploys on push.

## Tips for Success

1. **Start simple**: Test with scenario 1 first
2. **Understand the data**: Look at scenario JSON files
3. **Read the code**: Start with `models.py`, then `optimizer.py`
4. **Experiment**: Change weights, add buses, create scenarios
5. **Document**: Note what works and what doesn't

## Ready to Deploy?

See `DEPLOYMENT.md` for step-by-step instructions to deploy on Streamlit Community Cloud (free).

You'll get a public URL like:
```
https://your-username-bus-charging-scheduler.streamlit.app
```

## Questions?

- Check `README.md` for usage details
- Check `ARCHITECTURE.md` for technical details
- Check `PROJECT_SUMMARY.md` for overview
- Review code comments in `scheduler/` directory

Happy scheduling! 🚌⚡
