import cv2
import numpy as np
import os
from utils import detectTextOrientation, rotateImage
import re

def slugify(value):
    """将字符串转换为适合文件名的格式"""
    value = str(value)
    value = value.strip().lower()
    value = re.sub(r'[-\s]+', '-', value)  # 替换空格和连字符
    value = re.sub(r'[^\w\-]', '', value)  # 移除非字母数字字符
    return value

def process_single_image(image_path, new_image_name, receipts_folder):
    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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
            warped = cv2.warpPerspective(image, M, (width, height))

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

            # 使用 slugify 处理文件名
            safe_image_name = slugify(new_image_name)
            output_path = os.path.join(receipts_folder, f"{safe_image_name}.jpg")  # 确保使用 .jpg 扩展名
            cv2.imwrite(output_path, rotated)
            print(f"Processed and saved: {output_path}")
        else:
            print(f"No contours found in {image_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")

def detectAndCorrectReceipt(image_path, new_image_name, receipts_folder):
    """处理并提取发票部分"""
    process_single_image(image_path, new_image_name, receipts_folder)

# 处理图片
if __name__ == "__main__":
    detectAndCorrectReceipt('receipt/IMG_4109.jpg', 'new_image_name', 'receipts')