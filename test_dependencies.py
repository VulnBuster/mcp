#!/usr/bin/env python3
"""
Check installation of all required dependencies for Bandit MCP
"""

import sys
import subprocess

def check_package(package_name, import_name=None):
    """Checks package installation"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} - installed")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT installed")
        return False

def check_command(command):
    """Checks command availability in system"""
    try:
        result = subprocess.run([command, "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command} - available")
            return True
        else:
            print(f"❌ {command} - unavailable")
            return False
    except FileNotFoundError:
        print(f"❌ {command} - not found")
        return False

def main():
    print("🔒 Checking Bandit MCP Dependencies")
    print("=" * 50)
    
    all_good = True
    
    # Check Python packages
    print("\n📦 Python packages:")
    packages = [
        ("gradio", "gradio"),
        ("bandit", "bandit"),
        ("smolagents", "smolagents")
    ]
    
    for package, import_name in packages:
        if not check_package(package, import_name):
            all_good = False
    
    # Check commands
    print("\n🔧 System commands:")
    commands = ["bandit", "npx"]
    
    for command in commands:
        if not check_command(command):
            all_good = False
    
    # Check specific bandit capabilities
    print("\n🎯 Bandit capabilities:")
    try:
        result = subprocess.run(["bandit", "--help"], 
                              capture_output=True, text=True)
        if "-f json" in result.stdout:
            print("✅ JSON format - supported")
        else:
            print("❌ JSON format - not supported")
            
        if "-b" in result.stdout:
            print("✅ Baseline - supported")
        else:
            print("❌ Baseline - not supported")
            
        if "-p" in result.stdout:
            print("✅ Profiles - supported")
        else:
            print("❌ Profiles - not supported")
            
    except Exception as e:
        print(f"❌ Error checking Bandit: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All dependencies are installed correctly!")
        print("💡 Now you can run: python app.py")
    else:
        print("⚠️  Some dependencies are missing.")
        print("💡 Install them with: pip install -r requirements.txt")
        print("💡 For npm dependencies: npm install -g npx")
        
    return all_good

if __name__ == "__main__":
    main() 