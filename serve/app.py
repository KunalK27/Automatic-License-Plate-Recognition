"""This is an Object detection and Optical Character Recognition(OCR) app that enables a user to

- Select or upload an image.
- Get a annotated and cropped license plate image.
- Play around with Image enhance options (OpenCV).
- Get OCR Prediction using various options.

"""

# streamlit configurations and options
import streamlit as st
from streamlit import caching
#st.set_page_config(page_title="Ex-stream-ly Cool App", page_icon="😎", layout="centered", initial_sidebar_state="expanded")
st.set_option('deprecation.showfileUploaderEncoding', False)

from utils.retinanet_helper import retinanet_detector, draw_detections, inference, load_image, image_preprocessing, load_retinanet
from utils.ocr import try_all_OCR, easy_OCR, OCR
from utils.yolov3_helper import yolo_inference, yolo_detector
from utils.enhance import cannize_image, enhance_crop, cropped_image

import os
from os import listdir
from os.path import isfile, join
import cv2
import numpy as np
from PIL import Image
import time
import random
import pandas as pd

try:
    import easyocr
except:
    pass

# miscellaneous modules
# from pyngrok import ngrok
import webbrowser

# https://github.com/keras-team/keras/issues/13353#issuecomment-545459472
import keras.backend.tensorflow_backend as tb
tb._SYMBOLIC_SCOPE.value = True

#============================ About ==========================
def about():

    st.warning("""
    ## \u26C5 Behind The Scenes
        """)
    st.success("""
    To see how it works, please click the button below!
        """)
    github = st.button("👉🏼 Click Here To See How It Works")
    if github:
        github_link = "https://github.com/SamratRode/Automatic-License-Plate-Recognition"
        try:
            webbrowser.open(github_link)
        except:
            st.error("""
                ⭕ Something Went Wrong!!! Please Try Again Later!!!
                """)
    st.info("Built with Streamlit by [Samrat, Anika and Aiswarya 😎](https://github.com/SamratRode)")


# @st.cache(suppress_st_warning=True, allow_output_mutation=True, show_spinner=True)
def about_yolo():
    yolo_dir = 'banners/yolo/'
    yolo_banner = random.choice(listdir(yolo_dir))
    st.sidebar.image(yolo_dir+yolo_banner, use_column_width=True)
    
    st.sidebar.info(
        "**YOLO (“You Only Look Once”)** is an effective real-time object recognition algorithm, \
        first described in the seminal 2015 [**paper**](https://arxiv.org/abs/1506.02640) by Joseph Redmon et al.\
        It's a network that uses **Deep Learning (DL)** algorithms for **object detection**. \
        \n\n[**YOLO**](https://missinglink.ai/guides/computer-vision/yolo-deep-learning-dont-think-twice/) performs object detection \
        by classifying certain objects within the image and **determining where they are located** on it.\
        \n\nFor example, if you input an image of a herd of sheep into a YOLO network, it will generate an output of a vector of bounding boxes\
            for each individual sheep and classify it as such. Yolo is based on algorithms based on regression━they **scan the whole image** and make predictions to **localize**, \
        identify and classify objects within the image. \
        \n\nAlgorithms in this group are faster and can be used for **real-time** object detection.\
        **YOLO V3** is an **improvement** over previous YOLO detection networks. \
        Compared to prior versions, it features **multi-scale detection**, stronger feature extractor network, and some changes in the loss function.\
        As a result, this network can now **detect many more targets from big to small**. \
        And, of course, just like other **single-shot detectors**, \
        YOLO V3 also runs **quite fast** and makes **real-time inference** possible on **GPU** devices.")


# @st.cache(suppress_st_warning=True, allow_output_mutation=True, show_spinner=True)
def about_retinanet():
    od_dir = 'banners/Object detection/'
    od_banner = random.choice(listdir(od_dir))
    st.sidebar.image(od_dir+od_banner, use_column_width=True)

    st.sidebar.info(
        "[RetinaNet](https://arxiv.org/abs/1708.02002) is **one of the best one-stage object detection models** that has proven to work well with dense and small scale objects. \
        For this reason, it has become a **popular** object detection model to be used with aerial and satellite imagery. \
        \n\n[RetinaNet architecture](https://www.mantralabsglobal.com/blog/better-dense-shape-detection-in-live-imagery-with-retinanet/) was published by **Facebook AI Research (FAIR)** and uses Feature Pyramid Network (FPN) with ResNet. \
        This architecture demonstrates **higher accuracy** in situations where *speed is not really important*. \
        RetinaNet is built on top of FPN using ResNet.")


