"""
IPAWAS Master Data Population Script (FIXED)
=============================================

Executes all population scripts in the correct order using the current Python interpreter.

Run this script to populate the entire IPAWAS database.
"""

import os
import subprocess
import sys
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def run_script(script_path):
    """Run a Python script and handle errors"""
    script_name = os.path.basename(script_path)
    print(f"\n▶ Running: {script_name}")
    print("-" * 70)

    try:
        # FIXED: Use sys.executable to ensure we use the same Python interpreter
        result = subprocess.run(
            [sys.executable, script_path], capture_output=False, text=True, check=True
        )
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR in {script_name}")
        print(f"  Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR in {script_name}")
        print(f"  {str(e)}")
        return False


def main():
    """Main execution function"""
    start_time = datetime.now()

    print_header("IPAWAS PLATFORM DATA POPULATION")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using Python: {sys.executable}")
    print(f"Python Version: {sys.version.split()[0]}")
    print("\nThis script will populate the IPAWAS database with:")
    print("  - 12 ECOWAS Member State IPAs")
    print("  - Investment sectors and opportunities")
    print("  - Strategic partners and publications")
    print("  - Knowledge hub content")
    print("  - Sample users and inquiries")
    print("  - Events and registrations")

    response = input("\nProceed with data population? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Operation cancelled.")
        return

    # Define scripts in execution order
    scripts = [
        ("populate_core.py", "Core App Data"),
        ("populate_members_part1.py", "Member States (Part 1 of 3)"),
        ("populate_members_part2.py", "Member States (Part 2 of 3)"),
        ("populate_accounts.py", "Accounts & Users"),
        ("populate_members_part3.py", "Member States (Part 3 of 3)"),
        ("populate_knowledge_hub.py", "Knowledge Hub Content"),
        ("populate_opportunities.py", "Investment Opportunities"),
    ]

    # Track results
    results = []

    print_header("STARTING DATA POPULATION SEQUENCE")

    # Execute each script
    for idx, (script_name, description) in enumerate(scripts, 1):
        print(f"\nStep {idx}/{len(scripts)}: {description}")
        script_path = os.path.join(os.path.dirname(__file__), script_name)

        if not os.path.exists(script_path):
            print(f"✗ ERROR: Script not found: {script_name}")
            results.append((script_name, False))
            continue

        success = run_script(script_path)
        results.append((script_name, success))

        if not success:
            print(f"\n⚠ WARNING: {script_name} encountered errors")
            response = input("Continue with remaining scripts? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("\nStopping execution.")
                break

    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time

    print_header("DATA POPULATION SUMMARY")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration}")
    print("\nResults:")
    print("-" * 70)

    successful = 0
    failed = 0

    for script_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {status:12} - {script_name}")
        if success:
            successful += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"\nTotal: {len(results)} scripts")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n" + "=" * 70)
        print("  ✓ ALL DATA POPULATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nYou can now:")
        print("  1. Run the development server: python manage.py runserver")
        print("  2. Login with credentials shown in populate_accounts.py output")
        print("  3. Access the admin panel at /admin/")
        print("  4. View the platform at http://localhost:8000")
    else:
        print("\n⚠ Some scripts failed. Please check the errors above.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Check if Django is installed
    try:
        import django

        print(f"✓ Django {django.get_version()} detected")
    except ImportError:
        print("✗ ERROR: Django not found. Please install Django first.")
        sys.exit(1)

    main()
