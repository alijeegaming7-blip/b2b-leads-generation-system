import sys
sys.path.insert(0, '.')
try:
    import main
    print("SUCCESS: All imports work!")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
