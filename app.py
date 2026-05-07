import json
import os
import shutil
import socket
import sqlite3
import stat
from difflib import get_close_matches
from datetime import datetime
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
ENV_FILE = BASE_DIR / ".env"
DEFAULT_MANDI_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
CROP_OPTIONS = [
    "Soybean",
    "Cotton",
    "Wheat",
    "Rice",
    "Maize",
    "Tomato",
    "Onion",
    "Potato",
    "Sugarcane",
    "Groundnut",
    "Brinjal",
    "Cabbage",
    "Chilli",
    "Turmeric",
    "Grapes",
    "Pomegranate",
    "Banana",
    "Mango",
    "Bajra",
    "Jowar",
    "Tur",
    "Moong",
    "Urad",
    "Gram",
]
LANGUAGE_OPTIONS = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}
TRANSLATIONS = {
    "en": {
        "smart_agriculture_platform": "VGROW PLATFORM",
        "dashboard": "Dashboard",
        "expert": "Expert",
        "admin": "Admin",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",
        "create_account": "Create account",
        "name": "Name",
        "email": "Email",
        "password": "Password",
        "role": "Role",
        "state": "State",
        "district": "District",
        "village": "Village",
        "crops": "Crops",
        "select_state": "Select state",
        "select_district": "Select district",
        "select_village": "Select village",
        "select_crop": "Select crop",
        "farmer": "Farmer",
        "create_account_cta": "Create account",
        "use_demo_account": "Use demo account",
        "smarter_farming_title": "KRUSHIGOLD.AI for smarter farming decisions.",
        "smarter_farming_copy": "Includes login/register, farmer dashboard, expert panel, admin panel, live weather, local mandi rates, AI crop guidance, crop reports, notifications, GPS search, voice chat, and SQLite storage.",
        "password_label": "Password",
        "welcome_back": "Welcome back.",
        "login_title": "Login",
        "language": "Language",
        "save_language": "Save language",
        "language_updated": "Language updated.",
        "farmer_dashboard": "Farmer Dashboard",
        "farmer_profile_line": "{role} profile for {village}, {district}, {state} | Crops: {crops}",
        "farmer_information": "Farmer Information",
        "login_profile": "Login profile",
        "location": "Location",
        "preferences": "Preferences",
        "crop_details": "Crop Details",
        "saved_location": "Saved location",
        "weather_and_gps": "Weather and GPS",
        "weather_api": "Weather API",
        "mandi_api": "Mandi API",
        "openai_label": "OpenAI",
        "refresh_weather": "Refresh weather",
        "showing_weather_for": "Showing weather for:",
        "soil": "Soil",
        "humidity": "Humidity",
        "wind": "Wind",
        "soil_moisture": "Soil Moisture",
        "market_rate_and_notifications": "Market Rate and Notifications",
        "stored_api": "Stored + API",
        "search_local_mandi": "Search local mandi",
        "local_mandi_area": "Local mandi area:",
        "selected_crop": "Selected crop:",
        "available_mandi_markets": "Available mandi markets in this district:",
        "no_mandi_rate": "No mandi rate found for this state, district, and crop selection.",
        "notifications": "Notifications",
        "no_notifications": "No notifications yet.",
        "crop_advisory": "Crop Advisory",
        "select_crop_advisory": "Select crop advisory",
        "load_advisory": "Load advisory",
        "guidance": "Guidance",
        "fertilizer": "Fertilizer",
        "pesticide": "Pesticide",
        "ai_crop_advisor_voice_support": "AI Crop Advisor and Voice Support",
        "live_ai_hook": "Live AI hook",
        "crop_focus": "Crop focus",
        "question": "Question",
        "question_placeholder": "Ask about pests, fertilizer, rainfall, or disease.",
        "start_voice_chat": "Start voice chat",
        "voice_chat_hint": "Tap the voice chat button and speak your question.",
        "voice_chat_not_supported": "Voice chat is not supported in this browser.",
        "voice_chat_listening": "Listening now. Speak your farming question.",
        "voice_question_added": "Voice question added. You can review it and ask AI.",
        "voice_chat_listening_button": "Listening...",
        "voice_chat_error": "Voice chat could not start",
        "ask_ai": "Ask AI",
        "ai_reply": "AI reply",
        "ai_system_prompt": "You are an agriculture assistant for Indian farmers. Reply in clear, simple {language_name} that a farmer can understand easily. Give practical step-by-step guidance, explain the reason in plain words, and keep the advice safety-minded.",
        "ai_pest_reply": "First inspect the field properly before using any chemical spray. Check both sides of the leaves, count how many plants are affected, and see whether the pest attack is light, medium, or severe. Start with safer control methods like yellow sticky traps, pheromone traps, removing badly affected leaves, and keeping the field clean. If the attack is still increasing, then choose a suitable pesticide as per the crop stage and label dose. Do not spray more than needed, and avoid mixing chemicals without expert advice.",
        "ai_nutrient_reply": "For {crop}, fertilizer should not be applied only by guess. First think about three things: soil test result, crop growth stage, and moisture in the field. If the soil is dry, fertilizer may not dissolve well and the plant may not use it properly, so apply when there is enough moisture or after light irrigation. Give the main dose in split applications instead of all at once, because that improves nutrient use and reduces waste. If leaves are pale or growth is weak, check whether nitrogen, potash, or micronutrients are needed, but avoid extra fertilizer without checking because too much fertilizer can increase cost and also harm the crop.",
        "ai_weather_reply": "Rain may come soon, so do not do immediate spraying now. If you spray just before rain, the medicine may wash away and your money and effort can be wasted. First check field drainage so water does not stay in one place and damage roots. If fertilizer or pesticide application is planned, wait until the weather becomes stable. Also watch for humidity after rain, because high moisture can increase disease and pest problems in many crops.",
        "multi_language_support": "Multi-language support",
        "detected_language": "Detected language",
        "original_text": "Original text",
        "translated_question": "Translated question",
        "translation_service_unavailable": "Translation service is not configured yet. Add SARVAM_API_KEY in .env to enable live translations.",
        "header_copy": "Empowering Farmers, Digitally",
        "landing_pill": "Smart support for every farm day",
        "landing_title": "One field-ready platform for weather, mandi intelligence, AI crop support, and farmer collaboration.",
        "landing_copy": "KRUSHIGOLD.AI helps farmers track weather, monitor mandi prices, ask crop questions, detect disease symptoms, and stay connected with experts and community updates.",
        "showcase_productivity": "Improve Productivity",
        "showcase_productivity_title": "Live village weather, soil moisture, and advisory flow",
        "showcase_productivity_copy": "Make spray and irrigation decisions faster with one dashboard view.",
        "showcase_market": "Stay Market Ready",
        "showcase_market_title": "Mandi rates, notifications, and crop updates",
        "showcase_market_copy": "Bring pricing context and field alerts into the same daily workflow.",
        "showcase_community": "Learn Together",
        "showcase_community_title": "Community questions, expert replies, and disease logs",
        "showcase_community_copy": "Turn scattered field problems into shared learning for every farmer.",
        "feature_news_title": "Keep support programs visible",
        "feature_news_copy": "Use admin notifications to publish subsidy reminders, scheme updates, and local advisories so they are not lost in conversation.",
        "feature_weather_title": "Reduce risk before acting",
        "feature_weather_copy": "Forecast cards, temperature, humidity, wind, and soil hints make timing decisions easier before irrigation or spraying.",
        "feature_roles": "Role-Based Workflow",
        "feature_roles_title": "Farmer, expert, and admin in one app",
        "feature_roles_copy": "Demo accounts are ready for each role so the full flow is visible without extra setup.",
        "quick_access": "Quick Access",
        "ready_to_use": "Ready to use",
        "built_for_real_farm_work": "Built for real farm work",
        "built_for_real_farm_work_copy": "Use the platform to check conditions, review local markets, follow crop guidance, save field reports, and keep communication active across farmers, experts, and admins.",
        "welcome_back_eyebrow": "Welcome Back",
        "login_copy": "Sign in to continue with weather alerts, mandi tracking, AI crop guidance, and your farmer community workspace.",
        "register_eyebrow": "Create Your Farming Profile",
        "register_copy": "Set your role, location, and crop focus so the dashboard can show relevant weather, mandi, and crop support information.",
        "farm_operations_dashboard": "Farm operations dashboard",
        "live": "Live",
        "demo": "Demo",
        "farm_overview": "Farm Overview",
        "daily_summary": "Daily summary",
        "working_snapshot": "Working Snapshot",
        "live_app": "Live app",
        "weather": "Weather",
        "mandi": "Mandi",
        "community": "Community",
        "active_posts": "{count} active posts",
        "translation_english": "English",
        "translation_hindi": "Hindi",
        "weather_updated_for": "Weather updated for {location}.",
        "mandi_updated_for": "Mandi rates updated for {location}{crop_suffix}.",
        "advisory_updated_for": "Advisory updated for {crop}.",
        "similar_post_exists": "This similar post already exists. Please update the title or details.",
        "ai_empty_response": "AI returned an empty response.",
        "overview_weather_note_ready": "Village weather insights ready",
        "overview_market_ready": "{count} updates ready",
        "overview_market_default": "Admin and mandi updates ready",
        "overview_community_ready": "{count} farmer discussions active",
        "overview_community_default": "Start the first farmer discussion",
        "overview_report_ready": "{count} reports reviewed",
        "overview_report_default": "Upload the first field report",
        "overview_weather_body": "Plan irrigation, spraying, and harvest timing with local forecasts and soil moisture hints.",
        "overview_market_body": "Compare mandi movement and keep important alerts visible in one working screen.",
        "overview_community_body": "Ask real field questions, collect replies, and keep local experience flowing between farmers.",
        "overview_report_body": "Capture crop symptoms early and save quick diagnosis notes for follow-up action.",
        "knowledge_weather_fallback": "Weather monitoring active",
        "knowledge_notice_fallback": "Create admin notices for schemes, subsidy reminders, or local alerts.",
        "knowledge_post_fallback": "No community story yet. Farmers can post a real field question here.",
        "knowledge_news_title": "Agriculture News & Government Schemes",
        "knowledge_news_body": "Keep policy updates, subsidy reminders, and government support information in one place for faster farmer access.",
        "knowledge_news_item": "Use admin notifications to publish subsidy deadlines, loan support, or district advisories.",
        "knowledge_weather_title": "Weather Alerts",
        "knowledge_weather_body": "Farm decisions are easier when risk signals are easy to scan before acting in the field.",
        "knowledge_weather_item": "Current weather: {summary}",
        "knowledge_weather_hint": "Forecast cards and soil moisture hints are available in the dashboard below.",
        "knowledge_community_body": "The community feed helps farmers, experts, and admins share field problems and practical solutions in one place.",
        "knowledge_community_item": "Experts and admins can reply directly from the same shared knowledge flow.",
        "ai_unavailable_reply": "AI advice is temporarily unavailable right now. Please check your OpenAI billing/quota or try again later.",
        "ai_missing_key_reply": "OpenAI key is not added yet. Add OPENAI_API_KEY in .env to enable live AI chat.",
        "disease_detection": "Disease Detection and Crop Reports",
        "image_upload_rule_engine": "Image upload + rule engine",
        "symptom": "Symptom",
        "crop_image": "Crop image",
        "save_disease_report": "Save disease report",
        "no_disease_reports": "No disease reports yet.",
        "leaf_spots": "Leaf spots",
        "yellowing": "Yellowing",
        "chewing_holes": "Chewing holes",
        "farmer_community": "Farmer Community",
        "live_community_feed": "Live Community Feed",
        "question_title": "Question title",
        "problem_details": "Problem details",
        "post_question": "Post question",
        "reply": "Reply",
        "reply_placeholder": "Write a reply for this farmer",
        "send_reply": "Send reply",
        "community_post_created": "Community post created.",
        "reply_added": "Reply added.",
        "no_posts": "No community posts yet. Be the first farmer to post a real field question.",
        "expert_panel": "Expert Panel",
        "admin_panel": "Admin Panel",
        "farmer_questions": "Farmer Questions",
        "expert_view": "Expert view",
        "disease_reports": "Disease Reports",
        "review_queue": "Review queue",
        "send_notifications": "Send Notifications",
        "admin_tools": "Admin tools",
        "target_user": "Target user",
        "all_users": "All users",
        "title": "Title",
        "body": "Body",
        "create_notification": "Create notification",
        "users_and_roles": "Users and Roles",
        "users_count": "{count} users",
        "no_location": "No location",
        "notification_history": "Notification History",
        "required_name_email_password": "Name, email, and password are required.",
        "account_created_login_now": "Account created. You can log in now.",
        "email_registered": "That email is already registered.",
        "invalid_credentials": "Invalid email or password.",
        "logged_out": "You have been logged out.",
        "access_denied": "You do not have access to that page.",
        "weather_refresh_error": "Enter village, district, or state to refresh weather.",
        "mandi_refresh_error": "Select state and district to search mandi rates.",
        "disease_report_saved": "Disease report saved.",
        "notification_created": "Notification created.",
    },
    "hi": {
        "smart_agriculture_platform": "VGROW PLATFORM",
        "dashboard": "डैशबोर्ड",
        "expert": "विशेषज्ञ",
        "admin": "एडमिन",
        "logout": "लॉगआउट",
        "login": "लॉगिन",
        "register": "रजिस्टर",
        "create_account": "खाता बनाएं",
        "name": "नाम",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "role": "भूमिका",
        "state": "राज्य",
        "district": "जिला",
        "village": "गांव",
        "crops": "फसलें",
        "select_state": "राज्य चुनें",
        "select_district": "जिला चुनें",
        "select_village": "गांव चुनें",
        "select_crop": "फसल चुनें",
        "farmer": "किसान",
        "create_account_cta": "खाता बनाएं",
        "use_demo_account": "डेमो खाता उपयोग करें",
        "smarter_farming_title": "बेहतर खेती के फैसलों के लिए KRUSHIGOLD.AI",
        "smarter_farming_copy": "इसमें लॉगिन/रजिस्टर, किसान डैशबोर्ड, विशेषज्ञ पैनल, एडमिन पैनल, लाइव मौसम, स्थानीय मंडी दरें, एआई फसल मार्गदर्शन, फसल रिपोर्ट, सूचनाएं, जीपीएस खोज, वॉइस चैट और SQLite स्टोरेज शामिल हैं।",
        "password_label": "पासवर्ड",
        "welcome_back": "फिर से स्वागत है।",
        "login_title": "लॉगिन",
        "language": "भाषा",
        "save_language": "भाषा सहेजें",
        "language_updated": "भाषा अपडेट हो गई।",
        "farmer_dashboard": "किसान डैशबोर्ड",
        "farmer_profile_line": "{role} प्रोफ़ाइल {village}, {district}, {state} | फसलें: {crops}",
        "farmer_information": "किसान जानकारी",
        "login_profile": "लॉगिन प्रोफ़ाइल",
        "location": "स्थान",
        "preferences": "पसंद",
        "crop_details": "फसल विवरण",
        "saved_location": "सहेजा गया स्थान",
        "weather_and_gps": "मौसम और जीपीएस",
        "weather_api": "मौसम API",
        "mandi_api": "मंडी API",
        "openai_label": "OpenAI",
        "refresh_weather": "मौसम अपडेट करें",
        "showing_weather_for": "इसके लिए मौसम दिखाया जा रहा है:",
        "soil": "मिट्टी",
        "humidity": "नमी",
        "wind": "हवा",
        "soil_moisture": "मिट्टी की नमी",
        "market_rate_and_notifications": "मंडी दर और सूचनाएं",
        "stored_api": "संग्रहित + API",
        "search_local_mandi": "स्थानीय मंडी खोजें",
        "local_mandi_area": "स्थानीय मंडी क्षेत्र:",
        "selected_crop": "चयनित फसल:",
        "available_mandi_markets": "इस जिले में उपलब्ध मंडी बाजार:",
        "no_mandi_rate": "इस राज्य, जिले और फसल चयन के लिए कोई मंडी दर नहीं मिली।",
        "notifications": "सूचनाएं",
        "no_notifications": "अभी कोई सूचना नहीं है।",
        "crop_advisory": "फसल सलाह",
        "select_crop_advisory": "फसल सलाह चुनें",
        "load_advisory": "सलाह लोड करें",
        "guidance": "मार्गदर्शन",
        "fertilizer": "उर्वरक",
        "pesticide": "कीटनाशक",
        "ai_crop_advisor_voice_support": "एआई फसल सलाहकार और वॉइस सपोर्ट",
        "live_ai_hook": "लाइव एआई हुक",
        "crop_focus": "फसल फोकस",
        "question": "प्रश्न",
        "question_placeholder": "कीट, उर्वरक, बारिश या रोग के बारे में पूछें।",
        "start_voice_chat": "वॉइस चैट शुरू करें",
        "voice_chat_hint": "वॉइस चैट बटन दबाएं और अपना प्रश्न बोलें।",
        "voice_chat_not_supported": "इस ब्राउज़र में वॉइस चैट समर्थित नहीं है।",
        "voice_chat_listening": "सुन रहा है। अपना खेती का प्रश्न बोलें।",
        "voice_question_added": "वॉइस प्रश्न जोड़ दिया गया है। आप इसे देखकर एआई से पूछ सकते हैं।",
        "voice_chat_listening_button": "सुन रहा है...",
        "voice_chat_error": "वॉइस चैट शुरू नहीं हो सकी",
        "ask_ai": "एआई से पूछें",
        "ai_reply": "एआई जवाब",
        "ai_system_prompt": "आप भारतीय किसानों के लिए कृषि सहायक हैं। साफ़ और आसान {language_name} में ऐसा जवाब दें जिसे किसान आसानी से समझ सके। चरण-दर-चरण उपयोगी सलाह दें, साधारण शब्दों में कारण भी समझाएँ, और सलाह सुरक्षित रखें।",
        "ai_pest_reply": "रासायनिक छिड़काव करने से पहले खेत का ठीक से निरीक्षण करें। पत्तियों के ऊपर और नीचे दोनों तरफ देखें, कितने पौधे प्रभावित हैं यह समझें, और यह जानें कि कीट का प्रकोप कम है, मध्यम है या ज्यादा है। शुरुआत सुरक्षित तरीकों से करें जैसे स्टिकी ट्रैप, फेरोमोन ट्रैप, ज्यादा प्रभावित पत्तियाँ हटाना और खेत को साफ रखना। अगर प्रकोप बढ़ता रहे, तभी फसल की अवस्था और सही मात्रा के अनुसार दवा चुनें। बिना सलाह के दवाओं को मिलाकर छिड़काव न करें।",
        "ai_nutrient_reply": "{crop} के लिए उर्वरक केवल अंदाज़ से नहीं देना चाहिए। तीन बातों को देखें: मिट्टी परीक्षण, फसल की अवस्था और खेत में नमी। अगर मिट्टी बहुत सूखी है तो उर्वरक अच्छी तरह घुल नहीं पाता और पौधा उसका सही उपयोग नहीं कर पाता, इसलिए पर्याप्त नमी या हल्की सिंचाई के बाद देना बेहतर है। पूरी मात्रा एक साथ देने के बजाय भागों में दें, इससे पौधे को पोषण बेहतर मिलता है और खाद की बर्बादी कम होती है। अगर पत्तियाँ फीकी हैं या बढ़वार कमजोर है, तो नाइट्रोजन, पोटाश या सूक्ष्म पोषक तत्व की जरूरत जाँचें, लेकिन बिना जाँच ज्यादा खाद न डालें क्योंकि इससे खर्च बढ़ता है और फसल को नुकसान भी हो सकता है।",
        "ai_weather_reply": "जल्द बारिश आने की संभावना है, इसलिए अभी छिड़काव न करें। अगर बारिश से पहले दवा छिड़क दी जाए तो वह बह सकती है और आपका पैसा व मेहनत दोनों खराब हो सकते हैं। पहले खेत की जल निकासी जांचें ताकि पानी जमा होकर जड़ों को नुकसान न पहुँचाए। अगर खाद या दवा डालने की योजना है, तो मौसम थोड़ा स्थिर होने तक इंतजार करें। बारिश के बाद नमी बढ़ने से कई फसलों में रोग और कीट का खतरा भी बढ़ सकता है, इसलिए खेत पर नजर रखें।",
        "ai_unavailable_reply": "अभी एआई सलाह उपलब्ध नहीं है। कृपया अपनी OpenAI बिलिंग/कोटा जांचें या बाद में फिर प्रयास करें।",
        "ai_missing_key_reply": "OpenAI key अभी जोड़ी नहीं गई है। लाइव AI चैट के लिए .env में OPENAI_API_KEY जोड़ें।",
        "disease_detection": "रोग पहचान और फसल रिपोर्ट",
        "image_upload_rule_engine": "चित्र अपलोड + नियम इंजन",
        "symptom": "लक्षण",
        "crop_image": "फसल की तस्वीर",
        "save_disease_report": "रोग रिपोर्ट सहेजें",
        "no_disease_reports": "अभी कोई रोग रिपोर्ट नहीं है।",
        "leaf_spots": "पत्ती धब्बे",
        "yellowing": "पीलापन",
        "chewing_holes": "चबाने के छेद",
        "farmer_community": "किसान समुदाय",
        "live_community_feed": "लाइव कम्युनिटी फीड",
        "question_title": "प्रश्न शीर्षक",
        "problem_details": "समस्या विवरण",
        "post_question": "प्रश्न पोस्ट करें",
        "reply": "जवाब",
        "reply_placeholder": "इस किसान के लिए जवाब लिखें",
        "send_reply": "जवाब भेजें",
        "community_post_created": "कम्युनिटी पोस्ट बन गई।",
        "reply_added": "जवाब जोड़ दिया गया।",
        "no_posts": "अभी कोई कम्युनिटी पोस्ट नहीं है। सबसे पहले अपना खेत का सवाल पोस्ट करें।",
        "expert_panel": "विशेषज्ञ पैनल",
        "admin_panel": "एडमिन पैनल",
        "farmer_questions": "किसान प्रश्न",
        "expert_view": "विशेषज्ञ दृश्य",
        "disease_reports": "रोग रिपोर्ट",
        "review_queue": "समीक्षा कतार",
        "send_notifications": "सूचनाएं भेजें",
        "admin_tools": "एडमिन टूल्स",
        "target_user": "लक्षित उपयोगकर्ता",
        "all_users": "सभी उपयोगकर्ता",
        "title": "शीर्षक",
        "body": "विवरण",
        "create_notification": "सूचना बनाएं",
        "users_and_roles": "उपयोगकर्ता और भूमिकाएं",
        "users_count": "{count} उपयोगकर्ता",
        "no_location": "कोई स्थान नहीं",
        "notification_history": "सूचना इतिहास",
        "required_name_email_password": "नाम, ईमेल और पासवर्ड आवश्यक हैं।",
        "account_created_login_now": "खाता बन गया। अब आप लॉगिन कर सकते हैं।",
        "email_registered": "यह ईमेल पहले से पंजीकृत है।",
        "invalid_credentials": "अमान्य ईमेल या पासवर्ड।",
        "logged_out": "आप लॉगआउट हो गए हैं।",
        "access_denied": "आपको इस पेज की अनुमति नहीं है।",
        "weather_refresh_error": "मौसम अपडेट करने के लिए गांव, जिला या राज्य दर्ज करें।",
        "mandi_refresh_error": "मंडी दर खोजने के लिए राज्य और जिला चुनें।",
        "disease_report_saved": "रोग रिपोर्ट सहेज दी गई।",
        "notification_created": "सूचना बन गई।",
    },
    "mr": {
        "smart_agriculture_platform": "VGROW PLATFORM",
        "dashboard": "डॅशबोर्ड",
        "expert": "तज्ज्ञ",
        "admin": "अॅडमिन",
        "logout": "लॉगआउट",
        "login": "लॉगिन",
        "register": "नोंदणी",
        "create_account": "खाते तयार करा",
        "name": "नाव",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "role": "भूमिका",
        "state": "राज्य",
        "district": "जिल्हा",
        "village": "गाव",
        "crops": "पिके",
        "select_state": "राज्य निवडा",
        "select_district": "जिल्हा निवडा",
        "select_village": "गाव निवडा",
        "select_crop": "पीक निवडा",
        "farmer": "शेतकरी",
        "create_account_cta": "खाते तयार करा",
        "use_demo_account": "डेमो खाते वापरा",
        "smarter_farming_title": "हुशार शेती निर्णयांसाठी KRUSHIGOLD.AI",
        "smarter_farming_copy": "यात लॉगिन/नोंदणी, शेतकरी डॅशबोर्ड, तज्ज्ञ पॅनेल, अॅडमिन पॅनेल, थेट हवामान, स्थानिक मंडी दर, AI पीक मार्गदर्शन, पीक अहवाल, सूचना, GPS शोध, व्हॉइस चॅट आणि SQLite स्टोरेज आहे.",
        "password_label": "पासवर्ड",
        "welcome_back": "पुन्हा स्वागत आहे.",
        "login_title": "लॉगिन",
        "language": "भाषा",
        "save_language": "भाषा जतन करा",
        "language_updated": "भाषा अपडेट झाली.",
        "farmer_dashboard": "शेतकरी डॅशबोर्ड",
        "farmer_profile_line": "{role} प्रोफाइल {village}, {district}, {state} | पिके: {crops}",
        "farmer_information": "शेतकरी माहिती",
        "login_profile": "लॉगिन प्रोफाइल",
        "location": "स्थान",
        "preferences": "प्राधान्ये",
        "crop_details": "पीक तपशील",
        "saved_location": "जतन केलेले स्थान",
        "weather_and_gps": "हवामान आणि GPS",
        "weather_api": "हवामान API",
        "mandi_api": "मंडी API",
        "openai_label": "OpenAI",
        "refresh_weather": "हवामान रीफ्रेश करा",
        "showing_weather_for": "यासाठी हवामान दाखवत आहोत:",
        "soil": "माती",
        "humidity": "आर्द्रता",
        "wind": "वारा",
        "soil_moisture": "मातीतील ओलावा",
        "market_rate_and_notifications": "मंडी दर आणि सूचना",
        "stored_api": "साठवलेले + API",
        "search_local_mandi": "स्थानिक मंडी शोधा",
        "local_mandi_area": "स्थानिक मंडी क्षेत्र:",
        "selected_crop": "निवडलेले पीक:",
        "available_mandi_markets": "या जिल्ह्यात उपलब्ध मंडी बाजार:",
        "no_mandi_rate": "या राज्य, जिल्हा आणि पीक निवडीसाठी कोणताही मंडी दर सापडला नाही.",
        "notifications": "सूचना",
        "no_notifications": "अजून कोणत्याही सूचना नाहीत.",
        "crop_advisory": "पीक सल्ला",
        "select_crop_advisory": "पीक सल्ला निवडा",
        "load_advisory": "सल्ला लोड करा",
        "guidance": "मार्गदर्शन",
        "fertilizer": "खत",
        "pesticide": "कीटकनाशक",
        "ai_crop_advisor_voice_support": "AI पीक सल्लागार आणि व्हॉइस सपोर्ट",
        "live_ai_hook": "लाईव्ह AI हुक",
        "crop_focus": "पीक फोकस",
        "question": "प्रश्न",
        "question_placeholder": "कीड, खत, पाऊस किंवा रोगाबद्दल विचारा.",
        "start_voice_chat": "व्हॉइस चॅट सुरू करा",
        "voice_chat_hint": "व्हॉइस चॅट बटण दाबा आणि तुमचा प्रश्न बोला.",
        "voice_chat_not_supported": "या ब्राउझरमध्ये व्हॉइस चॅट समर्थित नाही.",
        "voice_chat_listening": "ऐकत आहे. तुमचा शेतीचा प्रश्न बोला.",
        "voice_question_added": "व्हॉइस प्रश्न जोडला गेला. तुम्ही तो पाहून AI ला विचारू शकता.",
        "voice_chat_listening_button": "ऐकत आहे...",
        "voice_chat_error": "व्हॉइस चॅट सुरू होऊ शकली नाही",
        "ask_ai": "AI ला विचारा",
        "ai_reply": "AI उत्तर",
        "ai_system_prompt": "तुम्ही भारतीय शेतकऱ्यांसाठी कृषी सहाय्यक आहात. सोप्या आणि स्पष्ट {language_name} मध्ये असे उत्तर द्या की शेतकऱ्याला ते लगेच समजेल. टप्प्याटप्प्याने उपयोगी मार्गदर्शन द्या, साध्या शब्दांत कारण समजवा, आणि सल्ला सुरक्षित ठेवा.",
        "ai_pest_reply": "रासायनिक फवारणी करण्यापूर्वी शेताची नीट पाहणी करा. पानांच्या वरच्या आणि खालच्या बाजू तपासा, किती झाडे बाधित आहेत ते पाहा, आणि किडीचा प्रादुर्भाव कमी आहे की जास्त हे समजून घ्या. सुरुवात सुरक्षित उपायांनी करा जसे स्टिकी ट्रॅप, फेरोमोन ट्रॅप, जास्त बाधित पाने काढणे आणि शेत स्वच्छ ठेवणे. प्रादुर्भाव वाढत असेल तरच पिकाच्या अवस्थेनुसार आणि योग्य डोसमध्ये औषध वापरा. तज्ज्ञ सल्ल्याशिवाय औषधे मिसळू नका.",
        "ai_nutrient_reply": "{crop} साठी खत फक्त अंदाजाने देऊ नका. तीन गोष्टी महत्त्वाच्या आहेत: माती चाचणी, पिकाची अवस्था आणि शेतातील ओलावा. माती खूप कोरडी असेल तर खत नीट विरघळत नाही आणि पिकाला त्याचा योग्य फायदा मिळत नाही, म्हणून पुरेसा ओलावा असताना किंवा हलक्या पाण्यानंतर खत देणे चांगले. सर्व खत एकदाच देण्यापेक्षा भागांमध्ये दिल्यास पोषण चांगले मिळते आणि खताची नासाडी कमी होते. पाने फिकट दिसत असतील किंवा वाढ कमी असेल तर नत्र, पालाश किंवा सूक्ष्म अन्नद्रव्यांची गरज तपासा, पण तपासणीशिवाय जास्त खत देऊ नका कारण खर्च वाढतो आणि पिकालाही त्रास होऊ शकतो.",
        "ai_weather_reply": "लवकरच पाऊस येण्याची शक्यता आहे, त्यामुळे आत्ताच फवारणी करू नका. पावसापूर्वी फवारणी केल्यास औषध वाहून जाऊ शकते आणि पैसा व मेहनत वाया जाऊ शकते. आधी शेतातील निचरा व्यवस्थित आहे का ते तपासा, म्हणजे पाणी साचून मुळांना त्रास होणार नाही. खत किंवा औषध देण्याचा विचार असेल तर हवामान स्थिर होईपर्यंत थांबा. पावसानंतर ओलावा वाढल्याने अनेक पिकांमध्ये रोग आणि किडीचा धोका वाढू शकतो, त्यामुळे शेतावर लक्ष ठेवा.",
        "ai_unavailable_reply": "सध्या AI सल्ला उपलब्ध नाही. कृपया तुमची OpenAI बिलिंग/कोटा तपासा किंवा नंतर पुन्हा प्रयत्न करा.",
        "ai_missing_key_reply": "OpenAI key अजून जोडलेली नाही. लाइव्ह AI चॅटसाठी .env मध्ये OPENAI_API_KEY जोडा.",
        "disease_detection": "रोग शोध आणि पीक अहवाल",
        "image_upload_rule_engine": "प्रतिमा अपलोड + नियम इंजिन",
        "symptom": "लक्षण",
        "crop_image": "पिकाची प्रतिमा",
        "save_disease_report": "रोग अहवाल जतन करा",
        "no_disease_reports": "अजून कोणतेही रोग अहवाल नाहीत.",
        "leaf_spots": "पानांवरील डाग",
        "yellowing": "पिवळेपणा",
        "chewing_holes": "चावलेली छिद्रे",
        "farmer_community": "शेतकरी समुदाय",
        "live_community_feed": "लाईव्ह कम्युनिटी फीड",
        "question_title": "प्रश्न शीर्षक",
        "problem_details": "समस्येचा तपशील",
        "post_question": "प्रश्न पोस्ट करा",
        "reply": "उत्तर",
        "reply_placeholder": "या शेतकऱ्यासाठी उत्तर लिहा",
        "send_reply": "उत्तर पाठवा",
        "community_post_created": "कम्युनिटी पोस्ट तयार झाली.",
        "reply_added": "उत्तर जोडले गेले.",
        "no_posts": "अजून कोणतीही कम्युनिटी पोस्ट नाही. सर्वात पहिले तुमचा शेतातील प्रश्न पोस्ट करा.",
        "expert_panel": "तज्ज्ञ पॅनल",
        "admin_panel": "अॅडमिन पॅनल",
        "farmer_questions": "शेतकरी प्रश्न",
        "expert_view": "तज्ज्ञ दृश्य",
        "disease_reports": "रोग अहवाल",
        "review_queue": "पुनरावलोकन रांग",
        "send_notifications": "सूचना पाठवा",
        "admin_tools": "अॅडमिन साधने",
        "target_user": "लक्ष्य वापरकर्ता",
        "all_users": "सर्व वापरकर्ते",
        "title": "शीर्षक",
        "body": "मजकूर",
        "create_notification": "सूचना तयार करा",
        "users_and_roles": "वापरकर्ते आणि भूमिका",
        "users_count": "{count} वापरकर्ते",
        "no_location": "स्थान नाही",
        "notification_history": "सूचना इतिहास",
        "required_name_email_password": "नाव, ईमेल आणि पासवर्ड आवश्यक आहेत.",
        "account_created_login_now": "खाते तयार झाले. आता तुम्ही लॉगिन करू शकता.",
        "email_registered": "हा ईमेल आधीच नोंदणीकृत आहे.",
        "invalid_credentials": "अवैध ईमेल किंवा पासवर्ड.",
        "logged_out": "तुम्ही लॉगआउट झाला आहात.",
        "access_denied": "तुम्हाला या पानाचा प्रवेश नाही.",
        "weather_refresh_error": "हवामान रीफ्रेश करण्यासाठी गाव, जिल्हा किंवा राज्य भरा.",
        "mandi_refresh_error": "मंडी दर शोधण्यासाठी राज्य आणि जिल्हा निवडा.",
        "disease_report_saved": "रोग अहवाल जतन केला.",
        "notification_created": "सूचना तयार झाली.",
    },
}
LOCATION_DIRECTORY = {
    "Andhra Pradesh": {
        "Anantapur": ["Anantapur", "Dharmavaram", "Hindupur"],
        "Chittoor": ["Chittoor", "Madanapalle", "Punganur"],
        "Guntur": ["Guntur", "Mangalagiri", "Tenali"],
    },
    "Arunachal Pradesh": {
        "Papum Pare": ["Itanagar", "Doimukh", "Naharlagun"],
        "Tawang": ["Tawang", "Jang", "Lumla"],
    },
    "Assam": {
        "Kamrup": ["Guwahati", "Hajo", "Rangia"],
        "Nagaon": ["Nagaon", "Kampur", "Raha"],
        "Sonitpur": ["Tezpur", "Dhekiajuli", "Biswanath"],
    },
    "Bihar": {
        "Gaya": ["Gaya", "Sherghati", "Tekari"],
        "Muzaffarpur": ["Muzaffarpur", "Motipur", "Kanti"],
        "Patna": ["Patna", "Bakhtiarpur", "Danapur"],
    },
    "Chhattisgarh": {
        "Bilaspur": ["Bilaspur", "Takhatpur", "Masturi"],
        "Durg": ["Durg", "Bhilai", "Patan"],
        "Raipur": ["Raipur", "Arang", "Abhanpur"],
    },
    "Goa": {
        "North Goa": ["Mapusa", "Bicholim", "Pernem"],
        "South Goa": ["Margao", "Quepem", "Canacona"],
    },
    "Gujarat": {
        "Ahmedabad": ["Ahmedabad", "Sanand", "Dholka"],
        "Rajkot": ["Rajkot", "Gondal", "Jasdan"],
        "Surat": ["Surat", "Bardoli", "Kamrej"],
    },
    "Haryana": {
        "Hisar": ["Hisar", "Hansi", "Narnaund"],
        "Karnal": ["Karnal", "Nilokheri", "Assandh"],
        "Sirsa": ["Sirsa", "Dabwali", "Ellenabad"],
    },
    "Himachal Pradesh": {
        "Kangra": ["Dharamshala", "Palampur", "Nurpur"],
        "Mandi": ["Mandi", "Sundarnagar", "Jogindernagar"],
        "Shimla": ["Shimla", "Rohru", "Theog"],
    },
    "Jharkhand": {
        "Dhanbad": ["Dhanbad", "Jharia", "Baghmara"],
        "Ranchi": ["Ranchi", "Bundu", "Tamar"],
        "West Singhbhum": ["Chaibasa", "Chakradharpur", "Noamundi"],
    },
    "Karnataka": {
        "Belagavi": ["Belagavi", "Gokak", "Athani"],
        "Mysuru": ["Mysuru", "Nanjangud", "Hunsur"],
        "Tumakuru": ["Tumakuru", "Tiptur", "Gubbi"],
    },
    "Kerala": {
        "Ernakulam": ["Kochi", "Aluva", "Perumbavoor"],
        "Palakkad": ["Palakkad", "Ottapalam", "Chittur"],
        "Thrissur": ["Thrissur", "Kodungallur", "Irinjalakuda"],
    },
    "Madhya Pradesh": {
        "Bhopal": ["Bhopal", "Berasia", "Phanda"],
        "Indore": ["Indore", "Mhow", "Depalpur"],
        "Jabalpur": ["Jabalpur", "Sihora", "Patan"],
    },
    "Maharashtra": {
        "Ahmednagar": ["Ahmednagar", "Sangamner", "Shrirampur"],
        "Beed": ["Beed", "Ambejogai", "Georai"],
        "Chhatrapati Sambhajinagar": ["Paithan", "Kannad", "Phulambri"],
        "Dhule": ["Dhule", "Shirpur", "Sakri"],
        "Jalgaon": ["Jalgaon", "Bhusawal", "Chopda"],
        "Jalna": ["Jalna", "Ambad", "Bhokardan"],
        "Kolhapur": ["Kolhapur", "Karvir", "Hatkanangale"],
        "Latur": ["Latur", "Ausa", "Udgir"],
        "Mumbai City": ["Colaba", "Byculla", "Dadar"],
        "Nagpur": ["Nagpur", "Katol", "Kamptee"],
        "Nanded": ["Nanded", "Loha", "Mukhed"],
        "Nandurbar": ["Nandurbar", "Shahada", "Navapur"],
        "Nashik": ["Pimpalgaon", "Niphad", "Sinnar", "Igatpuri", "Yeola", "Nashik"],
        "Pune": ["Baramati", "Chakan", "Junnar", "Shirur", "Pune"],
        "Ratnagiri": ["Ratnagiri", "Chiplun", "Dapoli"],
        "Satara": ["Satara", "Karad", "Phaltan"],
        "Solapur": ["Solapur", "Pandharpur", "Akkalkot"],
        "Thane": ["Thane", "Bhiwandi", "Kalyan"],
    },
    "Manipur": {
        "Imphal East": ["Porompat", "Sawombung", "Keirao"],
        "Imphal West": ["Lamphel", "Sekmai", "Patsoi"],
    },
    "Meghalaya": {
        "East Khasi Hills": ["Shillong", "Mawkynrew", "Sohra"],
        "West Garo Hills": ["Tura", "Dadenggre", "Selsella"],
    },
    "Mizoram": {
        "Aizawl": ["Aizawl", "Saitual", "Darlawn"],
        "Lunglei": ["Lunglei", "Hnahthial", "Bunghmun"],
    },
    "Nagaland": {
        "Dimapur": ["Dimapur", "Chumoukedima", "Medziphema"],
        "Kohima": ["Kohima", "Tseminyu", "Jakhama"],
    },
    "Odisha": {
        "Cuttack": ["Cuttack", "Athagad", "Banki"],
        "Khordha": ["Bhubaneswar", "Jatni", "Balipatna"],
        "Sambalpur": ["Sambalpur", "Kuchinda", "Rairakhol"],
    },
    "Punjab": {
        "Amritsar": ["Amritsar", "Ajnala", "Majitha"],
        "Bathinda": ["Bathinda", "Talwandi Sabo", "Rampura Phul"],
        "Ludhiana": ["Ludhiana", "Khanna", "Samrala"],
    },
    "Rajasthan": {
        "Jaipur": ["Jaipur", "Chomu", "Kotputli"],
        "Kota": ["Kota", "Ramganj Mandi", "Sangod"],
        "Sri Ganganagar": ["Sri Ganganagar", "Raisinghnagar", "Suratgarh"],
    },
    "Sikkim": {
        "East Sikkim": ["Gangtok", "Pakyong", "Rangpo"],
        "South Sikkim": ["Namchi", "Ravangla", "Jorethang"],
    },
    "Tamil Nadu": {
        "Coimbatore": ["Coimbatore", "Pollachi", "Mettupalayam"],
        "Erode": ["Erode", "Gobichettipalayam", "Sathyamangalam"],
        "Thanjavur": ["Thanjavur", "Kumbakonam", "Pattukkottai"],
    },
    "Telangana": {
        "Karimnagar": ["Karimnagar", "Huzurabad", "Jammikunta"],
        "Nalgonda": ["Nalgonda", "Miryalaguda", "Devarakonda"],
        "Warangal": ["Warangal", "Parkal", "Narsampet"],
    },
    "Tripura": {
        "Dhalai": ["Ambassa", "Kamalpur", "Gandacherra"],
        "West Tripura": ["Agartala", "Jirania", "Mohanpur"],
    },
    "Uttar Pradesh": {
        "Agra": ["Agra", "Etmadpur", "Kheragarh"],
        "Kanpur Nagar": ["Kanpur", "Bilhaur", "Ghatampur"],
        "Lucknow": ["Lucknow", "Malihabad", "Mohanlalganj"],
        "Varanasi": ["Varanasi", "Pindra", "Arajiline"],
    },
    "Uttarakhand": {
        "Dehradun": ["Dehradun", "Vikasnagar", "Doiwala"],
        "Haridwar": ["Haridwar", "Roorkee", "Laksar"],
        "Udham Singh Nagar": ["Rudrapur", "Kashipur", "Sitarganj"],
    },
    "West Bengal": {
        "Darjeeling": ["Darjeeling", "Siliguri", "Kurseong"],
        "Hooghly": ["Chinsurah", "Arambagh", "Tarakeswar"],
        "Nadia": ["Krishnanagar", "Ranaghat", "Kalyani"],
    },
    "Delhi": {
        "Central Delhi": ["Daryaganj", "Karol Bagh", "Paharganj"],
        "North West Delhi": ["Narela", "Rohini", "Bawana"],
        "South Delhi": ["Saket", "Mehrauli", "Badarpur"],
    },
    "Jammu and Kashmir": {
        "Anantnag": ["Anantnag", "Bijbehara", "Pahalgam"],
        "Baramulla": ["Baramulla", "Sopore", "Uri"],
        "Jammu": ["Jammu", "Akhnoor", "Bishnah"],
    },
    "Ladakh": {
        "Kargil": ["Kargil", "Drass", "Sankoo"],
        "Leh": ["Leh", "Nubra", "Nyoma"],
    },
    "Puducherry": {
        "Karaikal": ["Karaikal", "Nedungadu", "Tirunallar"],
        "Puducherry": ["Puducherry", "Bahour", "Villianur"],
    },
    "Chandigarh": {
        "Chandigarh": ["Chandigarh", "Manimajra", "Dhanas"],
    },
}
INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Puducherry",
    "Chandigarh",
]
DISTRICT_OPTIONS = sorted({district for districts in LOCATION_DIRECTORY.values() for district in districts})
VILLAGE_OPTIONS = sorted(
    {
        village
        for districts in LOCATION_DIRECTORY.values()
        for villages in districts.values()
        for village in villages
    }
)


