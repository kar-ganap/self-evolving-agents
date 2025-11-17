import subprocess
import json
import logging
import tempfile
import os
import sys
from typing import Dict, Any, List

# Configure basic logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

class ProductionReadiness:
    """
    A wrapper class for the 'pytest-cov' library to check test coverage.

    This class uses pytest-cov to measure the test coverage of a given Python
    project. It interprets the results to provide a "production readiness" score
    based on the percentage of code covered by tests.
    """

    def _get_default_result(self) -> Dict[str, Any]:
        """Returns a default result structure for failure cases."""
        return {
            'score': 0.0,
            'checks': {},
            'issues': [],
            'suggestions': []
        }

    def _run_pytest_cov(self, target_path: str) -> Dict[str, Any]:
        """
        Runs pytest-cov as a subprocess and returns the parsed JSON output.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_report:
            report_path = tmp_report.name
        
        # Determine the module/package name to target with --cov.
        # This is a common convention, but might need adjustment for complex layouts.
        cov_target = os.path.basename(target_path) if os.path.isdir(target_path) else os.path.dirname(target_path)
        if not cov_target:
            cov_target = "."

        command = [
            sys.executable,
            '-m',
            'pytest',
            target_path,
            f'--cov={cov_target}',
            '--cov-report',
            f'json:{report_path}',
            '--cov-fail-under=0'  # Always generate a report, don't fail the run
        ]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )

            # Pytest exit codes: 0=OK, 1=tests failed, 5=no tests collected.
            # We can often still get a coverage report even if tests fail.
            if process.returncode not in [0, 1, 5]:
                error_message = f"Pytest execution failed with an unexpected exit code {process.returncode}."
                details = process.stderr or process.stdout
                logging.error(f"{error_message}\nDetails: {details}")
                # We'll still try to read the report, but log the error.

            if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
                error_message = "pytest-cov did not generate a coverage report."
                details = "This could be due to test failures, no tests found, or a configuration issue.\n" + (process.stderr or process.stdout)
                logging.error(f"{error_message}\nDetails: {details}")
                return {'error': error_message, 'details': details}

            with open(report_path, 'r') as f:
                return json.load(f)

        except FileNotFoundError:
            logging.error("pytest or python executable not found. Make sure pytest and pytest-cov are installed.")
            return {'error': "pytest not found. Please ensure it's installed and in your PATH."}
        except json.JSONDecodeError:
            logging.error("Failed to parse pytest-cov JSON report.")
            return {'error': "Could not parse the coverage report. It might be corrupted or empty."}
        except Exception as e:
            logging.error(f"An unexpected error occurred while running pytest-cov: {e}")
            return {'error': f"An unexpected error occurred: {str(e)}"}
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)

    def _format_output(self, cov_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the raw pytest-cov JSON data into the standardized format.
        """
        if 'error' in cov_data:
            result = self._get_default_result()
            result['issues'].append({
                'type': 'Execution Error',
                'message': cov_data['error'],
                'details': cov_data.get('details', '')
            })
            result['suggestions'].append("Ensure 'pytest' and 'pytest-cov' are installed and that the target path contains a valid project with tests.")
            return result

        totals = cov_data.get('totals', {})
        if not totals or 'percent_covered' not in totals:
            result = self._get_default_result()
            result['issues'].append({
                'type': 'No Coverage Data',
                'message': 'The coverage report was empty or did not contain summary totals.',
                'details': 'This can happen if no code was executed during the test run.'
            })
            result['suggestions'].append("Verify that your tests are correctly discovering and executing the code you want to measure.")
            return result

        score = totals.get('percent_covered', 0.0) / 100.0

        checks = {
            'total_coverage_percent': totals.get('percent_covered', 0.0),
            'covered_lines': totals.get('covered_lines', 0),
            'total_statements': totals.get('num_statements', 0),
            'missing_lines': totals.get('missing_lines', 0),
            'covered_branches': totals.get('covered_branches', 0),
            'total_branches': totals.get('num_branches', 0),
        }

        issues: List[Dict[str, Any]] = []
        suggestions: List[str] = []

        for filename, data in cov_data.get('files', {}).items():
            summary = data.get('summary', {})
            percent_covered = summary.get('percent_covered', 100.0)

            if percent_covered < 100.0:
                missing_lines = data.get('missing_lines', [])
                issue = {
                    'file': filename,
                    'message': f"Incomplete test coverage ({percent_covered:.2f}%)",
                    'details': f"Missing lines: {missing_lines}"
                }
                issues.append(issue)
                suggestions.append(f"Improve test coverage for '{filename}' by adding tests that execute lines: {missing_lines}.")

        if not issues and score > 0:
            suggestions.append("Great job! All executed files appear to have 100% test coverage.")
        elif score == 0:
            suggestions.append("No lines were covered. Check if tests ran correctly and targeted the right code.")

        return {
            'score': round(score, 4),
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions
        }

    def analyze(self, code: str, file_path: str = None) -> Dict[str, Any]:
        """
        Analyzes a Python project's test coverage using pytest-cov.

        Note: This tool requires a file path to a valid project structure with
        tests that pytest can discover and run. The 'code' parameter is ignored
        as pytest-cov operates on file-based projects, not in-memory code strings.

        Args:
            code (str): This parameter is ignored for this specific tool.
            file_path (str, optional): The path to the Python project directory or
                                       a specific file to analyze. This path should
                                       contain the source code and associated tests.
                                       Defaults to None.

        Returns:
            dict: A dictionary in the standardized format:
                  {'score': float, 'checks': dict, 'issues': list, 'suggestions': list}
        """
        if not file_path:
            logging.error("A file_path to a project directory is required for pytest-cov analysis.")
            result = self._get_default_result()
            result['issues'].append({
                'type': 'Configuration Error',
                'message': 'No file_path provided.',
                'details': 'pytest-cov requires a path to a project to run tests and measure coverage.'
            })
            result['suggestions'].append("Provide a valid 'file_path' to your project's root directory.")
            return result
        
        if not os.path.exists(file_path):
            logging.error(f"The provided file_path does not exist: {file_path}")
            result = self._get_default_result()
            result['issues'].append({
                'type': 'Configuration Error',
                'message': 'Provided file_path does not exist.',
                'details': f"Path '{file_path}' could not be found."
            })
            result['suggestions'].append("Please provide a valid 'file_path'.")
            return result

        raw_results = self._run_pytest_cov(file_path)
        return self._format_output(raw_results)