#================================= Functions =================================

def streamlit_preview_image(image):
    st.sidebar.image(
                image,
                use_column_width=True,
                caption = "Original Image")

def streamlit_output_image(image, caption):
    st.image(image,
            use_column_width=True,
            caption = caption)

def streamlit_OCR(output_image):

    st.write("## 🎅 Bonus:- Optical Character Recognition (OCR)")
    
    st.error("Note: OCR is performed on the enhanced cropped images.")
    
    note = st.empty()
    OCR_type = st.radio("OCR Mode",["Google's Tesseract OCR","easy_OCR","Secret Combo All-out Attack!!"])
    button = st.empty()
    ocr_text = st.empty()
    if button.button('Recognize Characters !!'):
        
        if OCR_type == "Google's Tesseract OCR":
            # try:
            tessy_ocr = OCR(output_image)
            
            if len(tessy_ocr) == 0:
                ocr_text.error("Google's Tesseract OCR Failed! :sob:")

            else:
                ocr_text.success("Google's Tesseract OCR: " + tessy_ocr)
                st.error("Researching Google's Tesseract OCR is a work in progress 🚧\
            \nThe results might be unreliable.")

        elif OCR_type == "easy_OCR":

            try:
                easy_ocr = easy_OCR(output_image)
                ocr_text.success("easy OCR: " + easy_ocr)

            except NameError:
                ocr_text.error("EasyOCR not installed")

            except ModuleNotFoundError:
                ocr_text.error("EasyOCR not installed")

            except:
                ocr_text.error("Easy OCR Failed! :sob:")

        elif OCR_type == "Secret Combo All-out Attack!!":

            try_all_OCR(output_image)

def multi_crop(image, crop_list):

    if len(crop_list)!=0: 
        # https://dbader.org/blog/python-min-max-and-nested-lists
        [max_crop, max_conf] = max(crop_list, key=lambda x: x[1])

        st.write("## License Plate Detection!")
        streamlit_output_image(image, 'Annotated Image with model confidence score: {0:.2f}'.format(max_conf))
        
        img_list, score_list =  map(list, zip(*crop_list))
        st.write("### Cropped Plates")
        st.image(img_list, caption=["Cropped Image with model confidence score:"+'{0:.2f}'.format(score) for score in score_list], width = crop_size)
    else:
        st.error("Plate not found! Reduce confidence cutoff or select different image.")
        return
    return max_crop

#======================== Time To See The Magic ===========================

st.sidebar.markdown("## Automatic License Plate recognition system 🇮🇳")


crop, image = None, None
img_size, crop_size = 600, 400

activities = ["Home", "YoloV3 Detection", "RetinaNet Detection", "About"]
choice = st.sidebar.radio("Go to", activities)

if choice == "Home":
    
    st.markdown("<h1 style='text-align: center; color: black;'>Indian ALPR System using Deep Learning 👁</h1>", unsafe_allow_html=True)
    st.sidebar.info(__doc__)
    st.write("## How does it work?")
    st.write("Add an image of a car and a [deep learning](http://wiki.fast.ai/index.php/Lesson_1_Notes) model will look at it\
         and find the **license plate** like the example below:")
    st.sidebar.info("- The learning (detection) happens  \
                    with a fine-tuned [**Retinanet**](https://arxiv.org/abs/1708.02002) or a [**YoloV3**](https://pjreddie.com/darknet/yolo/) \
                    model ([**Google's Tensorflow 2**](https://www.tensorflow.org/)), \
                    \n- This front end (what you're reading) is built with [**Streamlit**](https://www.streamlit.io/) \
                    \n- It's all hosted on the cloud using [**Google Cloud Platform's App Engine**](https://cloud.google.com/appengine/).")
                    
    # st.video("https://youtu.be/C_lIenSJb3c")
    #  and a [YouTube playlist](https://www.youtube.com/playlist?list=PL6vjgQ2-qJFeMrZ0sBjmnUBZNX9xaqKuM) detailing more below.")
    # or OpenCV Haar cascade

    st.sidebar.warning("#### Checkout the Source code on [GitHub](https://github.com/SamratRode/Automatic-License-Plate-Recognition)")

    st.image("output/sample_output.png",
            caption="Example of a model being run on a car.",
            use_column_width=True)

    st.write("## How is this made?")
    banners = 'banners/'
    files = [banners+f for f in os.listdir(banners) if os.path.isfile(os.path.join(banners, f))]
    st.image(random.choice(files),use_column_width=True)