APP_DATABASE_NAME = "KRISHIGOLD.AI.db"
RUNTIME_DATABASE_NAME = "KRISHIGOLD.AI_runtime.db"


def get_windows_data_dir():
    windows_data_root = os.getenv("LOCALAPPDATA", "").strip()
    if windows_data_root:
        return Path(windows_data_root) / "KRISHIGOLD.AI"
    return BASE_DIR


def can_write_to_directory(path):
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe_file = path / "write_probe.tmp"
        probe_file.write_text("ok", encoding="utf-8")
        probe_file.unlink()
        return True
    except OSError:
        return False


def get_data_dir():
    configured_dir = os.getenv("KRISHIGOLD.AI_DATA_DIR", "").strip()
    if configured_dir:
        return Path(configured_dir).expanduser()
    return BASE_DIR


def is_valid_sqlite_database(path):
    try:
        if not path.exists() or path.stat().st_size == 0:
            return False
        with path.open("rb") as handle:
            return handle.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def preserve_invalid_database(path):
    if not path.exists() or is_valid_sqlite_database(path):
        return
    backup_path = path.with_name(f"{path.stem}_invalid{path.suffix}")
    if backup_path.exists():
        return
    try:
        shutil.move(str(path), str(backup_path))
    except OSError:
        pass


