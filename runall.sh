#!/bin/bash

# Create a temporary directory for test artifacts
TEST_ARTIFACTS_DIR="/tmp/split_test_artifacts_$(date +%s)"
mkdir -p "$TEST_ARTIFACTS_DIR"

# Function to clean up old processes
cleanup() {
    echo "Cleaning up old processes..."
    # Kill any Python processes running SPLiT
    pkill -9 -f "python3 SPLiT.py" >/dev/null 2>/dev/null
    # Kill any SIPp processes
    pkill -9 -f "sipp" >/dev/null 2>/dev/null
    # Kill any processes using port 5060
    lsof -ti :5060 2>/dev/null | xargs -r kill -9 >/dev/null 2>/dev/null
    # Wait a moment to ensure processes are fully terminated
    sleep 2
}

# Function to check if port is in use
check_port() {
    if lsof -i :5060 >/dev/null 2>&1; then
        echo "Port 5060 is still in use. Trying to clean up..."
        cleanup
        if lsof -i :5060 >/dev/null 2>&1; then
            echo "Error: Port 5060 is still in use after cleanup. Please check manually."
            exit 1
        fi
    fi
}

# Main execution
echo "Starting test suite..."

# Clean up any existing processes
cleanup
check_port

# Start the proxy server
echo "Starting proxy server..."
python3 SPLiT.py -d -t -l log.txt&

# Store the process ID and remove it from shell job control to prevent kill messages
PROXY_PID=$!
disown $PROXY_PID

# Wait for proxy to start
sleep 2

# Verify proxy is running
if ! ps -p $PROXY_PID > /dev/null; then
    echo "Error: Proxy server failed to start"
    cleanup
    exit 1
fi

# Run the tests
echo "Running tests..."
cd tests/test_001 && ./run.sh
TEST_RESULT_1=$?

cd ../test_002 && ./run.sh
TEST_RESULT_2=$?

# Combine test results - if any test fails, the final result should be failure
TEST_RESULT=$((TEST_RESULT_1 || TEST_RESULT_2))

# Clean up after tests
echo "Cleaning up after tests..."
cleanup

[ $TEST_RESULT_1 -eq 0 ] && echo "Test 001: SUCCESS" || echo "Test 001: FAILED"
[ $TEST_RESULT_2 -eq 0 ] && echo "Test 002: SUCCESS" || echo "Test 002: FAILED"

# Exit with test result
exit $TEST_RESULT 