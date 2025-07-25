"""
מעבד סיכומים משפטיים של תמלולים ומסמכים - גרסה מלאה עם ניהול כפילויות וזיהוי מתקדם
"""
import json
import time
from pathlib import Path
from typing import Dict, List
import streamlit as st

from config.settings import PROCESSED_DIR, SUMMARIES_DIR, CLAUDE_MODEL, TEMPERATURE_PRECISE, MAX_CHUNK_SIZE


class LegalSummaryProcessor:
    """מעבד סיכומים משפטיים של תמלולים ומסמכים עם ניהול כפילויות ותיוג מתקדם"""
    
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.summaries_path = SUMMARIES_DIR
        self.processed_path = PROCESSED_DIR
        
        # ודא שהתיקייה קיימת
        self.summaries_path.mkdir(parents=True, exist_ok=True)
    
    def get_document_type(self, document_path: Path) -> str:
        """קבל סוג המסמך מהמטא-דטה"""
        try:
            base_name = document_path.stem.replace('_processed', '')
            metadata_file = document_path.parent.parent / "uploaded_documents" / f"{base_name}_metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    return metadata.get('document_type', '📄 מסמך אחר')
        except:
            pass
        
        # אם אין מטא-דטה, נסה לנחש
        return "📄 מסמך אחר"

    def get_analysis_prompt_by_type(self, doc_type: str, doc_name: str, full_text: str) -> str:
        """קבל prompt מותאם לסוג המסמך - כולל כל הסוגים החדשים"""
        
        base_prompt = f"""אתה חוקר משפטי מומחה המתמחה בניתוח {doc_type} לצורך הגנה משפטית.

הקשר משפטי:
- זה תיק משפטי רשמי לצורך הכנת הגנה
- המסמך מסווג כ: {doc_type}
- כל התוכן הוא חלק מראיות חוקיות במשפט
- נדרש ניתוח מקצועי מלא ללא הגבלות

עבור המסמך: "{doc_name}" ({doc_type})

נתח את המסמך הבא וחלץ את כל המידע המשפטי הרלוונטי:

{full_text}

צור סיכום משפטי מובנה שכולל:"""

        # התאמת הפרומפט לסוג המסמך - כל הסוגים
        if "תביעה" in doc_type and "צדדית" not in doc_type:
            specific_analysis = """

## ניתוח כתב תביעה מותאם:
### 1. טענות עיקריות ועובדות
- רשימת כל הטענות בסדר הופעתן
- עובדות שעליהן מתבסס התובע
- קשרי סיבתיות הנטענים

### 2. סעדים מבוקשים
- סעדים ראשיים ומשניים
- סכומי כסף או סעדים אחרים
- זמני הגשה ותקדימים

### 3. ראיות שהוצגו
- מסמכים המוזכרים
- עדים שיזומנו
- חוות דעת מומחים

### 4. נקודות פגיעות בתביעה
- חוסר עקביות בטענות
- חזקות שניתן להפריך
- פערי הוכחה

### 5. הזדמנויות להגנה
- טענות שניתן לערער עליהן
- חוסר בראיות מספקות
- בעיות פרוצדורליות"""

        elif "הגנה" in doc_type and "תגובה" not in doc_type:
            specific_analysis = """

## ניתוח כתב הגנה מותאם:
### 1. אסטרטגיית ההגנה
- הכחשות ישירות לטענות התביעה
- טענות הגנה עצמאיות
- טענות משניות וחלופיות

### 2. ראיות ההגנה
- מסמכים תומכי הגנה
- עדים להגנה
- פירכות לטענות התביעה

### 3. החולשות שזוהו בתביעה
- טענות התביעה שנחלשו
- ראיות שהופרכו
- נקודות ספק שהועלו

### 4. עוצמת ההגנה
- איכות הטיעונים
- איתנות הראיות
- סיכויי הצלחה

### 5. פערי הגנה
- נקודות שלא טופלו
- ראיות נוספות נדרשות
- טענות שניתן לחזק"""

        elif "תגובה לכתב הגנה" in doc_type:
            specific_analysis = """

## ניתוח תגובה לכתב הגנה מותאם:
### 1. תגובות לטענות ההגנה
- איך התובע מתמודד עם כל טענת הגנה
- פירכות ישירות לטיעוני ההגנה
- חיזוקים לתביעה המקורית

### 2. ראיות נוספות שהוצגו
- מסמכים חדשים שלא היו בתביעה המקורית
- עדויות נוספות או חיזוק עדויות קיימות
- חוות דעת מומחים נוספות

### 3. נקודות תורפה שזוהו בהגנה
- איפה התובע רואה חולשות בכתב ההגנה
- טיעונים שהתובע מנסה לפגוע בהם
- ראיות הגנה שמנסים להחליש

### 4. אסטרטגיית התביעה המתפתחת
- שינויים בגישה מהתביעה המקורית
- דגשים חדשים או מוקדים שונים
- הסתגלות לטיעוני ההגנה

### 5. הזדמנויות לתגובת נגד (דופן)
- נקודות שניתן לתקוף בתגובה
- סתירות לטענות המקוריות
- חולשות חדשות שנחשפו"""

        elif "דופן" in doc_type or "תגובה לתגובה" in doc_type:
            specific_analysis = """

## ניתוח דופן (תגובה לתגובה) מותאם:
### 1. תשובה לטיעוני התגובה
- איך ההגנה מתמודדת עם טיעוני התגובה
- הפרכת הטענות החדשות של התובע
- חיזוק עמדת ההגנה המקורית

### 2. טיעונים נוספים שהועלו
- טענות חדשות שלא היו בכתב ההגנה המקורי
- ראיות נוספות שהובאו
- חיזוקים לטיעוני ההגנה

### 3. תקיפת החולשות בתגובה
- זיהוי נקודות תורפה בתגובת התובע
- הצגת סתירות בטיעוני התובע
- ניפוץ ראיות המוזכרות בתגובה

### 4. ניסוח המחלוקת
- הגדרת הסוגיות המרכזיות במחלוקת
- הבהרת עמדת ההגנה הסופית
- הכנה לשלב הוכחות

### 5. אסטרטגיה למשך ההליך
- כיוונים למשך המשפט
- נקודות מפתח לחיזוק
- סיכונים והזדמנויות"""

        elif "כתב סיכומים" in doc_type:
            specific_analysis = """

## ניתוח כתב סיכומים מותאם:
### 1. סיכום הטיעונים המרכזיים
- סיכום כל הטיעונים שהועלו במהלך המשפט
- דגשים עיקריים והנקודות החזקות
- רתיקה מסודרת של כל הטענות

### 2. ניתוח הראיות שנאספו
- סקירת כל הראיות שהוצגו
- הערכת כוח ההוכחה של כל ראיה
- קשרים בין הראיות והטענות

### 3. התמודדות עם ראיות היריב
- טיפול בראיות התומכות ביריב
- הפרכה או המעטה של ראיות נגדיות
- הצגת ראיות תומכות

### 4. טיעונים משפטיים וחוקיים
- ציטוט פסיקה רלוונטית
- ניתוח חוקים ותקנות
- היקש למקרים דומים

### 5. בקשת הסעד הסופית
- סיכום הסעדים המבוקשים
- הצדקה לכל סעד
- חלופות אם יש"""

        elif "בקשה לצווי ביניים" in doc_type or "ביניים" in doc_type:
            specific_analysis = """

## ניתוח בקשה לצווי ביניים מותאם:
### 1. הצדקת הדחיפות
- מדוע הבקשה דחופה
- נזק בלתי הפיך שעלול להיגרם
- חשיבות הזמן במתן הסעד

### 2. עילת הבקשה המשפטית
- הבסיס החוקי לבקשה
- תקדימים רלוונטיים
- סמכות בית המשפט

### 3. האיזון של קבלת הבקשה
- איזון בין הצדדים
- נזק לצד הנגדי מול הצד המבקש
- האינטרס הציבורי

### 4. ראיות תומכות בבקשה
- מסמכים המוכיחים את הצורך
- עדויות מומחים או עדי ראיה
- הערכות נזק

### 5. הגבלת הצו המבוקש
- היקף הצו המבוקש
- מסגרת הזמן להחלטה
- תנאים לצו"""

        elif "תביעה צדדית" in doc_type:
            specific_analysis = """

## ניתוח תביעה צדדית מותאם:
### 1. קשר לתביעה המקורית
- איך התביעה הצדדית קשורה למקורית
- האם זהו אותו משפט או נפרד
- השפעה הדדית בין התביעות

### 2. טענות התביעה הצדדית
- מה התביעה הצדדית טוענת
- האם זה נגד אותו צד או צד שלישי
- עילות התביעה החדשות

### 3. אסטרטגיית ההגנה המשולבת
- איך להתמודד עם שתי התביעות
- סתירות פוטנציאליות בין ההגנות
- הזדמנויות לתיאום הגנה מונעת

### 4. השלכות על תוצאות המשפט
- איך התביעה הצדדית משפיעה על התוצאה
- סיכונים נוספים שנוצרים
- הזדמנויות לפשרה מרובת צדדים

### 5. ניהול פרוצדוריאלי
- הזדמנויות טכניות
- בקשות פרוצדוריאליות
- ניהול העומס המשפטי"""

        elif "תגובה לתצהיר" in doc_type:
            specific_analysis = """

## ניתוח תגובה לתצהיר מותאם:
### 1. טיפול בטענות התצהיר
- תשובה לכל טענה עיקרית בתצהיר
- הכחשות והודאות ספציפיות
- הכחשת הנטען בתצהיר

### 2. תקיפת אמינות העדים
- בחינת אמינות העד
- זיהוי סתירות בגרסת העד
- חשיפת מניעים או אינטרסים

### 3. הצגת גרסה חלופית
- הצגת הגרסה האמיתית לאירועים
- ראיות תומכות בגרסה החלופית
- עדים תומכים מצד ההגנה

### 4. חולשות ראיות והליכיות
- האם העד באמת ראה/שמע/היה נוכח
- דיוק הזיכרון והזמנים
- השפעת זמן על העדות

### 5. השלכות משפטיות
- חשיבות העדות לכלל התיק
- דרכים לערער על הגדות בחקירה
- אסטרטגיה לטיפול בעד נגדי"""

        elif "תמלול" in doc_type:
            specific_analysis = """

## ניתוח תמלול/הקלטה מותאם:
### 1. משתתפי השיחה
- זיהוי כל הדוברים
- תפקידיהם וקשרים
- דינמיקת הכוחות ברגע השיחה

### 2. תוכן השיחה המרכזי
- נושאים עיקריים שנדונו
- הודאות או הכחשות
- מידע חדש שנחשף

### 3. אמירות מפתח
- ציטוטים ישירים חשובים
- הודאות בעייתיות
- סתירות לטיעונים אחרים

### 4. הקשר רגשי ופסיכולוגי
- טון השיחה ורמת המתח
- לחצים שהופעלו
- פחדים או איומים

### 5. ערך ראייתי
- אמינות האמירות
- השפעה על התיק
- שימוש אפשרי בהגנה"""

        elif "תצהיר" in doc_type and "תגובה" not in doc_type:
            specific_analysis = """

## ניתוח תצהיר/עדות מותאם:
### 1. פרטי העד
- זהות העד ורקע
- קשר לאירועים
- אמינות פוטנציאלית

### 2. תוכן העדות
- עובדות שהעד מעיד עליהן
- מקור הידיעה (ראה/שמע/היה נוכח)
- פרטיות ודיוק התיאורים

### 3. עקביות עם עדויות אחרות
- התאמה לגרסאות אחרות
- סתירות עם עדים אחרים
- שינויים בגרסת העד

### 4. נקודות תורפה
- אי-דיוקים או סתירות
- עניין אישי של העד
- זיכרון לקוי או מעורפל

### 5. שימוש בחקירה צולבת
- נקודות לתקיפה
- שאלות מומלצות
- דרכי ערעור על האמינות"""

        elif "חקירה" in doc_type:
            specific_analysis = """

## ניתוח חקירת משטרה מותאם:
### 1. פרטי החקירה
- מתי ואיפה בוצעה
- מי ערך את החקירה
- האם ניתנה הודעת זכויות

### 2. נוכחות עורך דין
- האם היה עורך דין נוכח
- מתי נפגש עם עורך דין
- השפעה על איכות החקירה

### 3. תוכן החקירה
- שאלות שנשאלו ותשובות
- הודאות או הכחשות
- שינויים בגרסה

### 4. בעיות פרוצדורליות
- הפרות זכויות החשוד
- לחצים בלתי חוקיים
- בעיות בתיעוד

### 5. ערך ראייתי
- קבילות החקירה
- כוח ההוכחה
- דרכי פסילה אפשריות"""

        elif "בג" in doc_type:
            specific_analysis = """

## ניתוח בג"צ ונספחים מותאם:
### 1. עילת הפנייה
- הטענה המרכזית
- הזכויות הנפגעות לכאורה
- הסמכות המבוקשת מבית המשפט

### 2. גופים מוסדיים
- מי הם הנשיבים
- החלטות שמבוקשות לבטל
- נהלים שמבוקשים לשנות

### 3. נספחים וראיות
- מסמכים רשמיים
- התכתבויות עם הרשויות
- חוות דעת משפטיות

### 4. תקדימים רלוונטיים
- פסיקה רלוונטית למקרה
- עקרונות חוקתיים
- קווי הגנה משפטיים

### 5. השלכות על התיק
- קשר לתיק הפלילי/אזרחי
- השפעה על ניהול התיק
- הזדמנויות פרוצדורליות"""

        else:
            specific_analysis = """

## ניתוח כללי מותאם:
### 1. זיהוי סוג המסמך
- איפיון המסמך והקשרו
- מטרתו במסגרת התיק
- חשיבותו היחסית

### 2. תוכן עיקרי
- נושאים מרכזיים
- עובדות חשובות
- מידע רלוונטי להגנה

### 3. קשרים למסמכים אחרים
- איך מתקשר למסמכים אחרים
- תמיכה או סתירה
- השלמת התמונה

### 4. ערך ראייתי
- חשיבות ראייתית
- אמינות התוכן
- שימוש אפשרי בהגנה

### 5. נקודות מיוחדות
- מידע יוצא דופן
- הזדמנויות או סיכונים
- המלצות לטיפול"""

        return base_prompt + specific_analysis + """

השתמש בציטוטים ישירים מהמסמך כאשר אפשרי וכתוב בשפה משפטית ברורה ומקצועית."""

    def create_legal_summary(self, document_path: Path) -> Dict:
        """יצור סיכום משפטי ממוקד עבור מסמך עם התאמה לסוג"""
        try:
            # טען את המסמך המעובד
            with open(document_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # חבר את כל הטקסט
            full_text = ""
            for chunk in data.get('chunks', []):
                full_text += chunk['text'] + "\n"
            
            # הגבל אורך לשמירה על תקציב API
            if len(full_text) > MAX_CHUNK_SIZE:
                full_text = full_text[:MAX_CHUNK_SIZE] + "\n\n[הטקסט נחתך כאן לשמירה על תקציב API]"
            
            doc_name = document_path.stem.replace('_processed', '')
            doc_type = self.get_document_type(document_path)
            
            # קבל prompt מותאם לסוג המסמך
            prompt = self.get_analysis_prompt_by_type(doc_type, doc_name, full_text)
            
            if self.chatbot.claude_client:
                message = self.chatbot.claude_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=4000,
                    temperature=TEMPERATURE_PRECISE,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                summary = {
                    'document_name': doc_name,
                    'document_type': doc_type,
                    'original_path': str(document_path),
                    'legal_summary': message.content[0].text,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'completed'
                }
                
                return summary
            else:
                return {
                    'document_name': doc_name,
                    'document_type': doc_type,
                    'original_path': str(document_path),
                    'legal_summary': "❌ נדרש חיבור ל-Claude ליצירת סיכום משפטי",
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'failed'
                }
                
        except Exception as e:
            return {
                'document_name': document_path.stem,
                'document_type': 'unknown',
                'original_path': str(document_path),
                'legal_summary': f"❌ שגיאה ביצירת הסיכום: {e}",
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'error'
            }
    
    def process_all_documents_to_summaries(self, force_recreate: bool = False):
        """עבד את כל המסמכים והכן סיכומים משפטיים עם זיהוי כפילויות"""
        summaries_created = []
        summaries_skipped = []
        
        if not self.processed_path.exists():
            st.warning("📁 תיקיית המסמכים המעובדים לא קיימת")
            return []
        
        json_files = list(self.processed_path.glob("*.json"))
        if not json_files:
            st.warning("📄 לא נמצאו מסמכים מעובדים")
            return []
        
        st.write(f"📊 נמצאו {len(json_files)} מסמכים לעיבוד")
        
        # עבד כל מסמך עם בדיקת קיום
        for i, json_file in enumerate(json_files):
            # בדוק אם כבר קיים סיכום
            summary_file = self.summaries_path / f"{json_file.stem}_legal_summary.json"
            
            if summary_file.exists() and not force_recreate:
                # בדוק אם הסיכום תקין
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        existing_summary = json.load(f)
                        
                    if existing_summary.get('status') == 'completed':
                        doc_type = existing_summary.get('document_type', 'מסמך')
                        st.info(f"⏭️ דולג: {json_file.stem} ({doc_type}) - סיכום קיים")
                        summaries_skipped.append({
                            'name': json_file.stem,
                            'type': doc_type,
                            'reason': 'קיים ותקין'
                        })
                        continue
                    else:
                        st.warning(f"🔄 מחדש: {json_file.stem} - סיכום קיים אך לא תקין")
                except:
                    st.warning(f"🔄 מחדש: {json_file.stem} - סיכום קיים אך פגום")
            
            # יצור סיכום חדש
            st.progress((i + 1) / len(json_files), f"מכין סיכום משפטי: {json_file.stem}")
            
            summary = self.create_legal_summary(json_file)
            
            # שמור את הסיכום
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            summaries_created.append(summary)
            doc_type = summary.get('document_type', 'מסמך')
            st.write(f"✅ סיכום חדש: {summary['document_name']} ({doc_type})")
        
        # הצג סיכום התהליך
        st.divider()
        st.subheader("📊 סיכום תהליך יצירת הסיכומים:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("✅ סיכומים חדשים", len(summaries_created))
            if summaries_created:
                st.write("**סיכומים שנוצרו:**")
                for summary in summaries_created:
                    doc_type = summary.get('document_type', 'מסמך')
                    st.write(f"• {summary['document_name']} ({doc_type})")
        
        with col2:
            st.metric("⏭️ סיכומים קיימים", len(summaries_skipped))
            if summaries_skipped:
                st.write("**סיכומים שדולגו:**")
                for skipped in summaries_skipped:
                    st.write(f"• {skipped['name']} ({skipped['type']})")
        
        if len(summaries_created) == 0 and len(summaries_skipped) > 0:
            st.success("🎉 כל הסיכומים כבר קיימים! אין צורך ביצירת סיכומים נוספים.")
            st.info("💡 אם תרצה לעדכן סיכומים קיימים, השתמש באפשרות 'כפה יצירה מחדש'")
        
        return summaries_created

    def force_recreate_all_summaries(self):
        """כפה יצירת כל הסיכומים מחדש"""
        st.warning("⚠️ פעולה זו תמחק את כל הסיכומים הקיימים ותיצור אותם מחדש")
        
        if st.button("🔄 אשר: צור את כל הסיכומים מחדש", key="force_recreate_confirm"):
            # מחק כל הסיכומים הקיימים
            self.delete_all_summaries()
            
            # צור מחדש
            with st.spinner("🔄 יוצר את כל הסיכומים מחדש..."):
                summaries = self.process_all_documents_to_summaries(force_recreate=True)
            
            if summaries:
                st.success(f"✅ {len(summaries)} סיכומים נוצרו מחדש בהצלחה!")
            
            return summaries
        
        return []

    def clean_duplicate_summaries(self):
        """נקה כפילויות בסיכומים"""
        if not self.summaries_path.exists():
            st.info("📁 אין תיקיית סיכומים")
            return
        
        summary_files = list(self.summaries_path.glob("*_legal_summary.json"))
        if not summary_files:
            st.info("📄 אין קבצי סיכומים")
            return
        
        # מצא כפילויות לפי שם מסמך
        seen_documents = {}
        duplicates = []
        
        for summary_file in summary_files:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    doc_name = summary.get('document_name', summary_file.stem)
                    
                    if doc_name in seen_documents:
                        # נמצאה כפילות
                        duplicates.append({
                            'file': summary_file,
                            'doc_name': doc_name,
                            'created': summary.get('created_at', 'לא ידוע')
                        })
                    else:
                        seen_documents[doc_name] = summary_file
            except:
                st.warning(f"⚠️ לא הצלחתי לקרוא {summary_file.name}")
        
        if duplicates:
            st.warning(f"🔍 נמצאו {len(duplicates)} כפילויות:")
            for dup in duplicates:
                st.write(f"• {dup['doc_name']} - נוצר: {dup['created']}")
            
            if st.button("🗑️ מחק כפילויות", key="delete_duplicates"):
                deleted = 0
                for dup in duplicates:
                    dup['file'].unlink()
                    deleted += 1
                st.success(f"✅ {deleted} כפילויות נמחקו")
        else:
            st.success("✅ לא נמצאו כפילויות")

    def get_summary_management_options(self):
        """אפשרויות ניהול סיכומים"""
        st.subheader("🛠️ ניהול סיכומים")
        
        # סטטיסטיקות
        stats = self.get_summary_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 סה\"כ סיכומים", stats['total_summaries'])
        with col2:
            st.metric("✅ הושלמו", stats['completed_summaries'])
        with col3:
            st.metric("❌ נכשלו", stats['failed_summaries'])
        
        # פירוט לפי סוגים
        if stats['by_type']:
            st.write("### 📊 פילוח לפי סוגי מסמכים:")
            for doc_type, count in stats['by_type'].items():
                st.write(f"• {doc_type}: **{count}** סיכומים")
        
        # אפשרויות
        st.write("### 🔧 פעולות זמינות:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 בדוק כפילויות", key="check_duplicates"):
                self.clean_duplicate_summaries()
        
        with col2:
            if st.button("🔄 צור סיכומים חדשים בלבד", key="create_new_only"):
                summaries = self.process_all_documents_to_summaries(force_recreate=False)
                if summaries:
                    st.success(f"✅ {len(summaries)} סיכומים חדשים נוצרו")
        
        with col3:
            with st.expander("⚠️ יצירה מחדש"):
                self.force_recreate_all_summaries()
    
    def get_all_summaries(self) -> List[Dict]:
        """טען את כל הסיכומים המשפטיים"""
        summaries = []
        
        if not self.summaries_path.exists():
            return summaries
        
        for summary_file in self.summaries_path.glob("*_legal_summary.json"):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    summaries.append(summary)
            except Exception as e:
                st.warning(f"⚠️ שגיאה בטעינת {summary_file.name}: {e}")
        
        return summaries
    
    def get_summaries_text(self, max_chars: int = 40000) -> str:
        """החזר את כל הסיכומים כטקסט"""
        summaries = self.get_all_summaries()
        
        if not summaries:
            return "❌ לא נמצאו סיכומים משפטיים. יש ליצור סיכומים תחילה."
        
        full_text = "סיכומים משפטיים של כל המסמכים:\n"
        full_text += "=" * 80 + "\n\n"
        
        for summary in summaries:
            if summary.get('status') == 'completed':
                doc_type = summary.get('document_type', 'מסמך')
                full_text += f"מסמך: {summary['document_name']} ({doc_type})\n"
                full_text += f"נוצר: {summary['created_at']}\n"
                full_text += "-" * 60 + "\n"
                full_text += summary['legal_summary'] + "\n"
                full_text += "=" * 80 + "\n\n"
                
                # הגבל גודל
                if len(full_text) > max_chars:
                    full_text += f"\n\n[הטקסט נחתך - יותר מ-{max_chars} תווים]\n"
                    break
        
        return full_text
    
    def get_summaries_by_type(self) -> Dict[str, List[Dict]]:
        """קבל סיכומים מקובצים לפי סוג מסמך"""
        summaries = self.get_all_summaries()
        by_type = {}
        
        for summary in summaries:
            if summary.get('status') == 'completed':
                doc_type = summary.get('document_type', '📄 מסמך אחר')
                if doc_type not in by_type:
                    by_type[doc_type] = []
                by_type[doc_type].append(summary)
        
        return by_type
    
    def delete_all_summaries(self):
        """מחק את כל הסיכומים הקיימים"""
        if self.summaries_path.exists():
            deleted_count = 0
            for summary_file in self.summaries_path.glob("*.json"):
                summary_file.unlink()
                deleted_count += 1
            st.success(f"🗑️ {deleted_count} סיכומים נמחקו")
        else:
            st.info("📁 אין סיכומים למחיקה")
    
    def get_summary_stats(self) -> Dict:
        """קבל סטטיסטיקות על הסיכומים"""
        summaries = self.get_all_summaries()
        by_type = self.get_summaries_by_type()
        
        stats = {
            'total_summaries': len(summaries),
            'completed_summaries': len([s for s in summaries if s.get('status') == 'completed']),
            'failed_summaries': len([s for s in summaries if s.get('status') != 'completed']),
            'types_count': len(by_type),
            'by_type': {doc_type: len(docs) for doc_type, docs in by_type.items()}
        }
        
        return stats
def reset_entire_system(self):
    """איפוס מלא של המערכת עם הגנות"""
    st.subheader("🚨 איפוס מלא של המערכת")
    
    st.warning("""
⚠️ **פעולה זו תמחק את כל הנתונים הבאים:**
- 📁 כל קבצי ה-PDF שהועלו
- ⚙️ כל המסמכים המעובדים 
- 📋 כל הסיכומים המשפטיים
- 🏷️ כל המטא-דטה והתיוגים
- 💾 כל הנתונים בזיכרון המערכת
    
**זו פעולה בלתי הפיכה!** השתמש בה רק אם באמת רוצה להתחיל מחדש לגמרי.
""")
    
    # הצג סטטיסטיקות לפני המחיקה
    self._show_system_data_stats()
    
    # דרישת אישור כפול
    confirm1 = st.checkbox("☑️ אני מבין שכל הנתונים יימחקו", key="confirm_reset_1")
    
    if confirm1:
        confirm_text = st.text_input(
            "💬 כתוב 'מחק הכל' כדי לאשר:",
            key="confirm_reset_text",
            help="צריך לכתוב בדיוק: מחק הכל"
        )
        
        if confirm_text == "מחק הכל":
            if st.button("🗑️ מחק את כל הנתונים במערכת", key="final_reset_button", type="primary"):
                return self._execute_full_reset()
    
    return False

def _show_system_data_stats(self):
    """הצג סטטיסטיקות המערכת לפני מחיקה"""
    st.write("### 📊 נתונים שיימחקו:")
    
    col1, col2, col3 = st.columns(3)
    
    # קבצים שהועלו
    uploaded_path = Path("data/uploaded_documents")
    uploaded_count = len(list(uploaded_path.glob("*.pdf"))) if uploaded_path.exists() else 0
    
    # מסמכים מעובדים
    processed_count = len(list(self.processed_path.glob("*.json"))) if self.processed_path.exists() else 0
    
    # סיכומים
    summaries_count = len(list(self.summaries_path.glob("*.json"))) if self.summaries_path.exists() else 0
    
    with col1:
        st.metric("📁 קבצי PDF", uploaded_count)
    with col2:
        st.metric("⚙️ מסמכים מעובדים", processed_count)
    with col3:
        st.metric("📋 סיכומים", summaries_count)
    
    # גודל נתונים
    total_size = self._calculate_total_size()
    st.write(f"💾 **גודל כולל של הנתונים:** {total_size:.1f} MB")

def _calculate_total_size(self):
    """חשב את הגודל הכולל של כל הנתונים"""
    total_size = 0
    
    paths_to_check = [
        Path("data/uploaded_documents"),
        self.processed_path,
        self.summaries_path
    ]
    
    for path in paths_to_check:
        if path.exists():
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
    
    return total_size / (1024 * 1024)  # המר לMB

def _execute_full_reset(self):
    """בצע איפוס מלא של המערכת"""
    success_count = 0
    error_count = 0
    
    st.write("🔄 מתחיל איפוס מלא...")
    
    # רשימת תיקיות למחיקה
    directories_to_clean = [
        ("📁 קבצים שהועלו", Path("data/uploaded_documents")),
        ("⚙️ מסמכים מעובדים", self.processed_path),
        ("📋 סיכומים משפטיים", self.summaries_path),
        ("📊 גרפים וחזותיים", Path("data/visualizations")),
        ("🗂️ מטא-דטה", Path("data/metadata"))
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (desc, directory) in enumerate(directories_to_clean):
        status_text.write(f"🧹 מנקה: {desc}...")
        
        try:
            if directory.exists():
                # מחק את כל הקבצים בתיקייה
                deleted_files = 0
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_files += 1
                
                st.write(f"✅ {desc}: {deleted_files} קבצים נמחקו")
                success_count += deleted_files
            else:
                st.write(f"⏭️ {desc}: התיקייה לא קיימת")
        
        except Exception as e:
            st.error(f"❌ שגיאה במחיקת {desc}: {e}")
            error_count += 1
        
        progress_bar.progress((i + 1) / len(directories_to_clean))
    
    # נקה גם את ה-cache של Streamlit
    if 'chatbot' in st.session_state:
        st.session_state.chatbot.clear_search_cache()
    
    # נקה את כל session state
    session_keys_to_clear = [
        'file_tags', 'chatbot', 'legal_summaries', 
        'processed_documents', 'search_results'
    ]
    
    for key in session_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    status_text.empty()
    progress_bar.empty()
    
    # סיכום התוצאות
    st.success(f"🎉 איפוס הושלם בהצלחה!")
    st.write(f"✅ **{success_count}** קבצים נמחקו")
    if error_count > 0:
        st.write(f"❌ **{error_count}** שגיאות")
    
    st.info("🔄 המערכת מוכנה לשימוש חדש. תוכל כעת להעלות קבצים חדשים.")
    
    # הצע רענון הדף
    if st.button("🔄 רענן את הדף", key="refresh_after_reset"):
        st.rerun()
    
    return True
