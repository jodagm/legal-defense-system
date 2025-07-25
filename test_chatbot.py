"""
בדיקות לצ'אטבוט המשפטי
"""
from core.chatbot import LegalChatBot
import json


def test_chatbot_initialization():
    """בדיקת אתחול"""
    print("🧪 Testing chatbot initialization...")
    
    try:
        bot = LegalChatBot()
        print("✅ Chatbot initialized successfully")
        
        if bot.claude_client:
            print("✅ Claude API client connected")
        else:
            print("⚠️ Claude API client not connected (check API key)")
            
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_document_search():
    """בדיקת חיפוש מסמכים"""
    print("\n🧪 Testing document search...")
    
    try:
        bot = LegalChatBot()
        
        if not bot.has_documents():
            print("⚠️ No documents loaded for testing")
            return True
            
        # בדיקה פשוטה
        results = bot.simple_text_search("תביעה", max_results=3)
        print(f"✅ Found {len(results)} results for 'תביעה'")
        
        return True
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False


def test_ai_response():
    """בדיקת תשובת AI"""
    print("\n🧪 Testing AI response...")
    
    try:
        bot = LegalChatBot()
        
        if not bot.claude_client:
            print("⚠️ Skipping AI test - no API connection")
            return True
            
        response = bot.get_response("מה זה משפט?")
        
        if response and len(response) > 10:
            print("✅ AI response received")
            print(f"Response preview: {response[:100]}...")
            return True
        else:
            print("❌ AI response too short or empty")
            return False
            
    except Exception as e:
        print(f"❌ AI test failed: {e}")
        return False


def run_all_tests():
    """הרץ את כל הבדיקות"""
    print("🧪 Running Legal Defense System Tests\n")
    
    tests = [
        test_chatbot_initialization,
        test_document_search,
        test_ai_response
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed or were skipped")


if __name__ == "__main__":
    run_all_tests()