def copy_database_file(source_path, target_path):
    if not is_valid_sqlite_database(source_path):
        return False
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        preserve_invalid_database(target_path)
        shutil.copyfile(source_path, target_path)
        ensure_file_is_writable(target_path)
        return is_valid_sqlite_database(target_path)
    except OSError:
        return False


DATA_DIR = get_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_DATABASE = BASE_DIR / APP_DATABASE_NAME
WINDOWS_DATABASE = get_windows_data_dir() / APP_DATABASE_NAME
PRIMARY_DATABASE = DATA_DIR / APP_DATABASE_NAME
RUNTIME_DATABASE = get_windows_data_dir() / RUNTIME_DATABASE_NAME
DATABASE = PRIMARY_DATABASE


def ensure_file_is_writable(path):
    try:
        if path.exists():
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def can_write_to_database(path):
    try:
        ensure_file_is_writable(path)
        connection = sqlite3.connect(path, timeout=20)
        connection.execute("CREATE TABLE IF NOT EXISTS __write_probe (id INTEGER PRIMARY KEY)")
        connection.execute("DROP TABLE __write_probe")
        connection.commit()
        connection.close()
        return True
    except sqlite3.Error:
        return False


def promote_to_runtime_database(source_path, runtime_path):
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    if runtime_path.exists():
        ensure_file_is_writable(runtime_path)
        if can_write_to_database(runtime_path):
            return runtime_path
    try:
        if source_path.exists():
            source = sqlite3.connect(source_path, timeout=20)
            target = sqlite3.connect(runtime_path, timeout=20)
            source.backup(target)
            target.close()
            source.close()
            ensure_file_is_writable(runtime_path)
            if can_write_to_database(runtime_path):
                return runtime_path
    except sqlite3.Error:
        pass
    if can_write_to_database(runtime_path):
        return runtime_path
    return source_path


