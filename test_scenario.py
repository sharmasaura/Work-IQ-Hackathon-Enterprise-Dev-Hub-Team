import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "simulator"))

import engine as sim_engine_module
scenario_path = Path(__file__).parent / "simulator" / "scenarios" / "c1-northbridge"
sim_scenario = sim_engine_module.load_scenario(str(scenario_path))

print("Loaded sim_scenario:", type(sim_scenario))
print("sim_scenario class name:", sim_scenario.__class__.__name__)
print("sim_scenario.__dict__.keys():", list(sim_scenario.__dict__.keys())[:5])

# Now try the assignment
try:
    scenario = sim_scenario
    print("Assignment successful: scenario =", type(scenario))
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
