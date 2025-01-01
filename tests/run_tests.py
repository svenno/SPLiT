import unittest
import sys
import os
import subprocess
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_dhcp import TestDHCP
from test_tftp import TestTFTP
from test_http import TestHTTP
from test_proxy import TestProxy

def run_directory_tests():
    """Run all test scripts found in numbered test directories"""
    test_pattern = re.compile(r'^test_\d{3}')  # Matches 'test_' followed by exactly 3 digits
    test_dirs = [d for d in os.listdir('.') if test_pattern.match(d) and os.path.isdir(d)]
    test_dirs.sort()  # Run tests in numerical order
    
    failed_tests = []
    for test_dir in test_dirs:
        run_script = os.path.join(test_dir, 'run.sh')
        if os.path.exists(run_script):
            print(f"\nRunning tests in {test_dir}")
            try:
                subprocess.run(['bash', run_script], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Test {test_dir} failed with exit code {e.returncode}")
                failed_tests.append(test_dir)
    
    return len(failed_tests) == 0  # Return True if all tests passed

if __name__ == '__main__':
    # Run unittest-based tests
    unittest_result = unittest.main(verbosity=2, exit=False)
    unittest_success = unittest_result.result.wasSuccessful()
    
    # Run directory-based tests
    directory_success = run_directory_tests()
    
    # Exit with appropriate status code
    if not (unittest_success and directory_success):
        sys.exit(1)
    sys.exit(0) 