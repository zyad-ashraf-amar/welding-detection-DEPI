import streamlit as st
import torch
from PIL import Image
import cv2
import numpy as np
import os
import tempfile
import time
from detect import run, run_realtime
import shutil
import pathlib
import platform
from io import BytesIO
import base64
from streamlit_option_menu import option_menu

# Dynamically set path handling for different OS
if platform.system() == 'Windows':
    pathlib.PosixPath = pathlib.WindowsPath

# Set page config
st.set_page_config(page_title="Welding Detection App", page_icon="🔍", layout="wide")

# Custom CSS to improve UI
st.markdown("""
<style>
    .stApp {
        max-width: 4000px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
    }
    .uploadedFile {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .detectionResults {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
    }
    .download-btn {
        display: inline-block;
        padding: 0.5em 1em;
        color: #ffffff;
        background-color: #003366;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
    }
    .download-btn:hover {
        background-color: #002244;
    }
</style>
""", unsafe_allow_html=True)

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
    href = f'<a href="data:file/jpg;base64,{img_str}" download="{filename}" class="download-btn">{text}</a>'
    return href

def get_video_download_link(video_path, filename, text):
    """Generate a download link for a video"""
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    b64 = base64.b64encode(video_bytes).decode()
    href = f'<a href="data:file/mp4;base64,{b64}" download="{filename}" class="download-btn">{text}</a>'
    return href

def main():
    st.title('🔍 Welding Detection App')
    
    # Sidebar
    with st.sidebar:
        st.header('Settings')
        
        # Model selection
        weights_path = st.text_input(
            'Model Weights Path',
            'best.pt',
            help='Path to your YOLOv5 weights file'
        )
        
        # Confidence threshold
        confidence = st.slider(
            'Confidence Threshold',
            min_value=0.0,
            max_value=1.0,
            value=0.10,
            step=0.05,
            help='Adjust the confidence threshold for object detection'
        )
        
        # Input type selection using option_menu
        selected = option_menu(
            "Select Input Type",
            ["Image", "Video", "Real-time"],
            icons=['file-image', 'camera-video', 'camera'],
            menu_icon="cast",
            default_index=0,
        )
    
    # Main content area
    if selected == "Image":
        st.header("Image Detection")
        uploaded_files = st.file_uploader(
            label='Choose image file(s)',
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            cols = st.columns(3)
            for i, uploaded_file in enumerate(uploaded_files):
                with cols[i % 3]:
                    st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
            
            if st.button('Detect Objects', key='detect_image'):
                clean_previous_detections()
                
                progress_bar = st.progress(0)
                for i, uploaded_file in enumerate(uploaded_files):
                    with st.spinner(f'Detecting objects in image {i+1}/{len(uploaded_files)}...'):
                        # Save uploaded image temporarily
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            img_path = tmp_file.name
                        
                        try:
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
                                        
                                        # Create two columns for image and detections
                                        col1, col2 = st.columns([3, 2])
                                        
                                        with col1:
                                            st.image(result_image, caption=f"Processed {uploaded_file.name}", use_column_width=True)
                                            # Add download button for the processed image
                                            st.markdown(get_image_download_link(result_image, f"processed_{uploaded_file.name}", "📥 Download Processed Image"), unsafe_allow_html=True)
                                        
                                        with col2:
                                            st.subheader(f'Detections for {uploaded_file.name}')
                                            # Display detections
                                            labels_dir = output_path / 'labels'
                                            if labels_dir.exists():
                                                for txt_file in labels_dir.iterdir():
                                                    if txt_file.suffix == '.txt':
                                                        with open(txt_file) as f:
                                                            detections = f.readlines()
                                                        for detection in detections:
                                                            st.write(f'- {detection.strip()}')
                                        break
                        except Exception as e:
                            st.error(f"An error occurred while processing {uploaded_file.name}: {str(e)}")
                        finally:
                            # Clean up temporary file
                            os.unlink(img_path)
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success("All images processed successfully!")
    
    elif selected == "Video":
        st.header("Video Detection")
        video_path = load_video()
        
        if video_path is not None:
            st.video(video_path)
            
            if st.button('Detect Objects', key='detect_video'):
                with st.spinner('Processing video...'):
                    # Clean previous detections
                    clean_previous_detections()
                    
                    try:
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
                                    st.markdown(get_video_download_link(str(video_file), "processed_video.mp4", "📥 Download Processed Video"), unsafe_allow_html=True)
                                    break
                            
                            # Display detections
                            labels_dir = output_path / 'labels'
                            if labels_dir.exists():
                                with st.expander('Detections', expanded=False):
                                    for txt_file in labels_dir.iterdir():
                                        if txt_file.suffix == '.txt':
                                            with open(txt_file) as f:
                                                detections = f.readlines()
                                            for detection in detections:
                                                st.write(f'- {detection.strip()}')
                            st.success("Video processed successfully!")
                    except Exception as e:
                        st.error(f"An error occurred while processing the video: {str(e)}")
                    finally:
                        # Clean up temporary file
                        os.unlink(video_path)

    elif selected == "Real-time":
        st.header("Real-time Detection")
        
        # Initialize the webcam
        cam_options = st.selectbox("Select Camera", ["Webcam", "Mobile Camera"])
        
        if cam_options == "Mobile Camera":
            st.info("To use mobile camera, please follow these steps:")
            st.markdown("""
            1. Install 'IP Webcam' app on your Android phone
            2. Open the app and click 'Start server'
            3. Enter the IP address shown in the app below
            """)
            ip_address = st.text_input("Enter IP Webcam address", "http://192.168.1.X:8080/video")
            camera_source = ip_address if st.button("Start Mobile Camera") else None
        else:
            camera_source = 0  # Default webcam
            
        if st.button("Start Detection", key="start_realtime"):
            try:
                # Initialize detection model
                process_frame = run_realtime(
                    weights=weights_path,
                    conf_thres=confidence,
                    device=""
                )
                
                # Initialize video capture
                cap = cv2.VideoCapture(camera_source)
                
                if not cap.isOpened():
                    st.error("Error: Could not open camera.")
                    return
                
                # Create a placeholder for the video feed
                stframe = st.empty()
                stop_button = st.button("Stop")
                
                while not stop_button:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Error: Could not read frame.")
                        break
                    
                    # Process frame
                    frame = process_frame(frame)
                    
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Display the frame
                    stframe.image(frame, channels="RGB", use_column_width=True)
                    
                cap.release()
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


if __name__ == '__main__':
    main()