elif choice == "About":
    about()

elif choice == "RetinaNet Detection" or "YoloV3 Detection":

    crop, image = None, None

    st.write("## Upload your own image")

    # placeholders
    choose = st.empty() 
    upload = st.empty()
    note = st.empty()
    note.error("**Note:** The model has been trained on Indian cars and number plates, and therefore will only work with those kind of images.")

    # Detections below this confidence will be ignored
    confidence = st.slider("Confidence Cutoff",0.0,1.0,(0.5))
    predictor = st.checkbox("Make a Prediction 🔥")

    samplefiles = sorted([sample for sample in listdir('data/sample_images')])
    radio_list = ['Choose existing', 'Upload']

    query_params = st.experimental_get_query_params()
    # Query parameters are returned as a list to support multiselect.
    # Get the second item (upload) in the list if the query parameter exists.
    # Setting default page as Upload page, checkout the url too. The page state can be shared now!
    default = 1

    activity = choose.radio("Choose existing sample or try your own:", radio_list, index=default)
    
    if activity:
        st.experimental_set_query_params(activity=radio_list.index(activity))
        if activity == 'Choose existing':
            selected_sample = upload.selectbox("Pick from existing samples", (samplefiles))
            image = Image.open('data/sample_images/'+selected_sample)
            IMAGE_PATH = 'data/sample_images/'+selected_sample
            image = Image.open('data/sample_images/'+selected_sample)
            img_file_buffer = None

        else:
            # You can specify more file types below if you want
            img_file_buffer = upload.file_uploader("Upload image", type=['jpeg', 'png', 'jpg', 'webp'], multiple_files = True)

            IMAGE_PATH = img_file_buffer
            try:
                image = Image.open(IMAGE_PATH)
            except:
                pass

            selected_sample = None

    if image:
        
        st.sidebar.markdown("## Preview Of Selected Image! ")
        streamlit_preview_image(image)
        
        docs = st.sidebar.empty()
        if docs.checkbox("View Documentation"):
            if choice == "RetinaNet Detection":
                about_retinanet()
            else:
                about_yolo()

    else :

        if choice == "RetinaNet Detection":
            about_retinanet()
        else:
            about_yolo()

    max_crop, max_conf = None, None

    if choice == "RetinaNet Detection":

        if image:
            if predictor:
                model = load_retinanet()
                try:
                    # gif_runner = image_holder.image('banners/processing.gif', width = img_size)
                    annotated_image, score, crop_list = retinanet_detector(IMAGE_PATH, model, confidence)
                    # gif_runner.empty()
                    max_crop = multi_crop(annotated_image, crop_list)

                except TypeError as e:

                    st.warning('''
                            Model is not confident enough!
                            \nTry lowering the confidence cutoff.
                            ''')
                    # st.error("Error log: "+str(e))

                if max_crop!= None:
                    enhanced = enhance_crop(max_crop)
                    streamlit_OCR(enhanced)

    if choice == "YoloV3 Detection":
        if image:
            if predictor:
                try:
                    # gif_runner = image_holder.image('banners/processing.gif', width = img_size)
                    image, crop_list = yolo_inference(image, confidence)
                    # gif_runner.empty()
                    max_crop = multi_crop(image, crop_list)
                    
                except UnboundLocalError as e:
                    st.write(e)

                except NameError as e:
                    st.error('''
                    Model is not confident enough!
                    \nTry lowering the confidence cutoff.
                    ''')
                    st.error("Error log: "+str(e))
                
                if isinstance(max_crop, np.ndarray):
                    max_crop = Image.fromarray(max_crop)
                    enhanced = enhance_crop(max_crop)
                    streamlit_OCR(enhanced)

