#!/usr/bin/env python3
"""
Setup script for local Azure Functions development environment
This script installs dependencies and sets up the environment for proper autocomplete/IntelliSense
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and print status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("🚀 Setting up local development environment for Azure Functions")
    print("=" * 60)
    
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Already in a virtual environment")
        return True
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('.venv'):
        if not run_command('python3 -m venv .venv', 'Creating virtual environment'):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    print("\n📋 To activate the virtual environment, run:")
    print("   source .venv/bin/activate  # On macOS/Linux")
    print("   .venv\\Scripts\\activate     # On Windows")
    print("\nThen run this script again to install dependencies.")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    if not run_command('pip install -r requirements.txt', 'Installing Azure Functions dependencies'):
        return False
    
    # Install Azure Functions Core Tools if not already installed
    print("\n🛠️  Azure Functions Core Tools Installation:")
    print("   If you don't have Azure Functions Core Tools installed, run:")
    print("   npm install -g azure-functions-core-tools@4 --unsafe-perm true")
    print("   Or install via Homebrew on macOS: brew tap azure/functions && brew install azure-functions-core-tools@4")
    
    return True

def check_installation():
    """Check if installation was successful"""
    print("\n🧪 Testing installation...")
    
    try:
        import azure.functions
        print("✅ azure.functions imported successfully")
        
        import azure.cosmos
        print("✅ azure.cosmos imported successfully")
        
        import pydantic
        print("✅ pydantic imported successfully")
        
        print("\n🎉 All dependencies installed correctly!")
        print("   VS Code autocomplete should now work properly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Azure Functions development environment...")
    
    # Check if we're in a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        setup_virtual_environment()
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed")
        return
    
    # Test installation
    if check_installation():
        print("\n✅ Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Restart VS Code to refresh IntelliSense")
        print("2. Ensure VS Code is using the correct Python interpreter (.venv/bin/python)")
        print("3. Run 'func start' to test your functions locally")
    else:
        print("\n❌ Setup completed but some imports failed")

if __name__ == "__main__":
    main()
