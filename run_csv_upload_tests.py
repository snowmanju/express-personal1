"""
Script to run all CSV upload feature tests and generate a summary report
"""

import subprocess
import sys

# List of all CSV upload feature tests
CSV_UPLOAD_TESTS = [
    # Unit tests
    "test_file_validator_unit.py",
    "test_template_download.py",
    
    # Property-based tests
    "test_file_validation_properties.py",
    "test_file_format_processing_properties.py",
    "test_utf8_encoding_properties.py",
    "test_comprehensive_data_validation_properties.py",
    "test_error_recovery_properties.py",
    "test_preview_mode_isolation_properties.py",
    "test_save_mode_persistence_properties.py",
    "test_mode_consistency_properties.py",
    "test_statistics_accuracy_properties.py",
    "test_duplicate_detection_properties.py",
    "test_error_categorization_properties.py",
    "test_auth_verification_properties.py",
    "test_security_input_handling_properties.py",
    "test_audit_logging_properties.py",
    "test_data_persistence_timestamps_properties.py",
    "test_duplicate_handling_properties.py",
    "test_storage_error_recovery_properties.py",
    "test_performance_compliance_properties.py",
    "test_concurrency_safety_properties.py",
]

def run_tests():
    """Run all CSV upload tests and collect results"""
    print("=" * 80)
    print("Running CSV Upload Feature Tests")
    print("=" * 80)
    print()
    
    results = {}
    
    for test_file in CSV_UPLOAD_TESTS:
        print(f"\nRunning {test_file}...")
        print("-" * 80)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test file
            )
            
            # Parse output for pass/fail counts
            output = result.stdout + result.stderr
            
            if "passed" in output:
                results[test_file] = "PASSED"
                print(f"✓ {test_file}: PASSED")
            elif "failed" in output:
                results[test_file] = "FAILED"
                print(f"✗ {test_file}: FAILED")
            else:
                results[test_file] = "ERROR"
                print(f"⚠ {test_file}: ERROR")
                
        except subprocess.TimeoutExpired:
            results[test_file] = "TIMEOUT"
            print(f"⏱ {test_file}: TIMEOUT")
        except Exception as e:
            results[test_file] = f"ERROR: {str(e)}"
            print(f"⚠ {test_file}: ERROR - {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v == "PASSED")
    failed = sum(1 for v in results.values() if v == "FAILED")
    errors = sum(1 for v in results.values() if v not in ["PASSED", "FAILED"])
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors/Timeouts: {errors}")
    print()
    
    # Print detailed results
    print("\nDetailed Results:")
    print("-" * 80)
    for test_file, status in results.items():
        status_symbol = "✓" if status == "PASSED" else "✗" if status == "FAILED" else "⚠"
        print(f"{status_symbol} {test_file}: {status}")
    
    return results

if __name__ == "__main__":
    results = run_tests()
    
    # Exit with error code if any tests failed
    if any(v != "PASSED" for v in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)
