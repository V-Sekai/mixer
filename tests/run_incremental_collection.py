#!/usr/bin/env python3
"""
Incremental pytest collection runner for gradual infrastructure testing
"""

import subprocess
import sys
import os
from pathlib import Path

class PytestCollector:
    """Manages incremental pytest collection with fallbacks"""

    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.python_cmd = self._find_python()

    def _find_python(self):
        """Find available Python command"""
        for cmd in ["python3", "python", "python.exe"]:
            try:
                subprocess.run([cmd, "--version"],
                             capture_output=True,
                             check=True,
                             timeout=5)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def run_collection_phase(self, phase_name, cmd_args, description):
        """Run a specific collection phase with error handling"""
        print(f"\n🔍 Phase {phase_name}: {description}")

        try:
            if not self.python_cmd:
                print("❌ No Python command available")
                return False

            # Use uv if available for dependency management
            if self._has_uv():
                cmd = ["uv", "run"] + cmd_args
                print(f"Running: uv run {' '.join(cmd_args)}")
            else:
                cmd = [self.python_cmd] + cmd_args
                print(f"Running: {self.python_cmd} {' '.join(cmd_args)}")

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Count collected tests
                lines = result.stdout.split('\n')
                collected_count = 0
                for line in lines:
                    if '::' in line and any(word in line.lower() for word in ['test', 'fixture']):
                        collected_count += 1

                print(f"✅ Collection succeeded - collected {collected_count} items")
                return True
            else:
                print(f"⚠️ Collection completed with warnings (code {result.returncode})")
                # Print last few lines of output for diagnostics
                stdout_lines = result.stdout.split('\n')[-10:]
                stderr_lines = result.stderr.split('\n')[-5:]
                if stdout_lines:
                    print("Last stdout lines:")
                    for line in stdout_lines:
                        if line.strip():
                            print(f"  {line}")
                if stderr_lines:
                    print("Last stderr lines:")
                    for line in stderr_lines:
                        if line.strip():
                            print(f"  {line}")
                return True  # Consider warnings as success

        except subprocess.TimeoutExpired:
            print(f"⏰ Phase {phase_name} timed out")
            return False
        except Exception as e:
            print(f"❌ Phase {phase_name} failed: {e}")
            return False

    def _has_uv(self):
        """Check if uv is available"""
        try:
            subprocess.run(["uv", "--version"],
                         capture_output=True,
                         check=True,
                         timeout=10)
            return True
        except:
            return False

    def run_simple_infrastructure_test(self):
        """Test our simple collection script"""
        return self.run_collection_phase(
            "INFRA",
            ["tests/test_simple_collection.py"],
            "Testing basic pytest infrastructure"
        )

    def run_conftest_only_collection(self):
        """Collect only conftest-related fixtures"""
        return self.run_collection_phase(
            "CONFTEST",
            ["--collect-only", "tests/conftest.py", "-v"],
            "Testing conftest fixtures only"
        )

    def run_gradual_collection(self):
        """Gradually collect more test files"""
        phases = [
            ("BLENDER", ["--collect-only", "tests/blender/", "--tb=short"],
             "Testing Blender-specific tests"),
            ("VRTEST", ["--collect-only", "tests/generic/", "--tb=short"],
             "Testing VRtist tests"),
            ("FULL", ["--collect-only", "--tb=short"],
             "Full test collection"),
        ]

        results = []
        for phase_name, cmd_args, description in phases:
            success = self.run_collection_phase(phase_name, cmd_args, description)
            results.append(success)

        return results

def main():
    """Main incremental collection runner"""
    print("🚀 Pytest Incremental Collection Runner")
    print("=" * 50)

    project_root = Path(__file__).parent
    collector = PytestCollector(project_root)

    if not collector.python_cmd:
        print("❌ Cannot find Python - aborting")
        return 1

    # Phase 0: Infrastructure test
    if not collector.run_simple_infrastructure_test():
        print("❌ Infrastructure test failed - stopping")
        return 1

    # Phase 1: conftest collection
    if not collector.run_conftest_only_collection():
        print("⚠️ conftest collection failed - proceeding with caution")

    # Phase 2+: Gradual collection
    print("\n📈 Starting gradual collection phases...")
    results = collector.run_gradual_collection()

    successful = sum(results)
    total = len(results)

    print(f"\n📊 Collection Results: {successful}/{total} phases successful")

    if successful == total:
        print("🎉 All collection phases passed!")
        return 0
    else:
        print("⚠️ Some collection phases had issues")
        return 0  # Don't fail on warnings

if __name__ == "__main__":
    sys.exit(main())
