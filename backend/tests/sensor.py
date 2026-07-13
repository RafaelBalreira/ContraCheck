import sys, os, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'backend/tests/test_extraction.py', '-v', '-q'],
    capture_output=True, text=True, cwd=ROOT,
)
print("STDOUT:", repr(result.stdout[:200]))
print("STDERR:", repr(result.stderr[:500]))
print("RC:", result.returncode)
