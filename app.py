import os
import streamlit as st
from PIL import Image
from process_receipt import detectAndCorrectReceipt
from resize import resize_image
from layout_images import layout_images, create_pages
from datetime import datetime

# Set page title and layout
st.set_page_config(layout="wide")
st.title("Receipt Processor")

# Sidebar
st.sidebar.header("Settings")

# 使用文件上传器选择多张图片
uploaded_files = st.sidebar.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

# 创建 receipts 文件夹，命名为 receipts + 时间戳
if 'receipts_folder' not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.receipts_folder = os.path.join(os.getcwd(), f'receipts_{timestamp}')
    os.makedirs(st.session_state.receipts_folder, exist_ok=True)

# 创建 receipts 子文件夹
if 'extracted_receipts_folder' not in st.session_state:
    st.session_state.extracted_receipts_folder = os.path.join(st.session_state.receipts_folder, 'receipts')
    os.makedirs(st.session_state.extracted_receipts_folder, exist_ok=True)

# Display all uploaded images
if uploaded_files:
    st.subheader("Selected Images")
    cols = st.columns(10)  # Display 10 images per row
    image_names = {}  # To store user-inputted image names

    for i, uploaded_file in enumerate(uploaded_files):
        image = Image.open(uploaded_file)
        with cols[i % 10]:  # Change row every 10 images
            # Display thumbnail
            st.image(image, caption=uploaded_file.name, use_column_width='auto', width=100)  # Thumbnail
            
            # Input box for manually changing image name
            new_name = st.text_input("New Name", value=uploaded_file.name, key=f"input_{i}")
            image_names[uploaded_file.name] = new_name  # Save user-inputted name
            
            st.markdown("<div style='margin-bottom: 10px; margin-right: 10px;'></div>", unsafe_allow_html=True)  # Set bottom margin
            if i % 10 < 9:  # Only add right margin if not the last column
                st.markdown("<div style='display:inline-block; width:10px;'></div>", unsafe_allow_html=True)  # Set right margin

    # Extract receipts
    if st.sidebar.button("Extract Receipts"):
        # Show extracting indicator
        progress_bar = st.sidebar.progress(0)  # Initialize progress bar
        total_images = len(uploaded_files)

        with st.spinner("Extracting receipts..."):
            for idx, uploaded_file in enumerate(uploaded_files):
                # Use user-inputted new name
                if '.' in image_names[uploaded_file.name]:
                    new_image_name = image_names[uploaded_file.name].rsplit('.', 1)[0]  # Remove extension
                else:
                    new_image_name = image_names[uploaded_file.name]
                
                # Save uploaded file to the receipts folder
                original_image_path = os.path.join(st.session_state.receipts_folder, uploaded_file.name)
                with open(original_image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())  # 使用 getbuffer() 方法保存文件内容

                # 将提取后的发票保存到 receipts 子文件夹
                detectAndCorrectReceipt(original_image_path, new_image_name, st.session_state.extracted_receipts_folder)  # Pass receipts folder

                # Update progress bar and percentage
                progress = (idx + 1) / total_images
                progress_bar.progress(progress)

        st.sidebar.success("Receipts extracted successfully!")

        # Display extracted images
        st.subheader("Extracted Receipts")
        extracted_images = [f for f in os.listdir(st.session_state.extracted_receipts_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        cols = st.columns(10)  # Display 10 images per row
        for i, extracted_image_file in enumerate(extracted_images):
            extracted_image_path = os.path.join(st.session_state.extracted_receipts_folder, extracted_image_file)
            with cols[i % 10]:  # Change row every 10 images
                st.image(extracted_image_path, caption=extracted_image_file, use_column_width='auto', width=100)  # Thumbnail
                st.markdown("<div style='margin-bottom: 10px; margin-right: 10px;'></div>", unsafe_allow_html=True)  # Set bottom margin
                if i % 10 < 9:  # Only add right margin if not the last column
                    st.markdown("<div style='display:inline-block; width:10px;'></div>", unsafe_allow_html=True)  # Set right margin

    # Resize images
    scale_factor = st.sidebar.slider("Scale Factor (0-1)", 0.1, 1.0, 0.3)
    if st.sidebar.button("Resize Images"):
        # Store resize_folder in session state
        if 'resize_folder' not in st.session_state:
            st.session_state.resize_folder = os.path.join(st.session_state.receipts_folder, 'resize')
            os.makedirs(st.session_state.resize_folder, exist_ok=True)

        # Ensure extracted images exist
        extracted_images = [f for f in os.listdir(st.session_state.extracted_receipts_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if extracted_images:
            # Store resized_images in session state
            st.session_state.resized_images = []
            for image_file in extracted_images:
                input_path = os.path.join(st.session_state.extracted_receipts_folder, image_file)
                output_path = os.path.join(st.session_state.resize_folder, image_file)
                resize_image(input_path, output_path, scale_factor)
                st.session_state.resized_images.append(image_file)  # Save resized image file names

            st.sidebar.success("Images resized successfully!")

            # Do not display resized images on the main page

    # Auto arrange
    if st.sidebar.button("Auto Arrange"):
        layout_folder = os.path.join(os.getcwd(), 'layout')
        if not os.path.exists(layout_folder):
            os.makedirs(layout_folder)

        # 清空 layout_folder
        for f in os.listdir(layout_folder):
            os.remove(os.path.join(layout_folder, f))

        # 检查 resized_images 中的图片是否存在
        image_sizes = [(f, Image.open(os.path.join(st.session_state.resize_folder, f)).size) 
                       for f in st.session_state.resized_images 
                       if os.path.exists(os.path.join(st.session_state.resize_folder, f))]
        
        pages = layout_images(image_sizes)
        create_pages(pages, st.session_state.resize_folder, layout_folder)

        st.sidebar.success("Images arranged successfully!")

        # Display arranged results
        st.subheader("Arranged Results")
        layout_images = [f for f in os.listdir(layout_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        cols = st.columns(10)  # Display 10 images per row
        for i, image_file in enumerate(layout_images):
            image_path = os.path.join(layout_folder, image_file)
            with cols[i % 10]:  # Change row every 10 images
                # Display images at original size
                img = Image.open(image_path)
                st.image(img, caption=image_file, use_column_width='auto')  # Display original image
                st.markdown("<div style='margin-bottom: 10px; margin-right: 10px;'></div>", unsafe_allow_html=True)  # Set bottom margin
                if i % 10 < 9:  # Only add right margin if not the last column
                    st.markdown("<div style='display:inline-block; width:10px;'></div>", unsafe_allow_html=True)  # Set right margin

else:
    st.sidebar.warning("Please upload images.")