#!/bin/bash

for test in test_[0-9][0-9][0-9]*; do
    cd ${test}
    ./run.sh
    cd ..
done