for candidate in {LEGACY_DATABASE, WINDOWS_DATABASE, PRIMARY_DATABASE, RUNTIME_DATABASE}:
    preserve_invalid_database(candidate)

if PRIMARY_DATABASE != LEGACY_DATABASE and is_valid_sqlite_database(LEGACY_DATABASE) and not is_valid_sqlite_database(PRIMARY_DATABASE):
    copy_database_file(LEGACY_DATABASE, PRIMARY_DATABASE)

if PRIMARY_DATABASE != WINDOWS_DATABASE and is_valid_sqlite_database(WINDOWS_DATABASE) and not is_valid_sqlite_database(PRIMARY_DATABASE):
    copy_database_file(WINDOWS_DATABASE, PRIMARY_DATABASE)

if is_valid_sqlite_database(RUNTIME_DATABASE) and not is_valid_sqlite_database(PRIMARY_DATABASE):
    copy_database_file(RUNTIME_DATABASE, PRIMARY_DATABASE)

ensure_file_is_writable(PRIMARY_DATABASE)
if PRIMARY_DATABASE.exists() and is_valid_sqlite_database(PRIMARY_DATABASE):
    if not can_write_to_database(PRIMARY_DATABASE):
        DATABASE = promote_to_runtime_database(PRIMARY_DATABASE, RUNTIME_DATABASE)
