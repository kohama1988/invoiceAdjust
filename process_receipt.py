import cv2
import numpy as np
from PIL import Image
from utils import detectTextOrientation, rotateImage
import io
import re

def slugify(value):
    """将字符串转换为适合文件名的格式"""
    value = str(value)
    value = value.strip().lower()
    value = re.sub(r'[-\s]+', '-', value)  # 替换空格和连字符
    value = re.sub(r'[^\w\-]', '', value)  # 移除非字母数字字符
    return value

def process_single_image(uploaded_file, new_image_name):
    try:
        # 重置文件指针到开始位置
        uploaded_file.seek(0)
        
        # 从上传的文件中读取图像数据
        image_bytes = uploaded_file.read()
        
        # 使用PIL打开图像
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # 将PIL图像转换为NumPy数组
        image_np = np.array(pil_image)
        
        # 如果图像是RGBA格式，转换为RGB
        if len(image_np.shape) == 3 and image_np.shape[2] == 4:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        
        # 将RGB转换为BGR（OpenCV使用BGR格式）
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(max_contour)
            box = cv2.boxPoints(rect)
            box = np.int32(box)

            width = int(rect[1][0])
            height = int(rect[1][1])

            src_pts = box.astype("float32")
            dst_pts = np.array([[0, height-1], [0, 0], [width-1, 0], [width-1, height-1]], dtype="float32")

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(image_cv, M, (width, height))

            # 检测文字方向
            text_angle = detectTextOrientation(warped)
            
            # 调整旋转角度
            if text_angle > 0:
                rotation_angle = 360 - text_angle
            else:
                rotation_angle = -text_angle

            # 只有当文字方向不正确时才旋转
            if abs(rotation_angle) > 5 and abs(rotation_angle - 360) > 5:  # 允许5度的误差
                rotated = rotateImage(warped, rotation_angle)
            else:
                rotated = warped

            # 将BGR转换回RGB
            rotated_rgb = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
            
            # 将NumPy数组转换回PIL图像
            return Image.fromarray(rotated_rgb)
        else:
            print(f"No contours found in the image.")
            return None

    except Exception as e:
        print(f"Error processing the image: {str(e)}")
        return None

def detectAndCorrectReceipt(uploaded_file, new_image_name):
    """处理并提取发票部分"""
    return process_single_image(uploaded_file, new_image_name)

# 处理图片
if __name__ == "__main__":
    detectAndCorrectReceipt('receipt/IMG_4109.jpg', 'new_image_name')