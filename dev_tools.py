"""
כלי פיתוח למערכת הגנה משפטית
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path


def run_streamlit():
    """הרץ את המערכת"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])


def check_imports():
    """בדוק imports"""
    try:
        from core.chatbot import LegalChatBot
        from ui.sidebar import show_sidebar
        from processors.legal_summary import LegalSummaryProcessor
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def check_api_connection():
    """בדוק חיבור API"""
    try:
        from core.chatbot import LegalChatBot
        bot = LegalChatBot()
        if bot.claude_client:
            print("✅ Claude API connected")
            return True
        else:
            print("❌ Claude API not connected")
            return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False


def run_diagnostics():
    """הרץ בדיקות מערכת"""
    print("🔍 Running system diagnostics...")
    
    results = {
        "Imports": check_imports(),
        "API Connection": check_api_connection(),
        "Data Directory": Path("data").exists(),
        "Git Status": subprocess.run(["git", "status", "--porcelain"], 
                                   capture_output=True).returncode == 0
    }
    
    print("\n📊 Diagnostic Results:")
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Development tools")
    parser.add_argument("command", choices=["run", "check", "diagnose"])
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_streamlit()
    elif args.command == "check":
        check_imports()
    elif args.command == "diagnose":
        run_diagnostics()