elif is_valid_sqlite_database(RUNTIME_DATABASE):
    DATABASE = RUNTIME_DATABASE


def load_env():
    if not ENV_FILE.exists():
        return
    try:
        content = ENV_FILE.read_text(encoding="utf-8")
    except (PermissionError, OSError):
        return
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=20)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    global DATABASE
    schema_sql = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'farmer',
            language TEXT NOT NULL DEFAULT 'en',
            location TEXT,
            crops TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS disease_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            crop TEXT NOT NULL,
            symptom TEXT NOT NULL,
            image_name TEXT,
            diagnosis TEXT NOT NULL,
            solution TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS post_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    try:
        db = sqlite3.connect(DATABASE, timeout=20)
        db.executescript(schema_sql)
        db.commit()
        db.close()
    except sqlite3.OperationalError as error:
        if "disk I/O error" not in str(error):
            raise
        DATABASE = promote_to_runtime_database(DATABASE, RUNTIME_DATABASE)
        db = sqlite3.connect(DATABASE, timeout=20)
        db.executescript(schema_sql)
        db.commit()
        db.close()


def seed_demo_data():
    db = sqlite3.connect(DATABASE, timeout=20)
    db.row_factory = sqlite3.Row
    count = db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if count == 0:
        now = datetime.utcnow().isoformat()
        demo_users = [
            ("Farmer Demo", "farmer@example.com", generate_password_hash("demo123"), "farmer", "en", "Nashik, Maharashtra", "soybean,cotton", now),
            ("Expert Demo", "expert@example.com", generate_password_hash("demo123"), "expert", "en", "Pune, Maharashtra", "tomato,onion", now),
            ("Admin Demo", "admin@example.com", generate_password_hash("demo123"), "admin", "en", "Mumbai, Maharashtra", "all", now),
        ]
        db.executemany(
            "INSERT INTO users (name, email, password_hash, role, language, location, crops, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            demo_users,
        )
        db.commit()
    db.close()


def cleanup_demo_content():
    db = sqlite3.connect(DATABASE, timeout=20)
    db.execute(
        "DELETE FROM posts WHERE title = ? AND body = ?",
        ("Cotton leaves turning yellow", "Whitefly pressure seems high this week. Looking for a safer control plan."),
    )
    db.execute(
        "DELETE FROM notifications WHERE title = ? AND body = ?",
        ("Rain warning", "Rain is likely later today. Avoid pesticide spray and check field drainage."),
    )
    db.commit()
    db.close()


def cleanup_duplicate_posts(max_duplicates=1):
    db = sqlite3.connect(DATABASE, timeout=20)
    duplicate_groups = db.execute(
        """
        SELECT
            LOWER(TRIM(title)) AS normalized_title,
            LOWER(TRIM(body)) AS normalized_body,
            COUNT(*) AS post_count
        FROM posts
        GROUP BY normalized_title, normalized_body
        HAVING COUNT(*) > ?
        """,
        (max_duplicates,),
    ).fetchall()
    for normalized_title, normalized_body, _post_count in duplicate_groups:
        post_ids = db.execute(
            """
            SELECT id
            FROM posts
            WHERE LOWER(TRIM(title)) = ? AND LOWER(TRIM(body)) = ?
            ORDER BY id DESC
            """,
            (normalized_title, normalized_body),
        ).fetchall()
        ids_to_remove = [str(post_id[0]) for post_id in post_ids[max_duplicates:]]
        if not ids_to_remove:
            continue
        placeholders = ", ".join("?" for _ in ids_to_remove)
        db.execute(f"DELETE FROM post_replies WHERE post_id IN ({placeholders})", ids_to_remove)
        db.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", ids_to_remove)
    db.commit()
    db.close()


