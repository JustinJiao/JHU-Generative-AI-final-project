"""
Evaluation script for testing all three methods
"""
import json
import sys
from pathlib import Path
from typing import Dict, List
from tabulate import tabulate

from models import EscalationInput, Message, CaseMetadata, DecisionType
from policy_retriever import PolicyRetriever
from decision_engine import DecisionEngine
from baselines import PromptOnlyBaseline, KeywordRuleBaseline


class Evaluator:
    """Evaluate escalation decision systems"""

    def __init__(
        self,
        policy_file: str,
        test_cases_file: str,
        api_key: str = None
    ):
        # Load test cases
        with open(test_cases_file, 'r') as f:
            data = json.load(f)
            self.test_cases = data['test_cases']

        # Initialize systems
        policy_retriever = PolicyRetriever(policy_file)
        self.main_system = DecisionEngine(policy_retriever, api_key=api_key)
        self.baseline_1 = PromptOnlyBaseline(api_key=api_key)
        self.baseline_2 = KeywordRuleBaseline()

    def run_evaluation(self, verbose: bool = True):
        """Run evaluation on all test cases"""
        results = {
            'main': {'correct': 0, 'total': 0, 'fp': 0, 'fn': 0, 'details': []},
            'baseline1': {'correct': 0, 'total': 0, 'fp': 0, 'fn': 0, 'details': []},
            'baseline2': {'correct': 0, 'total': 0, 'fp': 0, 'fn': 0, 'details': []}
        }

        for test_case in self.test_cases:
            if verbose:
                print(f"\nTesting: {test_case['id']} - {test_case['name']}")

            # Prepare input
            input_data = self._prepare_input(test_case['input'])
            expected = test_case['expected_output']

            # Test main system
            main_result = self.main_system.make_decision(input_data)
            self._record_result(results['main'], main_result, expected, test_case)

            # Test baseline 1
            baseline1_result = self.baseline_1.make_decision(input_data)
            self._record_result(results['baseline1'], baseline1_result, expected, test_case)

            # Test baseline 2
            baseline2_result = self.baseline_2.make_decision(input_data)
            self._record_result(results['baseline2'], baseline2_result, expected, test_case)

            if verbose:
                print(f"  Main: {main_result.decision.value} -> {main_result.target_team}")
                print(f"  B1:   {baseline1_result.decision.value} -> {baseline1_result.target_team}")
                print(f"  B2:   {baseline2_result.decision.value} -> {baseline2_result.target_team}")
                print(f"  Expected: {expected['decision']} -> {expected['target_team']}")

        return results

    def _prepare_input(self, input_data: Dict) -> EscalationInput:
        """Convert test case input to EscalationInput"""
        messages = [Message(**m) for m in input_data['messages']]
        metadata = CaseMetadata(**input_data['metadata'])
        return EscalationInput(messages=messages, metadata=metadata)

    def _record_result(
        self,
        results: Dict,
        output,
        expected: Dict,
        test_case: Dict
    ):
        """Record evaluation results"""
        results['total'] += 1

        # Check decision correctness
        expected_decision = expected['decision']
        actual_decision = output.decision.value

        is_correct = (actual_decision == expected_decision)

        if is_correct:
            results['correct'] += 1

        # Track false positives and false negatives
        if actual_decision == 'escalate' and expected_decision == 'no_escalate':
            results['fp'] += 1  # False positive
        elif actual_decision == 'no_escalate' and expected_decision == 'escalate':
            results['fn'] += 1  # False negative

        # Store details
        results['details'].append({
            'test_id': test_case['id'],
            'test_name': test_case['name'],
            'expected': expected_decision,
            'actual': actual_decision,
            'correct': is_correct,
            'expected_team': expected.get('target_team'),
            'actual_team': output.target_team,
            'confidence': output.confidence
        })

    def print_summary(self, results: Dict):
        """Print evaluation summary"""
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)

        summary_data = []
        for system_name, system_results in results.items():
            total = system_results['total']
            correct = system_results['correct']
            accuracy = (correct / total * 100) if total > 0 else 0
            fpr = (system_results['fp'] / total * 100) if total > 0 else 0
            fnr = (system_results['fn'] / total * 100) if total > 0 else 0

            summary_data.append([
                system_name.upper(),
                f"{correct}/{total}",
                f"{accuracy:.1f}%",
                f"{fpr:.1f}%",
                f"{fnr:.1f}%"
            ])

        headers = ["System", "Correct", "Accuracy", "FP Rate", "FN Rate"]
        print("\n" + tabulate(summary_data, headers=headers, tablefmt="grid"))

        # Print detailed errors
        print("\n" + "="*80)
        print("DETAILED ERRORS")
        print("="*80)

        for system_name, system_results in results.items():
            errors = [d for d in system_results['details'] if not d['correct']]
            if errors:
                print(f"\n{system_name.upper()} Errors ({len(errors)}):")
                for error in errors:
                    print(f"  - {error['test_id']}: Expected {error['expected']}, got {error['actual']}")
                    print(f"    Test: {error['test_name']}")

    def export_results(self, results: Dict, output_file: str):
        """Export results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults exported to {output_file}")


def main():
    """Main evaluation function"""
    BASE_DIR = Path(__file__).parent.parent
    POLICY_FILE = BASE_DIR / "data" / "escalation_policies.json"
    TEST_CASES_FILE = BASE_DIR / "data" / "test_cases.json"

    print("Customer Support Escalation Assistant - Evaluation")
    print("="*80)

    # Check if files exist
    if not POLICY_FILE.exists():
        print(f"Error: Policy file not found: {POLICY_FILE}")
        sys.exit(1)

    if not TEST_CASES_FILE.exists():
        print(f"Error: Test cases file not found: {TEST_CASES_FILE}")
        sys.exit(1)

    # Initialize evaluator
    evaluator = Evaluator(
        policy_file=str(POLICY_FILE),
        test_cases_file=str(TEST_CASES_FILE)
    )

    # Run evaluation
    print("\nRunning evaluation on test cases...")
    results = evaluator.run_evaluation(verbose=True)

    # Print summary
    evaluator.print_summary(results)

    # Export results
    output_file = BASE_DIR / "evaluation_results.json"
    evaluator.export_results(results, str(output_file))


if __name__ == "__main__":
    # Note: tabulate is not in requirements.txt yet
    # If tabulate is not installed, it will fall back to simple printing
    try:
        from tabulate import tabulate
    except ImportError:
        print("Note: Install 'tabulate' for better output formatting: pip install tabulate")
        # Simple fallback
        def tabulate(data, headers, tablefmt):
            result = " | ".join(headers) + "\n"
            result += "-" * 80 + "\n"
            for row in data:
                result += " | ".join(str(x) for x in row) + "\n"
            return result

    main()
