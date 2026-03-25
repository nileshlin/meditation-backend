import streamlit as st
import requests
import time

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Meditation Audio Generator UI", page_icon="🧘", layout="centered")

st.title("🧘 Meditation Audio Generator")
st.markdown("Test the meditation audio generation flow and monitor background generation progress.")

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "med_id" not in st.session_state:
    st.session_state.med_id = None
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

prompt = st.text_area("What kind of meditation do you need today?", "I need a short meditation for sleep, very relaxing and calm.")

if st.button("Generate Meditation Audio", disabled=st.session_state.is_generating):
    if not prompt.strip():
        st.error("Please enter a prompt.")
    else:
        st.session_state.is_generating = True
        
        try:
            with st.spinner("Creating Session..."):
                # 1. Create session
                res = requests.post(f"{BASE_URL}/session/")
                res.raise_for_status()
                session_id = res.json()["id"]
                st.session_state.session_id = session_id
                
            with st.spinner("Analyzing prompt with Agent..."):
                # 2. Send message
                res = requests.post(f"{BASE_URL}/session/{session_id}/messages", json={"content": prompt})
                res.raise_for_status()
            
            with st.spinner("Starting background meditation generation..."):
                # 3. Start meditation
                res = requests.post(f"{BASE_URL}/meditation/sessions/{session_id}/start")
                res.raise_for_status()
                med_id = res.json()["id"]
                st.session_state.med_id = med_id
                
            st.success(f"Generation started successfully! (Session ID: {session_id}, Meditation ID: {med_id})")
            
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error: {e.response.text}")
            st.session_state.is_generating = False
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.is_generating = False

# Progress Polling UI
if st.session_state.is_generating and st.session_state.med_id:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while st.session_state.is_generating:
        try:
            res = requests.get(f"{BASE_URL}/meditation/{st.session_state.med_id}")
            res.raise_for_status()
            data = res.json()
            
            status = data.get("status", "pending")
            progress = data.get("progress", 0)
            
            progress_bar.progress(progress / 100.0)
            status_text.text(f"Status: {status.upper()} | Progress: {progress}%")
            
            if status.lower() == "completed":
                st.session_state.is_generating = False
                st.success("Meditation audio generated successfully!")
                
                # Render results
                st.subheader("Generated Audio Blocks")
                blocks = data.get("audio_blocks", [])
                
                for block in blocks:
                    block_type = "🗣️ Voice + Music" if block.get("has_voice") else "🎵 Music Only"
                    st.markdown(f"**Block {block['block']}** ({block['duration']}s) - {block_type}")
                    if block.get("background_audio"):
                        st.caption(f"Background: {block['background_audio']}")
                    st.audio(block["url"])
                    st.divider()
                    
                break
                
            elif status.lower() == "failed":
                st.session_state.is_generating = False
                st.error("Audio generation failed on the server.")
                break
                
            time.sleep(2.0)
            
        except Exception as e:
            status_text.text(f"Error checking status: {e}")
            time.sleep(3.0)
