#!/bin/bash
export https_proxy="http://172.22.176.1:7890"
export http_proxy="http://172.22.176.1:7890"
cd /home/aqiu/.openclaw/workspace/memex
python3 benchmarks/quick_test.py