def remove_uploaded_filenames_from_reports():
    db = sqlite3.connect(DATABASE, timeout=20)
    reports = db.execute("SELECT id, solution FROM disease_reports").fetchall()
    for report_id, solution in reports:
        cleaned_solution = (solution or "").split(" Uploaded file:", 1)[0].strip()
        if cleaned_solution != (solution or ""):
            db.execute(
                "UPDATE disease_reports SET solution = ? WHERE id = ?",
                (cleaned_solution, report_id),
            )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash(translate(get_active_language_code(), "access_denied"), "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


def fetch_json(url):
    with urlopen(url, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def is_port_available(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        return probe.connect_ex((host, port)) != 0


def get_flask_port(default_port=5000):
    configured_port = os.getenv("PORT", "").strip()
    if configured_port.isdigit():
        return int(configured_port)
    if is_port_available("127.0.0.1", default_port):
        return default_port
    return 5001


def normalize_location(location):
    raw = " ".join((location or "").replace(",", " , ").split()).strip(" ,")
    if not raw:
        return "Nashik, Maharashtra"
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if len(parts) >= 2:
        match = get_close_matches(parts[1].title(), INDIAN_STATES, n=1, cutoff=0.7)
        if match:
            parts[1] = match[0]
    return ", ".join(part.title() for part in parts) or "Nashik, Maharashtra"


def build_location(village="", district="", state=""):
    parts = [v.strip().title() for v in [village, district, state] if v and v.strip()]
    return ", ".join(parts)


def get_language_label(language_code):
    return LANGUAGE_OPTIONS.get((language_code or "").strip().lower(), "English")


def translate(language_code, key):
    selected_language = (language_code or "en").strip().lower()
    return TRANSLATIONS.get(selected_language, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def translate_format(language_code, key, **kwargs):
    template = translate(language_code, key)
    try:
        return template.format(**kwargs)
    except Exception:
        return template


SARVAM_LANGUAGE_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
}
SARVAM_LANGUAGE_ALIASES = {
    **SARVAM_LANGUAGE_CODES,
    "en-in": "en-IN",
    "hi-in": "hi-IN",
    "mr-in": "mr-IN",
}


def is_sarvam_translate_configured():
    return bool(os.getenv("SARVAM_API_KEY", "").strip())


def is_translation_configured():
    return is_sarvam_translate_configured()


def get_sarvam_language_code(language_code):
    normalized_code = (language_code or "").strip().lower()
    if normalized_code == "auto":
        return "auto"
    return SARVAM_LANGUAGE_ALIASES.get(normalized_code)


def sarvam_translate_text(text, target_lang, source_lang="auto"):
    if not (text or "").strip():
        return "", "unknown"
    api_key = os.getenv("SARVAM_API_KEY", "").strip()
    source_language_code = get_sarvam_language_code(source_lang)
    target_language_code = get_sarvam_language_code(target_lang)
    if not api_key or not source_language_code or not target_language_code:
        return None, "unknown"
    payload = {
        "input": text[:2000],
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "model": os.getenv("SARVAM_TRANSLATE_MODEL", "mayura:v1"),
    }
    request = Request(
        "https://api.sarvam.ai/translate",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        translated_text = result.get("translated_text")
        source_language_code = (result.get("source_language_code") or "unknown").split("-", 1)[0]
        return translated_text, source_language_code
    except Exception:
        return None, "unknown"


def translate_text(text, target_lang):
    if not (text or "").strip():
        return ""
    translated_text, _source_language_code = sarvam_translate_text(text, target_lang)
    if translated_text:
        return translated_text
    return text


def detect_language(text):
    if not (text or "").strip():
        return "unknown"
    return "unknown"


def build_translation_payload(text, target_langs=("en", "hi")):
    clean_text = (text or "").strip()
    detected_language = detect_language(clean_text)
    payload = {
        "available": is_translation_configured(),
        "detected_language": detected_language,
        "text": {
            "original": clean_text,
        },
    }
    for language_code in target_langs:
        if detected_language == language_code:
            payload["text"][language_code] = clean_text
            continue
        translated_text, source_language_code = sarvam_translate_text(clean_text, language_code)
        if translated_text:
            payload["text"][language_code] = translated_text
            if detected_language == "unknown":
                detected_language = source_language_code
                payload["detected_language"] = source_language_code
            continue
        payload["text"][language_code] = translate_text(clean_text, language_code)
    return payload


def get_speech_recognition_locale(language_code):
    return {
        "en": "en-IN",
        "hi": "hi-IN",
        "mr": "mr-IN",
    }.get((language_code or "en").strip().lower(), "en-IN")


def get_active_language_code():
    session_language = (session.get("language") or "").strip().lower()
    if session_language in LANGUAGE_OPTIONS:
        return session_language
    if "user_id" in session:
        user = current_user()
        if user:
            user_language = (user["language"] or "").strip().lower()
            if user_language in LANGUAGE_OPTIONS:
                return user_language
    return "en"


@app.context_processor
def inject_translation_helpers():
    current_language = get_active_language_code()
    return {
        "t": lambda key: translate(current_language, key),
        "current_language": current_language,
        "language_options": LANGUAGE_OPTIONS,
    }


def get_location_form_options():
    return {
        "state_options": INDIAN_STATES,
        "district_options": DISTRICT_OPTIONS,
        "village_options": VILLAGE_OPTIONS,
        "location_directory": LOCATION_DIRECTORY,
    }


def geocode_location(location, api_key):
    candidates = [location]
    if "," not in location:
        candidates.append(f"{location}, IN")
    else:
        city = location.split(",", 1)[0].strip()
        if city:
            candidates.append(f"{city}, IN")
    for candidate in candidates:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={quote_plus(candidate)}&limit=1&appid={api_key}"
        geo_data = fetch_json(geo_url)
        if geo_data:
            return geo_data[0]
    return None


def estimate_soil_moisture(location, humidity=None, weather_summary=""):
    normalized_location = normalize_location(location)
    village, district, state = parse_location_parts(normalized_location)
    location_seed = sum(ord(char) for char in normalized_location.lower())
    if humidity is None:
        humidity = 55 + (location_seed % 25)
    weather_hint = (weather_summary or "").lower()
    moisture_score = int(humidity)
    if "rain" in weather_hint or "storm" in weather_hint or "drizzle" in weather_hint:
        moisture_score += 15
    elif "clear" in weather_hint or "hot" in weather_hint:
        moisture_score -= 10
    moisture_score = max(25, min(92, moisture_score))
    if moisture_score >= 75:
        moisture_label = "High"
    elif moisture_score >= 55:
        moisture_label = "Moderate"
    else:
        moisture_label = "Low"
    focus_area = village or district or state or normalized_location
    return {
        "value": f"{moisture_score}% ({moisture_label})",
        "label": f"{focus_area} village soil estimate",
    }


def fallback_weather(location, error=None):
    soil = estimate_soil_moisture(location, humidity=74, weather_summary="Light rain expected after 4 PM")
    return {
        "location": location or "Nashik, Maharashtra",
        "source": "Fallback weather data",
        "current": "31 C",
        "summary": "Light rain expected after 4 PM",
        "metrics": {"humidity": "74%", "wind": "12 km/h", "soil_moisture": soil["value"]},
        "soil_label": soil["label"],
        "forecast": [
            {"day": "Fri", "temp": "31 C", "note": "Cloudy"},
            {"day": "Sat", "temp": "29 C", "note": "Light rain"},
            {"day": "Sun", "temp": "30 C", "note": "Humid"},
        ],
        "api_ready": bool(os.getenv("WEATHER_API_KEY")),
        "error": error,
    }


def get_weather(location):
    api_key = os.getenv("WEATHER_API_KEY", "").strip()
    normalized_location = normalize_location(location)
    if not api_key:
        return fallback_weather(normalized_location, "Live weather API key missing, so demo weather is shown.")
    try:
        geo = geocode_location(normalized_location, api_key)
        if not geo:
            return fallback_weather(normalized_location, f"Could not find live weather for '{normalized_location}'. Showing demo weather instead.")
        lat = geo["lat"]
        lon = geo["lon"]
        current = fetch_json(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric")
        forecast = fetch_json(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric")
        soil = estimate_soil_moisture(
            normalized_location,
            humidity=current["main"].get("humidity"),
            weather_summary=current["weather"][0]["description"],
        )
        cards = []
        seen = set()
        for item in forecast.get("list", []):
            day = item["dt_txt"].split(" ")[0]
            if day in seen:
                continue
            seen.add(day)
            cards.append(
                {
                    "day": day[-2:],
                    "temp": f"{round(item['main']['temp'])} C",
                    "note": item["weather"][0]["main"],
                }
            )
            if len(cards) == 3:
                break
        return {
            "location": f"{current.get('name', geo.get('name', normalized_location))}, {geo.get('state') or geo.get('country', 'IN')}",
            "source": "OpenWeatherMap",
            "current": f"{round(current['main']['temp'])} C",
            "summary": current["weather"][0]["description"].title(),
            "metrics": {
                "humidity": f"{current['main']['humidity']}%",
                "wind": f"{round(current['wind']['speed'] * 3.6)} km/h",
                "soil_moisture": soil["value"],
            },
            "soil_label": soil["label"],
            "forecast": cards or fallback_weather(normalized_location)["forecast"],
            "api_ready": True,
            "error": None,
        }
    except HTTPError as exc:
        if exc.code == 404:
            return fallback_weather(normalized_location, f"Could not find live weather for '{normalized_location}'. Showing demo weather instead.")
        return fallback_weather(normalized_location, "Weather service returned an error, so demo weather is shown.")
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return fallback_weather(normalized_location, "Could not reach the weather service, so demo weather is shown.")


def fallback_market_rates(location="", crops=""):
    fallback_rows = [
        {"crop": "Soybean", "market": "Lasalgaon APMC", "price": "Rs 4,680/qtl", "source": "Demo", "location": "Nashik, Maharashtra", "date": "Demo data"},
        {"crop": "Cotton", "market": "Jalgaon APMC", "price": "Rs 7,220/qtl", "source": "Demo", "location": "Jalgaon, Maharashtra", "date": "Demo data"},
        {"crop": "Tomato", "market": "Nashik APMC", "price": "Rs 1,480/qtl", "source": "Demo", "location": "Nashik, Maharashtra", "date": "Demo data"},
    ]
    filtered_rows = filter_market_rows(fallback_rows, location, crops)
    if location or crops:
        return filtered_rows
    return filtered_rows or fallback_rows


def parse_location_parts(location):
    normalized = normalize_location(location)
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    village = ""
    district = ""
    state = ""
    if len(parts) >= 3:
        village, district, state = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        district, state = parts[0], parts[1]
    elif len(parts) == 1:
        district = parts[0]
    return village, district, state


def parse_crop_list(crops):
    return [item.strip().title() for item in (crops or "").split(",") if item.strip()]


def normalize_crop_name(crop):
    lowered = (crop or "").strip().lower()
    for option in CROP_OPTIONS:
        if option.lower() == lowered:
            return option
    return (crop or "").strip().title() or "Cotton"


def market_row_matches(row, village="", district="", state="", crop_names=None):
    market_name = str(row.get("market", "")).strip().lower()
    row_district = str(row.get("district", "")).strip().lower()
    row_state = str(row.get("state", "")).strip().lower()
    if (not row_district or not row_state) and row.get("location"):
        location_parts = [part.strip().lower() for part in str(row.get("location", "")).split(",") if part.strip()]
        if len(location_parts) >= 2:
            row_district = row_district or location_parts[-2]
            row_state = row_state or location_parts[-1]
    row_crop = str(row.get("commodity", row.get("crop", ""))).strip().lower()
    village = (village or "").strip().lower()
    district = (district or "").strip().lower()
    state = (state or "").strip().lower()
    crop_names = [crop.strip().lower() for crop in (crop_names or []) if crop.strip()]

    if state and row_state and row_state != state:
        return False
    if district and row_district and row_district != district:
        return False
    if crop_names and not any(crop in row_crop for crop in crop_names):
        return False
    if village:
        village_tokens = [token for token in village.replace("-", " ").split() if token]
        if not village_tokens:
            return True
        if not all(token in market_name for token in village_tokens):
            return False
    return True


def filter_market_rows(rows, location="", crops=""):
    village, district, state = parse_location_parts(location)
    crop_names = parse_crop_list(crops)
    filtered_rows = [
        row for row in rows
        if market_row_matches(row, village=village, district=district, state=state, crop_names=crop_names)
    ]
    if filtered_rows:
        return filtered_rows
    if crop_names:
        crop_only_rows = [
            row for row in rows
            if market_row_matches(row, district=district, state=state, crop_names=crop_names)
        ]
        if crop_only_rows:
            return crop_only_rows
    if district or state:
        district_state_rows = [
            row for row in rows
            if market_row_matches(row, district=district, state=state)
        ]
        if district_state_rows:
            return district_state_rows
    return []


def get_market_rates(location="", crops=""):
    mandi_url = os.getenv("MANDI_API_URL", DEFAULT_MANDI_API_URL).strip()
    mandi_key = os.getenv("MANDI_API_KEY", "").strip()
    _village, district, state = parse_location_parts(location)
    crop_names = parse_crop_list(crops)
    try:
        params = ["format=json", "limit=20"]
        if mandi_key:
            params.append(f"api-key={quote_plus(mandi_key)}")
        if state:
            params.append(f"filters[state]={quote_plus(state)}")
        if district:
            params.append(f"filters[district]={quote_plus(district)}")
        final_url = f"{mandi_url}?{'&'.join(params)}"
        data = fetch_json(final_url)
        rows = data.get("records", [])

        if not rows and state:
            state_only_params = [item for item in params if not item.startswith("filters[district]=")]
            data = fetch_json(f"{mandi_url}?{'&'.join(state_only_params)}")
            rows = data.get("records", [])

        district_location = build_location("", district, state)
        rows = filter_market_rows(rows, district_location, crops) or rows

        parsed = []
        seen = set()
        for row in rows:
            key = (row.get("market"), row.get("commodity"))
            if key in seen:
                continue
            seen.add(key)
            parsed.append(
                {
                    "crop": row.get("commodity", row.get("crop", "Unknown crop")),
                    "market": row.get("market", "Unknown market"),
                    "price": f"Rs {row.get('modal_price', row.get('price', 'N/A'))}/qtl",
                    "source": "AGMARKNET",
                    "location": f"{row.get('district', district or 'Unknown district')}, {row.get('state', state or 'Unknown state')}",
                    "date": row.get("arrival_date", "Latest"),
                }
            )
            if len(parsed) == 8:
                break

        parsed = filter_market_rows(parsed, district_location, crops) or parsed
        return parsed or fallback_market_rates(district_location, crops)
    except (HTTPError, URLError, TimeoutError, TypeError, KeyError, json.JSONDecodeError):
        return fallback_market_rates(build_location("", district, state), crops)


def get_mandi_market_options(location="", crops=""):
    mandi_url = os.getenv("MANDI_API_URL", DEFAULT_MANDI_API_URL).strip()
    mandi_key = os.getenv("MANDI_API_KEY", "").strip()
    _village, district, state = parse_location_parts(location)
    crop_names = parse_crop_list(crops)
    if not district and not state:
        return []
    try:
        params = ["format=json", "limit=100"]
        if mandi_key:
            params.append(f"api-key={quote_plus(mandi_key)}")
        if state:
            params.append(f"filters[state]={quote_plus(state)}")
        if district:
            params.append(f"filters[district]={quote_plus(district)}")
        data = fetch_json(f"{mandi_url}?{'&'.join(params)}")
        options = []
        seen = set()
        rows = filter_market_rows(data.get("records", []), build_location("", district, state), crops) or data.get("records", [])
        for row in rows:
            market = str(row.get("market", "")).strip()
            if not market:
                continue
            if crop_names and not any(crop.lower() in str(row.get("commodity", "")).lower() for crop in crop_names):
                continue
            label = f"{market}, {row.get('district', district)}, {row.get('state', state)}"
            lowered = label.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            options.append(label)
        return options[:40]
    except (HTTPError, URLError, TimeoutError, TypeError, KeyError, json.JSONDecodeError):
        return []


def advisory_for(crop):
    crop_name = normalize_crop_name(crop)
    profiles = {
        "Soybean": {
            "hero": "Avoid evening spray before forecast rain.",
            "guidance": [
                "Check drainage before rainfall to prevent root stress.",
                "Scout leaves early in the morning for pest pressure.",
                "Keep irrigation light while topsoil moisture is already high.",
            ],
            "fertilizer": [
                "Apply balanced NPK based on soil test.",
                "Use biofertilizer seed treatment where available.",
            ],
            "pesticide": [
                "Spray only after field scouting confirms need.",
                "Use gloves and a mask during pesticide handling.",
            ],
        },
        "Cotton": {
            "hero": "Monitor whitefly and keep weeds controlled around the field.",
            "guidance": [
                "Inspect the underside of leaves for whitefly and eggs.",
                "Avoid waterlogging in low patches.",
                "Keep row spacing open to improve airflow.",
            ],
            "fertilizer": [
                "Apply split nitrogen dose instead of one heavy application.",
                "Add potash support during square formation.",
            ],
            "pesticide": [
                "Start with sticky traps and neem options.",
                "Avoid repeating the same insecticide group.",
            ],
        },
        "Wheat": {
            "hero": "Protect tillering and avoid unnecessary irrigation near maturity.",
            "guidance": [
                "Watch for yellow rust and aphids in cool mornings.",
                "Keep field moisture even during active growth.",
                "Remove weed competition early for better grain fill.",
            ],
            "fertilizer": [
                "Use split nitrogen at sowing and crown root initiation.",
                "Add zinc or sulfur only if deficiency is visible or confirmed.",
            ],
            "pesticide": [
                "Use threshold-based aphid control only after field scouting.",
                "Rotate fungicide groups when rust pressure rises.",
            ],
        },
        "Rice": {
            "hero": "Balance water management and check for stem borer or leaf folder.",
            "guidance": [
                "Maintain shallow standing water instead of deep flooding.",
                "Scout leaf damage and dead hearts every few days.",
                "Keep bunds clean and repair seepage points.",
            ],
            "fertilizer": [
                "Split nitrogen into multiple small doses.",
                "Add potash support where lodging risk is high.",
            ],
            "pesticide": [
                "Use pheromone traps before chemical intervention.",
                "Spray only if pest count crosses threshold levels.",
            ],
        },
    }
    default_profile = {
        "hero": f"Track moisture, nutrients, and pest pressure for {crop_name}.",
        "guidance": [
            f"Scout {crop_name.lower()} twice a week for visible stress and pest build-up.",
            "Adjust irrigation to avoid both water stress and waterlogging.",
            "Remove weeds and damaged plant material early.",
        ],
        "fertilizer": [
            "Follow soil-test based nutrition where possible.",
            "Use split applications instead of one heavy dose.",
        ],
        "pesticide": [
            "Prefer threshold-based spray decisions after scouting.",
            "Rotate pesticide groups and use safety gear during application.",
        ],
    }
    selected = profiles.get(crop_name, default_profile)
    return {"crop": crop_name, **selected}


def build_overview_cards(selected_language, weather, mandi_crop, notifications, posts, reports):
    weather_note = weather.get("summary") or translate(selected_language, "overview_weather_note_ready")
    market_note = translate_format(selected_language, "overview_market_ready", count=len(notifications)) if notifications else translate(selected_language, "overview_market_default")
    community_note = translate_format(selected_language, "overview_community_ready", count=len(posts)) if posts else translate(selected_language, "overview_community_default")
    report_note = translate_format(selected_language, "overview_report_ready", count=len(reports)) if reports else translate(selected_language, "overview_report_default")
    return [
        {
            "eyebrow": translate(selected_language, "showcase_productivity"),
            "title": translate(selected_language, "weather_and_gps"),
            "body": translate(selected_language, "overview_weather_body"),
            "value": weather.get("current", "--"),
            "tone": "cool",
            "note": weather_note,
        },
        {
            "eyebrow": translate(selected_language, "showcase_market"),
            "title": translate(selected_language, "market_rate_and_notifications"),
            "body": translate(selected_language, "overview_market_body"),
            "value": mandi_crop or "All Crops",
            "tone": "warm",
            "note": market_note,
        },
        {
            "eyebrow": translate(selected_language, "showcase_community"),
            "title": translate(selected_language, "farmer_community"),
            "body": translate(selected_language, "overview_community_body"),
            "value": str(len(posts)),
            "tone": "forest",
            "note": community_note,
        },
        {
            "eyebrow": translate(selected_language, "disease_detection"),
            "title": translate(selected_language, "disease_detection"),
            "body": translate(selected_language, "overview_report_body"),
            "value": str(len(reports)),
            "tone": "soft",
            "note": report_note,
        },
    ]


def build_knowledge_cards(selected_language, weather, notifications, posts):
    weather_summary = weather.get("summary") or translate(selected_language, "knowledge_weather_fallback")
    latest_notice = notifications[0]["title"] if notifications else translate(selected_language, "knowledge_notice_fallback")
    latest_post = posts[0]["title"] if posts else translate(selected_language, "knowledge_post_fallback")
    return [
        {
            "title": translate(selected_language, "knowledge_news_title"),
            "body": translate(selected_language, "knowledge_news_body"),
            "items": [
                latest_notice,
                translate(selected_language, "knowledge_news_item"),
            ],
        },
        {
            "title": translate(selected_language, "knowledge_weather_title"),
            "body": translate(selected_language, "knowledge_weather_body"),
            "items": [
                translate_format(selected_language, "knowledge_weather_item", summary=weather_summary),
                translate(selected_language, "knowledge_weather_hint"),
            ],
        },
        {
            "title": translate(selected_language, "farmer_community"),
            "body": translate(selected_language, "knowledge_community_body"),
            "items": [
                latest_post,
                translate(selected_language, "knowledge_community_item"),
            ],
        },
    ]


def detect_disease(crop, symptom, image_name):
    rules = {
        ("soybean", "spots"): ("Likely frogeye leaf spot", "Improve airflow and avoid late irrigation."),
        ("soybean", "yellowing"): ("Possible nutrient or root stress", "Check drainage and review nitrogen balance."),
        ("cotton", "yellowing"): ("Possible whitefly stress", "Inspect leaf undersides and start with sticky traps."),
        ("cotton", "holes"): ("Possible bollworm feeding", "Inspect squares and bolls and confirm with pheromone traps."),
        ("tomato", "spots"): ("Possible early blight or leaf spot", "Remove infected leaves and avoid leaf wetness during irrigation."),
        ("potato", "spots"): ("Possible early blight", "Improve airflow and begin preventive fungicide rotation if confirmed."),
        ("onion", "yellowing"): ("Possible thrips or nutrient stress", "Inspect leaf tips and maintain balanced nutrition."),
        ("rice", "yellowing"): ("Possible nitrogen deficiency or hopper stress", "Check field nutrition and inspect for hopper movement."),
        ("wheat", "yellowing"): ("Possible rust or nutrient deficiency", "Inspect leaves closely and compare with rust symptoms."),
        ("maize", "holes"): ("Possible fall armyworm feeding", "Inspect whorls and use threshold-based control."),
    }
    diagnosis, solution = rules.get((crop.lower(), symptom.lower()), ("General crop stress detected", "Confirm with a local expert before strong chemical use."))
    return diagnosis, solution


def ai_response(question, crop, language_code="en"):
    language_name = get_language_label(language_code)
    crop_name = crop or "your crop"
    lowered = (question or "").lower()
    if "pest" in lowered or "whitefly" in lowered or "bollworm" in lowered:
        return translate(language_code, "ai_pest_reply")
    if "fert" in lowered or "nutrient" in lowered:
        return translate_format(language_code, "ai_nutrient_reply", crop=crop_name)
    if "rain" in lowered or "weather" in lowered:
        return translate(language_code, "ai_weather_reply")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                input=[
                    {
                        "role": "system",
                        "content": translate_format(language_code, "ai_system_prompt", language_name=language_name),
                    },
                    {
                        "role": "user",
                        "content": f"Crop: {crop or 'unknown'}. Farmer question: {question}",
                    },
                ],
            )
            return response.output_text.strip() or translate(language_code, "ai_empty_response")
        except Exception:
            return translate(language_code, "ai_unavailable_reply")
    return translate(language_code, "ai_missing_key_reply")


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form.get("role", "farmer")
        language = request.form.get("language", "en")
        village = request.form.get("village", "").strip()
        district = request.form.get("district", "").strip()
        state = request.form.get("state", "").strip()
        location = build_location(village, district, state)
        crops = request.form.get("crops", "").strip()
        if not name or not email or not password:
            flash(translate(get_active_language_code(), "required_name_email_password"), "error")
        else:
            try:
                get_db().execute(
                    "INSERT INTO users (name, email, password_hash, role, language, location, crops, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, email, generate_password_hash(password), role, language, location, crops, datetime.utcnow().isoformat()),
                )
                get_db().commit()
                flash(translate(get_active_language_code(), "account_created_login_now"), "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash(translate(get_active_language_code(), "email_registered"), "error")
    return render_template(
        "register.html",
        language_options=LANGUAGE_OPTIONS,
        crop_options=["All Crops", *CROP_OPTIONS],
        **get_location_form_options(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["language"] = (user["language"] or "en").strip().lower()
            flash(translate(session["language"], "welcome_back"), "success")
            return redirect(url_for("dashboard"))
        flash(translate(get_active_language_code(), "invalid_credentials"), "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash(translate(get_active_language_code(), "logged_out"), "success")
    return redirect(url_for("home"))


@app.route("/api/translate", methods=["POST"])
@login_required
def translate_api():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or payload.get("input") or "").strip()
    source_lang = (payload.get("source") or payload.get("input_language") or "auto").strip().lower()
    output_lang = (payload.get("output") or payload.get("target") or payload.get("output_language") or "").strip().lower()
    if output_lang:
        translated_text, detected_language = sarvam_translate_text(text, output_lang, source_lang)
        translated_text = translated_text or text
        return jsonify(
            {
                "available": is_translation_configured(),
                "detected_language": detected_language,
                "input": text,
                "output": translated_text,
                "source_language": source_lang,
                "target_language": output_lang,
                "text": {
                    "original": text,
                    output_lang: translated_text,
                },
            }
        )
    requested_targets = payload.get("targets") or ["en", "hi"]
    target_langs = [str(item).strip().lower() for item in requested_targets if str(item).strip()]
    if not target_langs:
        target_langs = ["en", "hi"]
    return jsonify(build_translation_payload(text, tuple(dict.fromkeys(target_langs))))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()
    db = get_db()
    chat_answer = None
    question_translations = None
    selected_language = (user["language"] or "en").strip().lower()
    profile_village, profile_district, profile_state = parse_location_parts(user["location"] or "")
    farmer_profile = {
        "village": profile_village or "Not added",
        "district": profile_district or "Not added",
        "state": profile_state or "Not added",
        "language": get_language_label(user["language"]),
        "crops": user["crops"] or "Not added yet",
        "role": translate(selected_language, user["role"]),
    }
    gps_village = request.form.get("gps_village", profile_village)
    gps_district = request.form.get("gps_district", profile_district)
    gps_state = request.form.get("gps_state", profile_state)
    gps_location = build_location(gps_village, gps_district, gps_state) or (user["location"] or "")
    mandi_district = request.form.get("mandi_district", profile_district)
    mandi_state = request.form.get("mandi_state", profile_state)
    mandi_location = build_location("", mandi_district, mandi_state) or build_location("", profile_district, profile_state)
    mandi_crop = normalize_crop_name(request.form.get("mandi_crop", "")) if request.form.get("mandi_crop") else "All Crops"
    default_crop = parse_crop_list(user["crops"])[0] if parse_crop_list(user["crops"]) else "Cotton"
    advisory_crop = normalize_crop_name(request.form.get("advisory_crop", default_crop))
    disease_crop = normalize_crop_name(request.form.get("crop", default_crop))
    chat_crop = normalize_crop_name(request.form.get("crop_focus", advisory_crop))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_language":
            selected_language = request.form.get("language", "en").strip().lower()
            if selected_language not in LANGUAGE_OPTIONS:
                selected_language = "en"
            db.execute("UPDATE users SET language = ? WHERE id = ?", (selected_language, user["id"]))
            db.commit()
            session["language"] = selected_language
            flash(translate(selected_language, "language_updated"), "success")
            return redirect(url_for("dashboard"))
        if action == "refresh_weather":
            gps_village = request.form.get("gps_village", "").strip()
            gps_district = request.form.get("gps_district", "").strip()
            gps_state = request.form.get("gps_state", "").strip()
            gps_location = build_location(gps_village, gps_district, gps_state)
            if gps_location:
                flash(translate_format(selected_language, "weather_updated_for", location=gps_location), "success")
            else:
                gps_village = profile_village
                gps_district = profile_district
                gps_state = profile_state
                gps_location = user["location"] or ""
                flash(translate(selected_language, "weather_refresh_error"), "error")
        elif action == "refresh_mandi":
            mandi_district = request.form.get("mandi_district", "").strip()
            mandi_state = request.form.get("mandi_state", "").strip()
            mandi_location = build_location("", mandi_district, mandi_state)
            mandi_crop = normalize_crop_name(request.form.get("mandi_crop", "")) if request.form.get("mandi_crop") else "All Crops"
            if mandi_location:
                crop_suffix = "" if mandi_crop == "All Crops" else f" for {mandi_crop}"
                flash(translate_format(selected_language, "mandi_updated_for", location=mandi_location, crop_suffix=crop_suffix), "success")
            else:
                mandi_district = profile_district
                mandi_state = profile_state
                mandi_location = build_location("", profile_district, profile_state)
                flash(translate(selected_language, "mandi_refresh_error"), "error")
        elif action == "refresh_advisory":
            advisory_crop = normalize_crop_name(request.form.get("advisory_crop", default_crop))
            flash(translate_format(selected_language, "advisory_updated_for", crop=advisory_crop), "success")
        elif action == "post":
            title = request.form["title"].strip()
            body = request.form["body"].strip()
            duplicate_count = db.execute(
                """
                SELECT COUNT(*)
                FROM posts
                WHERE LOWER(TRIM(title)) = LOWER(TRIM(?)) AND LOWER(TRIM(body)) = LOWER(TRIM(?))
                """,
                (title, body),
            ).fetchone()[0]
            if duplicate_count >= 1:
                flash(translate(selected_language, "similar_post_exists"), "error")
                return redirect(url_for("dashboard"))
            db.execute(
                "INSERT INTO posts (user_id, title, body, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], title, body, datetime.utcnow().isoformat()),
            )
            db.commit()
            flash(translate(selected_language, "community_post_created"), "success")
            return redirect(url_for("dashboard"))
        elif action == "reply":
            reply_body = request.form.get("reply_body", "").strip()
            post_id = request.form.get("post_id", "").strip()
            if reply_body and post_id:
                db.execute(
                    "INSERT INTO post_replies (post_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                    (post_id, user["id"], reply_body, datetime.utcnow().isoformat()),
                )
                db.commit()
                flash(translate(selected_language, "reply_added"), "success")
            return redirect(url_for("dashboard"))
        elif action == "disease":
            crop = normalize_crop_name(request.form["crop"])
            disease_crop = crop
            symptom = request.form["symptom"].strip()
            image = request.files.get("crop_image")
            image_name = ""
            if image and image.filename:
                image_name = secure_filename(image.filename)
                image.save(UPLOADS_DIR / image_name)
            diagnosis, solution = detect_disease(crop, symptom, image_name)
            db.execute(
                "INSERT INTO disease_reports (user_id, crop, symptom, image_name, diagnosis, solution, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user["id"], crop, symptom, image_name, diagnosis, solution, datetime.utcnow().isoformat()),
            )
            db.commit()
            flash(translate(selected_language, "disease_report_saved"), "success")
            return redirect(url_for("dashboard"))
        elif action == "chat":
            question_text = request.form.get("question", "").strip()
            chat_crop = normalize_crop_name(request.form.get("crop_focus", advisory_crop))
            if question_text:
                question_translations = build_translation_payload(question_text, ("en", "hi"))
            chat_answer = ai_response(question_text, chat_crop, selected_language)

    user = current_user()
    selected_language = (user["language"] or "en").strip().lower()
    posts = db.execute(
        """
        SELECT posts.*, users.name
        FROM posts
        JOIN (
            SELECT MAX(id) AS id
            FROM posts
            GROUP BY LOWER(TRIM(title)), LOWER(TRIM(body))
        ) AS latest_posts ON latest_posts.id = posts.id
        JOIN users ON users.id = posts.user_id
        ORDER BY posts.id DESC
        """
    ).fetchall()
    replies = db.execute(
        "SELECT post_replies.*, users.name FROM post_replies JOIN users ON users.id = post_replies.user_id ORDER BY post_replies.id ASC"
    ).fetchall()
    replies_by_post = {}
    for reply in replies:
        replies_by_post.setdefault(reply["post_id"], []).append(reply)
    reports = db.execute("SELECT disease_reports.*, users.name FROM disease_reports JOIN users ON users.id = disease_reports.user_id ORDER BY disease_reports.id DESC").fetchall()
    notifications = db.execute("SELECT * FROM notifications WHERE user_id IS NULL OR user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    weather = get_weather(gps_location or user["location"])
    market_crop_source = "" if mandi_crop == "All Crops" else mandi_crop
    market_rates = get_market_rates(mandi_location or user["location"], market_crop_source)
    mandi_market_options = get_mandi_market_options(mandi_location or user["location"], market_crop_source)
    advisory = advisory_for(advisory_crop)
    overview_cards = build_overview_cards(selected_language, weather, mandi_crop, notifications, posts, reports, )
    knowledge_cards = build_knowledge_cards(selected_language, weather, notifications, posts)
    return render_template(
        "dashboard.html",
        user=user,
        farmer_profile=farmer_profile,
        posts=posts,
        replies_by_post=replies_by_post,
        reports=reports,
        notifications=notifications,
        weather=weather,
        market_rates=market_rates,
        advisory=advisory,
        overview_cards=overview_cards,
        knowledge_cards=knowledge_cards,
        chat_answer=chat_answer,
        question_translations=question_translations,
        gps_location=gps_location,
        gps_village=gps_village,
        gps_district=gps_district,
        gps_state=gps_state,
        mandi_location=mandi_location,
        mandi_district=mandi_district,
        mandi_state=mandi_state,
        mandi_crop=mandi_crop,
        mandi_market_options=mandi_market_options,
        advisory_crop=advisory_crop,
        disease_crop=disease_crop,
        chat_crop=chat_crop,
        crop_options=CROP_OPTIONS,
        mandi_crop_options=["All Crops", *CROP_OPTIONS],
        language_options=LANGUAGE_OPTIONS,
        current_language=selected_language,
        speech_locale=get_speech_recognition_locale(selected_language),
        t=lambda key: translate(selected_language, key),
        language_label=get_language_label(user["language"]),
        **get_location_form_options(),
        weather_api_ready=weather["api_ready"],
        mandi_api_configured=bool(os.getenv("MANDI_API_KEY")),
        ai_api_configured=bool(os.getenv("OPENAI_API_KEY")),
        translation_api_ready=is_translation_configured(),
    )


@app.route("/expert")
@login_required
@role_required("expert", "admin")
def expert_panel():
    db = get_db()
    posts = db.execute(
        """
        SELECT posts.*, users.name, users.location
        FROM posts
        JOIN (
            SELECT MAX(id) AS id
            FROM posts
            GROUP BY LOWER(TRIM(title)), LOWER(TRIM(body))
        ) AS latest_posts ON latest_posts.id = posts.id
        JOIN users ON users.id = posts.user_id
        ORDER BY posts.id DESC
        """
    ).fetchall()
    reports = db.execute("SELECT disease_reports.*, users.name FROM disease_reports JOIN users ON users.id = disease_reports.user_id ORDER BY disease_reports.id DESC").fetchall()
    return render_template("expert.html", posts=posts, reports=reports)


@app.route("/admin", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_panel():
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO notifications (user_id, title, body, created_at) VALUES (?, ?, ?, ?)",
            (request.form.get("target_user_id") or None, request.form["title"].strip(), request.form["body"].strip(), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash(translate(get_active_language_code(), "notification_created"), "success")
        return redirect(url_for("admin_panel"))
    users = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    notifications = db.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
    return render_template("admin.html", users=users, notifications=notifications)


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    cleanup_demo_content()
    cleanup_duplicate_posts()
    remove_uploaded_filenames_from_reports()
    port = get_flask_port()
    print(f"KRUSHIGOLD.AI running at http://127.0.0.1:{port}")
    app.run(debug=True, host="127.0.0.1", port=port, load_dotenv=False, use_reloader=False)
