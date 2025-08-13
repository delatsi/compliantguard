#!/usr/bin/env python3
"""
CompliantGuard Testing Control Script

Unified entry point for all testing operations.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_local_tests():
    """Run local tests (zero dependencies)"""
    print("🚀 Running Local Tests (Zero Dependencies)")
    print("=" * 45)
    
    testing_dir = Path(__file__).parent / "testing"
    local_dir = testing_dir / "local"
    
    if not local_dir.exists():
        print("❌ Testing directory not found")
        return False
    
    # Start server in background and run tests
    try:
        print("1. Starting test server...")
        server_process = subprocess.Popen([
            sys.executable, str(local_dir / "server.py")
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        import time
        time.sleep(2)
        
        print("2. Running test suite...")
        result = subprocess.run([
            sys.executable, str(local_dir / "test_all.py")
        ], capture_output=True, text=True)
        
        # Stop server
        server_process.terminate()
        server_process.wait()
        
        if result.returncode == 0:
            print("✅ Local tests passed!")
            print(result.stdout)
            return True
        else:
            print("❌ Local tests failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running local tests: {e}")
        if 'server_process' in locals():
            server_process.terminate()
        return False

def run_integration_tests():
    """Run integration tests (requires AWS)"""
    print("🧪 Running Integration Tests (Requires AWS)")
    print("=" * 45)
    
    testing_dir = Path(__file__).parent / "testing"
    integration_dir = testing_dir / "integration"
    
    if not integration_dir.exists():
        print("❌ Integration testing directory not found")
        return False
    
    try:
        print("1. Running integration test suite...")
        result = subprocess.run([
            sys.executable, str(integration_dir / "test_integration.py")
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Integration tests passed!")
            print(result.stdout)
            return True
        else:
            print("❌ Integration tests failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def setup_infrastructure():
    """Set up AWS infrastructure for testing"""
    print("🔧 Setting up AWS Infrastructure")
    print("=" * 35)
    
    testing_dir = Path(__file__).parent / "testing"
    integration_dir = testing_dir / "integration"
    setup_script = integration_dir / "setup_infrastructure.sh"
    
    if not setup_script.exists():
        print("❌ Setup script not found")
        return False
    
    try:
        result = subprocess.run([
            "bash", str(setup_script)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Infrastructure setup completed!")
            print(result.stdout)
            return True
        else:
            print("❌ Infrastructure setup failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up infrastructure: {e}")
        return False

def generate_test_data():
    """Generate test data"""
    print("🔧 Generating Test Data")
    print("=" * 25)
    
    testing_dir = Path(__file__).parent / "testing"
    tools_dir = testing_dir / "tools"
    generator = tools_dir / "generate_test_data.py"
    
    if not generator.exists():
        print("❌ Test data generator not found")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(generator)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test data generated!")
            print(result.stdout)
            return True
        else:
            print("❌ Test data generation failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        return False

def show_help():
    """Show available testing options"""
    print("🧪 CompliantGuard Testing Suite")
    print("=" * 35)
    print("")
    print("Available commands:")
    print("")
    print("  local        Run local tests (zero dependencies)")
    print("  integration  Run integration tests (requires AWS)")
    print("  setup        Set up AWS infrastructure")
    print("  data         Generate test data")
    print("  all          Run all tests (local + integration)")
    print("  help         Show this help message")
    print("")
    print("Examples:")
    print("  python3 test.py local")
    print("  python3 test.py integration")
    print("  python3 test.py all")
    print("")
    print("Quick start (recommended):")
    print("  python3 test.py local")

def main():
    """Main testing control function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "local":
        success = run_local_tests()
    elif command == "integration":
        success = run_integration_tests()
    elif command == "setup":
        success = setup_infrastructure()
    elif command == "data":
        success = generate_test_data()
    elif command == "all":
        print("🚀 Running All Tests")
        print("=" * 20)
        local_success = run_local_tests()
        print("\n" + "="*50 + "\n")
        integration_success = run_integration_tests()
        success = local_success and integration_success
        
        print(f"\n📊 Final Results:")
        print(f"Local Tests: {'✅ PASS' if local_success else '❌ FAIL'}")
        print(f"Integration Tests: {'✅ PASS' if integration_success else '❌ FAIL'}")
    elif command == "help":
        show_help()
        return
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()