# welding-detection-DEPI
Weld Defect Detection
=====================

# Overview
--------

This project focuses on developing a computer vision solution to detect and classify welding defects, ensuring improved quality control in welding processes. The system identifies welding quality as **Good Welding**, **Bad Welding**, or detects specific defects like **Porosity** and **Defect**.

# Features
--------

*   **YOLOv5-based Model**: Utilized YOLOv5 for object detection to ensure efficient and accurate classification.
*   **Unified Dataset**: Preprocessed and merged **6 different datasets** into a single comprehensive dataset.
*   **Interactive Web App**: Deployed the model using **Streamlit** for real-time defect detection and visualization.

# Model Performance  
| Metric        | Value  |  
|---------------|--------|  
| **mAP50**     | 0.934  |  

## Class-wise Performance  
| Class          | Precision | Recall | mAP50 |  
|----------------|-----------|--------|-------|  
| **Defect**     | 0.957     | 0.942  | 0.967 |  
| **Good Welding** | 0.736   | 0.830  | 0.839 |  
| **Porosity**   | 0.910     | 0.918  | 0.962 |  
| **Bad Welding** | 0.928   | 0.911  | 0.969 |  


# Installation
------------

1.  Clone the repository:
    
    ```bash
    git clone https://github.com/yourusername/weld-defect-detection.git  
    cd weld-defect-detection  
    ```
    
2.  Install dependencies:
    
    ```bash
    pip install -r requirements.txt  
    ```
    
3.  Download the pre-trained YOLOv5 weights and place them in the appropriate directory.
    

# Usage
-----

1.  Run the Streamlit app:
    
    ```bash
    streamlit run app4.py  
    ```
    
2.  Upload welding images and view real-time defect detection results.
    

# Dataset
-------

The dataset is a combination of **6 different datasets** preprocessed into a unified format for training. Details on preprocessing steps can be found in the `notebooks` folder.

# Results
-------

The model provides robust performance, achieving a **mAP50 of 0.934**, ensuring accurate defect detection across all defined classes.

# Future Enhancements
-------------------

*   Optimize the model for edge devices to enable real-time deployment on welding machines.
*   Extend the dataset with more diverse examples to improve robustness.

## Contributing
------------

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## Contact
-------

For any inquiries, reach out to zyadashrafamar@gmail.com.
