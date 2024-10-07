import streamlit as st
from PIL import Image
import io
from process_receipt import detectAndCorrectReceipt
from resize import resize_image
from layout_images import layout_images, create_pages, main
import logging
import numpy as np

# 设置日志
logging.basicConfig(level=logging.INFO)

# Set page title and layout
st.set_page_config(layout="wide")
st.title("Receipt Processor")

# Sidebar
st.sidebar.header("Settings")

# 使用文件上传器选择多张图片
uploaded_files = st.sidebar.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

# 初始化字典并保存到 session_state
if 'extracted_images' not in st.session_state:
    st.session_state.extracted_images = {}
if 'resized_images' not in st.session_state:
    st.session_state.resized_images = {}

# 旋转图像的函数
def rotate_image(image, angle):
    return image.rotate(angle, expand=True)

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
            
            # Input box for manually changing image name (without extension)
            default_name = uploaded_file.name.rsplit('.', 1)[0]
            new_name = st.text_input("No", value=default_name, key=f"input_{i}")
            image_names[uploaded_file.name] = new_name  # Save user-inputted name
            
            st.markdown("<div style='margin-bottom: 10px; margin-right: 10px;'></div>", unsafe_allow_html=True)  # Set bottom margin
            if i % 10 < 9:  # Only add right margin if not the last column
                st.markdown("<div style='display:inline-block; width:10px;'></div>", unsafe_allow_html=True)  # Set right margin

    # Extract receipts
    if st.sidebar.button("Extract Receipts"):
        # Show extracting indicator
        progress_bar = st.sidebar.progress(0)  # Initialize progress bar
        total_images = len(uploaded_files)
        st.write(f"Processing {total_images} images...")

        with st.spinner("Extracting receipts..."):
            for idx, uploaded_file in enumerate(uploaded_files):
                # Use user-inputted new name
                new_image_name = image_names[uploaded_file.name]
                
                # 将提取后的发票保存到字典中
                extracted_image = detectAndCorrectReceipt(uploaded_file, new_image_name)  # Pass the uploaded file and new name
                if extracted_image is not None:
                    # 将 PIL Image 转换为 bytes
                    img_byte_arr = io.BytesIO()
                    extracted_image.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    st.session_state.extracted_images[new_image_name] = img_byte_arr  # Save to session state
                else:
                    st.write(f"Failed to extract image: {new_image_name}")

                # Update progress bar and percentage
                progress = (idx + 1) / total_images
                progress_bar.progress(progress)

        st.sidebar.success(f"Receipts extracted successfully! Total: {len(st.session_state.extracted_images)}")
        st.write(f"Total extracted images: {len(st.session_state.extracted_images)}")

    # Display extracted images as thumbnails with delete button and rotation feature
    if st.session_state.extracted_images:
        st.subheader("Extracted Receipts")
        
        cols = st.columns(5)  # Display 5 images per row
        for i, (name, img_bytes) in enumerate(list(st.session_state.extracted_images.items())):
            with cols[i % 5]:
                # Create a container for the image, delete button, and rotation slider
                container = st.container()
                # Add delete button
                if container.button("X", key=f"delete_{name}"):
                    del st.session_state.extracted_images[name]
                    st.rerun()
                
                # Display thumbnail
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    container.image(img, caption=name, use_column_width=True)
                    
                    # Add rotation slider
                    rotation_angle = container.slider("Rotate", -180, 180, 0, key=f"rotate_{name}")
                    if rotation_angle != 0:
                        rotated_img = rotate_image(img, rotation_angle)
                        container.image(rotated_img, caption=f"{name} (Rotated)", use_column_width=True)
                        
                        # Save button for rotated image
                        if container.button("Save Rotation", key=f"save_rotation_{name}"):
                            # Convert rotated image to bytes and save to session state
                            rotated_bytes = io.BytesIO()
                            rotated_img.save(rotated_bytes, format='PNG')
                            st.session_state.extracted_images[name] = rotated_bytes.getvalue()
                            st.success(f"Rotated image saved for {name}")
                            st.rerun()
                
                except Exception as e:
                    st.write(f"Error displaying image {name}: {str(e)}")
            
            if (i + 1) % 5 == 0:
                st.write("")  # Add a new line after every 5 images
    else:
        st.write("No extracted images to display.")

    # Resize images
    scale_factor = st.sidebar.slider("Scale Factor (0-1)", 0.1, 1.0, 0.3)
    if st.sidebar.button("Resize Images"):
        # Ensure resized_images exists
        st.session_state.resized_images.clear()  # Clear previous entries
        
        if st.session_state.extracted_images:
            for name, img_bytes in st.session_state.extracted_images.items():
                img = Image.open(io.BytesIO(img_bytes))
                resized_image = resize_image(img, scale_factor)  # Resize and get the resized image
                # 将调整大小后的图像转换为 bytes
                resized_img_byte_arr = io.BytesIO()
                resized_image.save(resized_img_byte_arr, format='PNG')
                resized_img_byte_arr = resized_img_byte_arr.getvalue()
                st.session_state.resized_images[name] = resized_img_byte_arr  # Save resized image to session state

            st.sidebar.success("Images resized successfully!")
            logging.info(f"Total resized images: {len(st.session_state.resized_images)}")

    # Auto arrange
    if st.sidebar.button("Auto Arrange"):
        if st.session_state.resized_images:
            # 将 bytes 转换回 PIL Image 对象
            resized_images_pil = {name: Image.open(io.BytesIO(img_bytes)) for name, img_bytes in st.session_state.resized_images.items()}
            arranged_pages = main(resized_images_pil)  # 现在可以正确调用 main 函数
            st.session_state.arranged_pages = arranged_pages
            st.sidebar.success("Images arranged successfully!")

            # Display arranged results as thumbnails
            st.subheader("Arranged Results")
            cols = st.columns(5)  # Display 5 thumbnails per row
            for i, page in enumerate(st.session_state.arranged_pages):
                with cols[i % 5]:
                    # 将 PIL Image 转换为 bytes
                    img_byte_arr = io.BytesIO()
                    page.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    st.image(img_byte_arr, caption=f"Page {i+1}", use_column_width=True, width=200)  # Display thumbnail
                if (i + 1) % 5 == 0:
                    st.write("")  # Add a new line after every 5 thumbnails
        else:
            st.sidebar.warning("Please resize images first.")

else:
    st.sidebar.warning("Please upload images.")

# 在页面底部显示 session_state 中的信息
if 'arranged_pages' in st.session_state:
    st.write(f"Number of arranged pages: {len(st.session_state.arranged_pages)}")


# 尝试显示第一张提取的图片（如果有的话）
# if st.session_state.extracted_images:
#     first_image_name = next(iter(st.session_state.extracted_images))
#     first_image_bytes = st.session_state.extracted_images[first_image_name]
#     try:
#         st.image(first_image_bytes, caption=first_image_name, use_column_width=True)
#     except Exception as e:
#         st.write(f"Error displaying first image: {str(e)}")