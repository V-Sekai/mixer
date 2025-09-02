"""
Enhanced test utilities for pytest infrastructure
Provides profiling, performance monitoring, and test execution analytics
"""
import time
import psutil
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional
from functools import wraps


class TestProfiler:
    """Profiling tools for test performance analysis"""

    def __init__(self):
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'cpu_percent': [],
            'memory_mb': [],
            'io_read_mb': 0,
            'io_write_mb': 0,
        }
        self.monitoring = False

    def start_monitoring(self):
        """Start collecting system resource metrics"""
        if self.monitoring:
            return

        self.monitoring = True
        self.metrics['start_time'] = time.time()
        self._start_process = psutil.Process()
        self._baseline_io = psutil.net_io_counters()

        def collect_metrics():
            while self.monitoring:
                self.metrics['cpu_percent'].append(psutil.cpu_percent(interval=1))
                self.metrics['memory_mb'].append(psutil.virtual_memory().used / 1024 / 1024)
                time.sleep(0.5)

        self._monitor_thread = threading.Thread(target=collect_metrics, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> Dict:
        """Stop monitoring and return collected metrics"""
        if not self.monitoring:
            return self.metrics

        self.monitoring = False
        self.metrics['end_time'] = time.time()

        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=2)

        # Calculate final metrics
        runtime = self.metrics['end_time'] - self.metrics['start_time']
        avg_cpu = sum(self.metrics['cpu_percent']) / len(self.metrics['cpu_percent']) if self.metrics['cpu_percent'] else 0
        peak_memory = max(self.metrics['memory_mb']) if self.metrics['memory_mb'] else 0

        self.metrics.update({
            'runtime_seconds': runtime,
            'avg_cpu_percent': avg_cpu,
            'peak_memory_mb': peak_memory,
        })

        return self.metrics


def profile_test(func):
    """Decorator for profiling test functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = TestProfiler()
        profiler.start_monitoring()

        try:
            result = func(*args, **kwargs)
        finally:
            metrics = profiler.stop_monitoring()
            test_name = func.__name__

            # Store metrics for analysis if needed
            if hasattr(wrapper, '_collected_metrics'):
                wrapper._collected_metrics.append(metrics)

            print(f"\n📊 [PROFILER] {test_name}:")
            print(".2f")
            print(".1f")
            print(".1f")

        return result

    wrapper._collected_metrics = []
    return wrapper


@contextmanager
def profiled_context(name: str = "Context"):
    """Context manager for profiling code blocks"""
    profiler = TestProfiler()
    profiler.start_monitoring()

    print(f"⏱️  [PROFILE START] {name}")

    try:
        yield profiler
    finally:
        metrics = profiler.stop_monitoring()
        print(f"⏱️  [PROFILE END] {name}:")
        print(".2f")


class TestDatabase:
    """Simple in-memory test metrics database for analytics"""

    def __init__(self):
        self.results = []

    def add_result(self, test_name: str, metrics: Dict, result: str = "unknown"):
        """Add test result to database"""
        self.results.append({
            'test_name': test_name,
            'metrics': metrics,
            'result': result,
            'timestamp': time.time()
        })

    def get_slow_tests(self, threshold_seconds: float = 10.0) -> List[Dict]:
        """Find tests that took longer than threshold"""
        return [
            result for result in self.results
            if result['metrics'].get('runtime_seconds', 0) > threshold_seconds
        ]

    def get_performance_trends(self) -> str:
        """Generate simple performance report"""
        report = []
        report.append("📈 Performance Analysis Report")
        report.append("=" * 50)

        slow_tests = self.get_slow_tests(5.0)
        if slow_tests:
            report.append(f"\n🐌 Slow Tests (>5s): {len(slow_tests)}")
            for test in slow_tests[:5]:  # Show top 5
                runtime = test['metrics'].get('runtime_seconds', 0)
                report.append(".1f")

        if self.results:
            avg_runtime = sum(
                r['metrics'].get('runtime_seconds', 0) for r in self.results
            ) / len(self.results)
            report.append(".2f")

        return "\n".join(report)


# Global test database instance
test_db = TestDatabase()


def register_test_result(test_name: str, result: str = "passed"):
    """Helper function to register test results for analytics"""
    import pytest

    # Get current test item to collect metrics
    request = pytest.current_test
    if hasattr(request, 'node'):
        # We could collect more detailed metrics here if needed
        pass

    # For now, just log the test completion
    print(f"✅ Test registered: {test_name} ({result})")


def mark_slow_test(func):
    """Decorator to mark a test as slow (for filtering)"""
    func.pytestmark = [pytest.mark.slow]
    return func


# Usage examples and help functions
def demo_profiling():
    """Demo function to show profiling capabilities"""
    print("\n🔍 === TEST PROFILING DEMO ===\n")

    # Function profiling example
    @profile_test
    def example_test():
        time.sleep(1)  # Simulate test work
        return "test completed"

    example_test()

    # Context profiling example
    with profiled_context("Resource intensive operation"):
        time.sleep(0.5)
        # Simulate some computation
        sum(range(10000))


if __name__ == "__main__":
    demo_profiling()
