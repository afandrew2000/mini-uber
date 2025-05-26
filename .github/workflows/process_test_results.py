#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Get the API URL from environment variable or use default production URL
API_URL = os.getenv('TEST_RESULTS_API_URL', 'https://49ce-128-135-204-235.ngrok-free.app/api/test-results')

def run_pytest() -> tuple[int, str, str]:
    """Run pytest and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            ["pytest", "tests", "-v"],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", f"Failed to run pytest: {str(e)}"

def parse_pytest_output(stdout: str) -> List[Dict[str, Any]]:
    """Parse pytest output and convert to test results format."""
    results = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Regular expression to match pytest output lines
    # Example: test_file.py::test_function PASSED
    test_pattern = re.compile(r'^(.+?)\s+(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)(?:\s+\[.*?\])?$')
    
    # Split output into lines and process each test result
    for line in stdout.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = test_pattern.match(line)
        if not match:
            continue
            
        try:
            test_path = match.group(1)
            result = match.group(2)
            
            # Split test path into components
            path_parts = test_path.split('::')
            file_path = path_parts[0]
            test_name = path_parts[-1] if len(path_parts) > 1 else "unknown"
            
            # Extract module and category from file path
            path_components = file_path.split('/')
            # If the module name ends with .py, set it to 'core'
            module = 'core' if path_components[1].endswith('.py') else path_components[1] if len(path_components) > 1 else "unknown"
            category = path_components[2] if len(path_components) > 2 else "unknown"
            
            # Map pytest result to status
            status_map = {
                "PASSED": "passed",
                "FAILED": "failed",
                "SKIPPED": "skipped",
                "ERROR": "error",
                "XFAIL": "expected_failure",
                "XPASS": "unexpected_pass"
            }
            status = status_map.get(result, "unknown")
            
            results.append({
                "module": module,
                "category": category,
                "test_name": test_name,
                "status": status,
                "output": line,
                "attempted_at": timestamp,
                "completed_at": timestamp
            })
            
        except Exception as e:
            print(f"Error parsing line: {line}", file=sys.stderr)
            print(f"Error details: {str(e)}", file=sys.stderr)
            results.append({
                "module": "error",
                "category": "error",
                "test_name": "parse_error",
                "status": "error",
                "output": f"Error parsing test output: {str(e)}\nLine: {line}",
                "attempted_at": timestamp,
                "completed_at": timestamp
            })
    
    # If no results were parsed, add an error entry
    if not results:
        print("No test results found in output:", file=sys.stderr)
        print(stdout, file=sys.stderr)
        results.append({
            "module": "error",
            "category": "error",
            "test_name": "no_tests",
            "status": "error",
            "output": f"No test results found in output:\n{stdout[:1000]}...",  # Truncate very long output
            "attempted_at": timestamp,
            "completed_at": timestamp
        })
    
    return results

def upload_to_supabase(results: List[Dict[str, Any]]) -> bool:
    """Upload results to Supabase through Next.js API."""
    import requests
    from requests.exceptions import RequestException
    
    # List of URLs to try in order
    urls_to_try = [
        API_URL,
        'https://49ce-128-135-204-235.ngrok-free.app/api/test-results',
        'https://codemini.vercel.app/api/test-results',
    ]
    
    last_error = None
    
    for url in urls_to_try:
        try:
            print(f"\nTrying API URL: {url}", file=sys.stderr)
            headers = {
                "Content-Type": "application/json"
            }
            
            # Convert test results to JSONB array format as expected by the database
            tests_status = [
                {
                    "module": result["module"],
                    "category": result["category"],
                    "test_name": result["test_name"],
                    "status": result["status"],
                    "attempted_at": result["attempted_at"],
                    "completed_at": result["completed_at"],
                    "output": result["output"]
                }
                for result in results
            ]
            
            # Create the update data
            data = {
                "id": "4600c943-a7f9-4efc-ad50-615921f9bf00",
                "tests_status": tests_status
            }
            
            # Print request data for debugging
            print("\nSending to API:", file=sys.stderr)
            print(f"URL: {url}", file=sys.stderr)
            print("Headers:", json.dumps(headers, indent=2), file=sys.stderr)
            print("Data:", json.dumps(data, indent=2), file=sys.stderr)
            
            # Make the request with a timeout
            response = requests.post(
                url, 
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"\nAPI Response:", file=sys.stderr)
            print(f"Status Code: {response.status_code}", file=sys.stderr)
            print(f"Response Body: {response.text}", file=sys.stderr)
            
            if response.status_code in (200, 201, 204):
                print(f"Successfully uploaded to {url}", file=sys.stderr)
                return True
            
            print(f"Error response from {url}. Status code: {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            
        except RequestException as e:
            last_error = e
            print(f"Network error while trying {url}: {str(e)}", file=sys.stderr)
            continue
        except Exception as e:
            last_error = e
            print(f"Unexpected error while trying {url}: {str(e)}", file=sys.stderr)
            continue
    
    # If we get here, all URLs failed
    print("\nAll API endpoints failed.", file=sys.stderr)
    if last_error:
        print(f"Last error: {str(last_error)}", file=sys.stderr)
    return False

def main():
    """Main function to run tests and process results."""
    try:
        # Run pytest and collect output
        print("Running pytest...", file=sys.stderr)
        exit_code, stdout, stderr = run_pytest()
        
        # Print raw output for debugging
        print("\nPytest Output:", file=sys.stderr)
        print(stdout, file=sys.stderr)
        if stderr:
            print("\nPytest Errors:", file=sys.stderr)
            print(stderr, file=sys.stderr)
        
        # Parse the output into our format
        print("\nParsing test results...", file=sys.stderr)
        results = parse_pytest_output(stdout)
        
        # If there was an error running pytest, add it to results
        if exit_code != 0 and stderr:
            timestamp = datetime.now(timezone.utc).isoformat()
            results.append({
                "module": "error",
                "category": "error",
                "test_name": "pytest_error",
                "status": "error",
                "output": f"Pytest error (exit code {exit_code}):\n{stderr}",
                "attempted_at": timestamp,
                "completed_at": timestamp
            })
        
        # Print parsed results
        print("\nParsed Test Results:", file=sys.stderr)
        print(json.dumps(results, indent=2), file=sys.stderr)
        
        # Upload results to Supabase
        print("\nUploading results to Supabase...", file=sys.stderr)
        if upload_to_supabase(results):
            print("Successfully uploaded results to Supabase", file=sys.stderr)
            print(json.dumps(results, indent=2))  # Print to stdout for workflow
        else:
            print("Failed to upload results to Supabase", file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        timestamp = datetime.now(timezone.utc).isoformat()
        error_result = [{
            "module": "error",
            "category": "error",
            "test_name": "script_error",
            "status": "error",
            "output": f"Script error: {str(e)}",
            "attempted_at": timestamp,
            "completed_at": timestamp
        }]
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()