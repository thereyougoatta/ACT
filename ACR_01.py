import streamlit as st
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import io
import requests
import json
import time
import os
import base64
import hashlib
import hmac

# Parameters for audio recording
RATE = 44100
RECORD_SECONDS = 11
# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state['history'] = []

def record_audio():
    st.text("Recording...")
    
    audio_data = sd.rec(int(RECORD_SECONDS * RATE), samplerate=RATE, channels=1, dtype='int16')
    sd.wait()
    
    audio_bytes = io.BytesIO()
    write(audio_bytes, RATE, audio_data)
    audio_bytes.seek(0)  # Rewind the stream to the beginning
    
    st.text("Recording finished.")
    return audio_bytes

def make_api_call(audio_bytes):
    access_key = "e519e7ed020c3d0fc97ec0066199801d"  # 여기에 본인의 access_key
    access_secret = "2hFRraVEUoyRhgIiaV03r8AEayEDovsSMtlt9M84"  # 여기에 본인의 access_secret
    requrl = "http://identify-ap-southeast-1.acrcloud.com/v1/identify"
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = time.time()

    string_to_sign = f"{http_method}\n{http_uri}\n{access_key}\n{data_type}\n{signature_version}\n{str(timestamp)}"
    sign = base64.b64encode(hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()).decode('ascii')

    files = [
        ('sample', ('sample.wav', audio_bytes, 'audio/wav'))
    ]

    data = {
        'access_key': access_key,
        'sample_bytes': audio_bytes.getbuffer().nbytes,
        'timestamp': str(timestamp),
        'signature': sign,
        'data_type': data_type,
        'signature_version': signature_version
    }

    response = requests.post(requrl, files=files, data=data)
    response.encoding = "utf-8"
    return response

def identify_song(audio_bytes):
    response = make_api_call(audio_bytes)
    response_data = json.loads(response.text)

    try:
        music_info = response_data.get('metadata', {})
        if 'music' in music_info:
            music_info = music_info['music'][0]
        elif 'humming' in music_info:
            music_info = music_info['humming'][0]
        else:
            st.warning("No music or humming data found.")
            return

        track_name = music_info.get('title', 'Unknown Title')
        artist = music_info.get('artists', [{}])[0].get('name', 'Unknown Artist')
        album = music_info.get('album', {}).get('name', 'Unknown Album')

        if 'spotify' in music_info.get('external_metadata', {}):
            spotify_track_url = f"https://open.spotify.com/track/{music_info['external_metadata']['spotify']['track']['id']}"
        else:
            spotify_track_url = "Spotify link not available"

        if 'youtube' in music_info.get('external_metadata', {}):
            youtube_video_url = f"https://www.youtube.com/watch?v={music_info['external_metadata']['youtube']['vid']}"
        else:
            youtube_video_url = "YouTube link not available"

        st.success("Song identified!")
        st.write(f"Track Name: {track_name}")
        st.write(f"Artist: {artist}")
        st.write(f"Album: {album}")
        st.write(f"Spotify Track URL: {spotify_track_url}")
        st.write(f"YouTube Video URL: {youtube_video_url}")

        # History에 추가
        st.session_state['history'].append({
            'track_name': track_name,
            'artist': artist,
            'album': album,
            'spotify_url': spotify_track_url,
            'youtube_url': youtube_video_url
        })

    except KeyError as e:
        st.error(f"Error processing response: {e}")

def main():
    st.title("음악 식별기")
    st.sidebar.title("노래 기록 🎶")
    
    if st.session_state['history']:
        for entry in st.session_state['history']:
            st.sidebar.write(f"**Track Name:** {entry['track_name']}")
            st.sidebar.write(f"**Artist:** {entry['artist']}")
            st.sidebar.write(f"**Album:** {entry['album']}")
            st.sidebar.write(f"[Spotify Link]({entry['spotify_url']}) | [YouTube Link]({entry['youtube_url']})")
            st.sidebar.write("---")
    else:
        st.sidebar.write("기록이 없습니다. 노래를 불러보세요!")
        
    if st.button("🎤 녹음 시작"):
        audio_bytes = record_audio()
 