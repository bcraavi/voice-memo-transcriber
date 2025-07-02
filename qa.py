#!/usr/bin/env python3
"""
Generic Multi-Language Q&A Interface
Filters out telemetry error messages for a better user experience.
Supports all popular languages through the main.py interface.
"""

import sys
import subprocess
import os

def run_qa_clean():
    """Run the generic Q&A system and filter out telemetry errors."""
    
    # Set environment variables to disable telemetry
    env = os.environ.copy()
    env['ANONYMIZED_TELEMETRY'] = 'False'
    env['CHROMA_TELEMETRY_DISABLED'] = '1'
    
    # Determine the command to run
    if len(sys.argv) > 1:
        cmd = ['venv/bin/python', 'transcribe.py'] + sys.argv[1:]
    else:
        cmd = ['venv/bin/python', 'transcribe.py']
    
    # Run the command
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        env=env,
        bufsize=1
    )
    
    # Filter output to remove telemetry errors
    for line in process.stdout:
        # Skip telemetry error lines
        if 'Failed to send telemetry event' not in line:
            print(line, end='')
    
    process.wait()
    return process.returncode

if __name__ == "__main__":
    sys.exit(run_qa_clean())