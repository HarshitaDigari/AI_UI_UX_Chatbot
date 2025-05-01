import streamlit as st
from dotenv import load_dotenv
import os
import re
import speech_recognition as sr
import logging

try:
    import google.generativeai as genai
except ImportError:
    st.error("The 'google-generativeai' package is not installed. Run 'pip install google-generativeai==0.8.2' in your virtual environment.")
    st.stop()

try:
    import pyaudio
except ImportError:
    st.error("The 'pyaudio' package is not installed. Run 'pip install pyaudio' or follow macOS instructions in README.md.")
    st.stop()

#  Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(_name_)

# Load environment variables
load_dotenv()

# Inbuilt Gemini API key (replace with your full key or use .env)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or 'AIzaSyDisMGPndMSZUab9sLmsjc7idryAQZ3xoM'

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}. Please check your API key.")
    st.stop()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_login_form' not in st.session_state:
    st.session_state.show_login_form = False
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'mic_active' not in st.session_state:
    st.session_state.mic_active = False
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Yo! I'm DesignBuddy, here to help with UI/UX design. What's up?"}
    ]

# Custom CSS for styling with black background
st.markdown("""
    <style>
    .stApp {
        background: #000000;
        color: #e0e0e0;
    }
    .login-button, .home-button, .mic-button {
        background-color: #e67e22;
        color: white;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        border: none;
        margin: 5px;
        font-size: 14px;
    }
    .login-button:hover, .home-button:hover, .mic-button:hover {
        background-color: #d35400;
    }
    .main-header {
        font-size: 36px;
        color: #ff69b4;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }
    .sub-header {
        font-size: 24px;
        color: #ffc1cc;
    }
    .content {
        font-size: 16px;
        color: #d0d0d0;
        line-height: 1.6;
    }
    .stTextInput > div > input, .stChatInput > div > input {
        background-color: #333333;
        color: #e0e0e0;
        border: 1px solid #e67e22;
    }
    .stButton > button {
        background-color: #e67e22;
        color: white;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #d35400;
    }
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        margin-bottom: 20px;
        padding: 10px;
    }
    .stForm {
        position: sticky;
        bottom: 0;
        background: #000000;
        padding: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Function to transcribe audio using speech_recognition
def transcribe_audio():
    if st.session_state.mic_active:
        return  # Prevent multiple activations
    logger.info("Starting audio transcription")
    recognizer = sr.Recognizer()
    st.session_state.mic_active = True
    st.session_state.transcribed_text = "Listening..."
    try:
        with sr.Microphone() as source:
            logger.info("Microphone active, adjusting for noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Listening for audio (up to 10 seconds)...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            logger.info("Audio captured, transcribing...")
            # Transcribe using Google's Speech Recognition
            text = recognizer.recognize_google(audio)
            st.session_state.transcribed_text = text
            logger.info(f"Transcription successful: {text}")
    except sr.WaitTimeoutError:
        st.session_state.transcribed_text = "No speech detected. Try speaking louder or closer to the microphone."
        logger.warning("No speech detected")
    except sr.UnknownValueError:
        st.session_state.transcribed_text = "Could not understand audio. Try again."
        logger.warning("Could not understand audio")
    except sr.RequestError as e:
        st.session_state.transcribed_text = f"Speech recognition error: {e}. Check internet connection."
        logger.error(f"Speech recognition error: {e}")
    except PermissionError:
        st.session_state.transcribed_text = "Microphone access denied. Check macOS permissions (System Settings > Privacy & Security > Microphone)."
        logger.error("Microphone permission denied")
    except Exception as e:
        if "FLAC conversion utility not available" in str(e):
            st.session_state.transcribed_text = "FLAC utility missing. Install it with 'brew install flac' on macOS. See README.md."
            logger.error("FLAC conversion utility not available")
        else:
            st.session_state.transcribed_text = f"Error: {str(e)}. Ensure microphone is configured and internet is stable."
            logger.error(f"Unexpected error: {e}")
    finally:
        st.session_state.mic_active = False
        logger.info("Transcription ended")
        # Avoid st.rerun() in callback; rely on form submission to update UI

# Landing page
def landing_page():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h1 class='main-header'>Welcome to DesignBuddy 🎨</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("Login", key="login_btn", help="Click to log in"):
            st.session_state.show_login_form = True

    st.markdown("<h2 class='sub-header'>What is UI/UX?</h2>", unsafe_allow_html=True)
    st.markdown("""
        <p class='content'>
        UI (User Interface) design focuses on the visual layout and interactive elements of a product, like buttons, colors, and typography. 
        UX (User Experience) design ensures the product is intuitive, efficient, and enjoyable, emphasizing user needs and workflows. 
        Together, UI/UX create seamless, user-friendly digital experiences.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='sub-header'>How DesignBuddy Works</h2>", unsafe_allow_html=True)
    st.markdown("""
        <p class='content'>
        DesignBuddy is your AI-powered UI/UX assistant! Powered by the Gemini API, it provides concise, real-time advice on design principles, 
        tools, feedback, and creative ideas. Log in, speak or type queries using the microphone, submit, and get text responses. Perfect for students and designers!
        </p>
    """, unsafe_allow_html=True)

    if st.session_state.show_login_form:
        st.markdown("### Login to Access DesignBuddy")
        email = st.text_input("Email", placeholder="user@domain.com")
        password = st.text_input("Password", type="password")
        
        if st.button("Submit"):
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_regex, email):
                st.error("Please enter a valid email address (e.g., user@domain.com).")
            elif not password:
                st.error("Password cannot be empty.")
            else:
                st.session_state.logged_in = True
                st.session_state.show_login_form = False
                st.success("Login successful! Accessing DesignBuddy...")
                st.rerun()

# Chatbot page
def chatbot_page():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("DesignBuddy 🎨")
    with col2:
        if st.button("Home", key="home_btn", help="Return to home page"):
            st.session_state.logged_in = False
            st.session_state.show_login_form = False
            st.session_state.messages = [
                {"role": "assistant", "content": "Yo! I'm DesignBuddy, here to help with UI/UX design. What's up?"}
            ]
            st.session_state.transcribed_text = ""
            st.rerun()

    st.markdown("Your UI/UX design assistant! Ask about principles, tools, feedback, or ideas! 😎 Use the microphone to speak your query, then submit.")

    # Chat history container
    with st.container():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input form at the bottom
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([8, 1])
        with col1:
            prompt = st.text_input(
                label="Ask away...",
                value=st.session_state.transcribed_text if not st.session_state.mic_active else "Listening...",
                key="chat_input_form",
                placeholder="Type or speak your query..."
            )
        with col2:
            mic_button = st.form_submit_button("🎙️", on_click=transcribe_audio, disabled=st.session_state.mic_active)
        submit_button = st.form_submit_button("Submit")

        if submit_button and prompt and not st.session_state.mic_active and prompt != "Listening...":
            logger.info(f"Submitting prompt: {prompt}")
            st.session_state.transcribed_text = ""
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    response = model.generate_content(
                        f"You are a UI/UX design assistant. Provide a concise response (under 100 words) for: '{prompt}'"
                    )
                    response_text = response.text
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    logger.info(f"Response generated: {response_text}")
                except Exception as e:
                    error_msg = f"Oops, something went wrong with the Gemini API: {e}. Try again?"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    logger.error(f"Gemini API error: {e}")
            st.rerun()

# Render landing or chatbot page based on login state
if not st.session_state.logged_in:
    landing_page()
else:
    chatbot_page()