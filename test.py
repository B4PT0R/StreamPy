import streamlit as st
from audiorecorder import audiorecorder
from streamlit_deferrer import KeyManager
from pydub import AudioSegment
from speech_recognition import Recognizer, AudioData, AudioFile
import io
import wave

state=st.session_state

if not 'km' in state:
    state.km=KeyManager()

if not 'rec_key' in state:
    state.rec_key=state.km.gen_key()

if not 'texts' in state:
    state.texts=[]

def speech_to_text(audio):
    recognizer = Recognizer()
    with open('audio.mp3', 'wb') as f:
        f.write(audio.tobytes())
    with AudioFile('audio.mp3') as source:
        audio_data=recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except:
        return "Error recognizing audio"

audio = audiorecorder("Click to record", "Recording...",key=state.rec_key)

if len(audio) > 0:
    state.texts.append(speech_to_text(audio))
    state.rec_key=state.km.gen_key() 

for text in state.texts:
    st.text(text)