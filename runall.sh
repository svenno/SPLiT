#!/bin/bash

# Create a temporary directory for test artifacts
TEST_ARTIFACTS_DIR="/tmp/split_test_artifacts_$(date +%s)"
mkdir -p "$TEST_ARTIFACTS_DIR"

# Function to clean up old processes
cleanup() {
    echo "Cleaning up old processes..."
    # Kill any Python processes running SPLiT
    pkill -9 -f "python3 SPLiT.py" 2>/dev/null
    # Kill any SIPp processes
    pkill -9 -f "sipp" 2>/dev/null
    # Kill any processes using port 5060
    lsof -ti :5060 | xargs kill -9 2>/dev/null
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

# Function to preserve test artifacts
preserve_artifacts() {
    echo "Preserving test artifacts in $TEST_ARTIFACTS_DIR"
    if [ -d "tests/test_002" ]; then
        cp tests/test_002/*.dump "$TEST_ARTIFACTS_DIR/" 2>/dev/null
        cp tests/test_002/report_002.txt "$TEST_ARTIFACTS_DIR/" 2>/dev/null
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
PROXY_PID=$!

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
# exit 1
cd tests/test_001 && ./run.sh
TEST_RESULT=$?

cd ../test_002 && ./run.sh
TEST_RESULT=$?

# Preserve test artifacts before cleanup
# preserve_artifacts

# Clean up after tests
echo "Cleaning up after tests..."
cleanup

# Show test artifacts if they exist
if [ -n "$(ls -A $TEST_ARTIFACTS_DIR/*.dump 2>/dev/null)" ]; then
    echo "Test artifacts preserved in $TEST_ARTIFACTS_DIR:"
    ls -l "$TEST_ARTIFACTS_DIR"
    echo "Contents of dump files:"
    cat "$TEST_ARTIFACTS_DIR"/*.dump
fi

# Exit with test result
exit $TEST_RESULT 