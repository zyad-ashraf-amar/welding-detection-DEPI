import streamlit as st
import torch
from PIL import Image
import cv2
import numpy as np
import os
import tempfile
import time
from detect import run
import shutil
import pathlib
import platform
from io import BytesIO
import base64

# Dynamically set path handling for different OS
if platform.system() == 'Windows':
    pathlib.PosixPath = pathlib.WindowsPath

@st.cache_data
def load_image(uploaded_file):
    """Load an image and return the image array"""
    image = Image.open(uploaded_file)
    return image

def load_video():
    """Load a video and return the uploaded file"""
    uploaded_file = st.file_uploader(label='Choose a video file', type=['mp4', 'avi', 'mov'])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        st.video(uploaded_file)
        return tfile.name
    return None

def get_detection_folder():
    """Get the path to the detection results folder"""
    runs_dir = pathlib.Path(os.getcwd()) / 'runs' / 'detect'
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir

def clean_previous_detections():
    """Clean up previous detection results"""
    runs_dir = get_detection_folder()
    for item in runs_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)

def get_latest_detection_folder():
    """Get the path to the latest detection results"""
    runs_dir = get_detection_folder()
    exp_dirs = [d for d in runs_dir.iterdir() if d.name.startswith('exp')]
    if not exp_dirs:
        return None
    latest_exp = max(exp_dirs, key=lambda x: x.stat().st_ctime)
    return latest_exp

def get_image_download_link(img, filename, text):
    """Generate a download link for an image"""
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/jpg;base64,{img_str}" download="{filename}">{text}</a>'
    return href

def get_video_download_link(video_path, filename, text):
    """Generate a download link for a video"""
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    b64 = base64.b64encode(video_bytes).decode()
    href = f'<a href="data:file/mp4;base64,{b64}" download="{filename}">{text}</a>'
    return href

def main():
    st.title('Welding Detection')
    
    # Sidebar
    st.sidebar.title('Settings')
    
    # Model selection
    weights_path = st.sidebar.text_input(
        'Model Weights Path',
        'best.pt',
        help='Path to your YOLOv5 weights file'
    )
    
    # Confidence threshold
    confidence = st.sidebar.slider(
        'Confidence Threshold',
        min_value=0.0,
        max_value=1.0,
        value=0.10
    )
    
    # Input type selection
    input_type = st.sidebar.radio(
        'Select Input Type',
        ['Image', 'Video']
    )
    
    if input_type == 'Image':
        uploaded_files = st.file_uploader(
            label='Choose image file(s)',
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.image(uploaded_file, caption=uploaded_file.name)
            
            if st.button('Detect Objects'):
                clean_previous_detections()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    with st.spinner(f'Detecting objects in image {i+1}/{len(uploaded_files)}...'):
                        # Save uploaded image temporarily
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            img_path = tmp_file.name
                        
                        # Run detection
                        run(
                            weights=weights_path,
                            source=img_path,
                            conf_thres=confidence,
                            save_txt=True,
                            save_conf=True,
                            project=str(get_detection_folder())
                        )
                        
                        # Display results
                        output_path = get_latest_detection_folder()
                        if output_path:
                            # Find and display the result image
                            for img_file in output_path.iterdir():
                                if img_file.suffix in ['.jpg', '.jpeg', '.png']:
                                    result_image = Image.open(img_file)
                                    st.image(result_image, caption=f"Processed {uploaded_file.name}")
                                    
                                    # Add download button for the processed image
                                    st.markdown(get_image_download_link(result_image, f"processed_{uploaded_file.name}", "Download Processed Image"), unsafe_allow_html=True)
                                    break
                            
                            # Display detections
                            labels_dir = output_path / 'labels'
                            if labels_dir.exists():
                                st.write(f'Detections for {uploaded_file.name}:')
                                for txt_file in labels_dir.iterdir():
                                    if txt_file.suffix == '.txt':
                                        with open(txt_file) as f:
                                            detections = f.readlines()
                                        for detection in detections:
                                            st.write(f'- {detection.strip()}')
                        
                        # Clean up temporary file
                        os.unlink(img_path)
    
    else:  # Video input
        video_path = load_video()
        
        if video_path is not None:
            if st.button('Detect Objects'):
                with st.spinner('Processing video...'):
                    # Clean previous detections
                    clean_previous_detections()
                    
                    # Run detection
                    run(
                        weights=weights_path,
                        source=video_path,
                        conf_thres=confidence,
                        save_txt=True,
                        save_conf=True,
                        project=str(get_detection_folder())
                    )
                    
                    # Display results
                    output_path = get_latest_detection_folder()
                    if output_path:
                        # Find and display the result video
                        for video_file in output_path.iterdir():
                            if video_file.suffix == '.mp4':
                                st.video(str(video_file))
                                
                                # Add download button for the processed video
                                st.markdown(get_video_download_link(str(video_file), "processed_video.mp4", "Download Processed Video"), unsafe_allow_html=True)
                                break
                        
                        # Display detections
                        labels_dir = output_path / 'labels'
                        if labels_dir.exists():
                            st.write('Detections:')
                            for txt_file in labels_dir.iterdir():
                                if txt_file.suffix == '.txt':
                                    with open(txt_file) as f:
                                        detections = f.readlines()
                                    for detection in detections:
                                        st.write(f'- {detection.strip()}')
                    
                    # Clean up temporary file
                    os.unlink(video_path)

if __name__ == '__main__':
    main()