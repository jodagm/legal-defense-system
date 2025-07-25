"""
ממשק הצ'אט הראשי
"""
import streamlit as st

from config.settings import UI_MESSAGES
from processors.comprehensive_tasks import ComprehensiveTaskManager


def initialize_chat_history():
    """אתחל היסטוריית צ'אט אם לא קיימת"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": UI_MESSAGES["welcome"]
            }
        ]


def display_chat_messages():
    """הצג את כל ההודעות בצ'אט"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])


def handle_comprehensive_tasks(chatbot):
    """טפל במשימות מקיפות"""
    if hasattr(st.session_state, 'comprehensive_task'):
        task_type = st.session_state.comprehensive_task
        del st.session_state.comprehensive_task
        
        # יצור מנהל המשימות המקיפות
        comprehensive_manager = ComprehensiveTaskManager(chatbot)
        
        # בדוק שיש סיכומים
        summaries = comprehensive_manager.summary_processor.get_all_summaries()
        if not summaries:
            error_msg = UI_MESSAGES["no_summaries"]
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()
        
        # הצג את המשימה המבוקשת
        task_names = {
            "witness_statement": "🏛️ מסמך עדות ראשי מקיף (ללא הגבלות)",
            "defense_strategy": "⚖️ אסטרטגיית הגנה מלאה (ללא הגבלות)",
            "contradictions": "🔍 זיהוי כל הסתירות (ללא הגבלות)",
            "chronological": "📅 ניתוח כרונולוגי מלא (ללא הגבלות)",
            "connections": "🕷️ מפת קשרים מקיפה (ללא הגבלות)", 
            "executive_summary": "📋 סיכום מנהלים (ללא הגבלות)"
        }
        
        task_name = task_names.get(task_type, "משימה מקיפה")
        st.session_state.messages.append({"role": "user", "content": task_name})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(task_name)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner(f"🧠 מבצע ניתוח מקיף ללא הגבלות... זה יכול לקחת 1-2 דקות..."):
                
                # בצע את המשימה המקיפה על בסיס הסיכומים
                if task_type == "witness_statement":
                    response = comprehensive_manager.build_witness_statement()
                elif task_type == "defense_strategy":
                    response = comprehensive_manager.comprehensive_defense_strategy()
                elif task_type == "contradictions":
                    response = comprehensive_manager.find_all_contradictions()
                elif task_type == "chronological":
                    response = comprehensive_manager.chronological_analysis()
                elif task_type == "connections":
                    response = comprehensive_manager.connections_mapping()
                elif task_type == "executive_summary":
                    response = comprehensive_manager.executive_summary()
                else:
                    response = f"❌ משימה '{task_type}' טרם מומש. בקרוב..."
                
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})


def handle_quick_questions(chatbot):
    """טפל בשאלות מהירות"""
    if hasattr(st.session_state, 'quick_question'):
        prompt = st.session_state.quick_question
        del st.session_state.quick_question
        
        docs_info = chatbot.get_documents_info()
        if docs_info['total_chunks'] == 0:
            error_msg = UI_MESSAGES["no_documents"]
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()
        
        st.session_state.messages.append({"role": "user", "content": f"🔍 {prompt}"})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"🔍 {prompt}")
        
        with st.chat_message("assistant", avatar="🤖"):
            ai_name = "Claude" if chatbot.claude_client else "Ollama"
            with st.spinner(f"🧠 {ai_name} מחפש ומנתח ללא הגבלות..."):
                response = chatbot.chat_with_documents(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})


def handle_user_input(chatbot):
    """טפל בקלט משתמש חדש"""
    if prompt := st.chat_input("🔍 שאל כל שאלה משפטית - ללא הגבלות או צנזורה..."):
        # הוסף הודעת משתמש
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # התשובה של Claude או Ollama (מצב רגיל על הטקסט הגולמי)
        with st.chat_message("assistant", avatar="🤖"):
            docs_info = chatbot.get_documents_info()
            if docs_info['total_chunks'] == 0:
                response = UI_MESSAGES["no_documents"]
            else:
                ai_name = "Claude" if chatbot.claude_client else "Ollama"
                with st.spinner(f"🧠 {ai_name} מנתח ללא הגבלות..."):
                    response = chatbot.chat_with_documents(prompt)
            
            st.markdown(response)
        
        # הוסף תשובה להיסטוריה
        st.session_state.messages.append({"role": "assistant", "content": response})


def show_chat_interface(chatbot):
    """הצג ממשק הצ'אט המלא"""
    st.header("💬 שיחה עם העוזר המשפטי ללא הגבלות")
    
    # אתחל היסטוריה
    initialize_chat_history()
    
    # הצג הודעות קיימות
    display_chat_messages()
    
    # טפל במשימות מקיפות (על בסיס סיכומים)
    handle_comprehensive_tasks(chatbot)
    
    # טפל בשאלות מהירות (על הטקסט הגולמי)
    handle_quick_questions(chatbot)
    
    # טפל בקלט משתמש חדש
    handle_user_input(chatbot)


def clear_chat_history():
    """נקה היסטוריית צ'אט"""
    if st.button("🗑️ נקה היסטוריית צ'אט"):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": UI_MESSAGES["welcome"]
            }
        ]
        st.rerun()
