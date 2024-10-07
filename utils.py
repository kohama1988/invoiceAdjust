import cv2
import numpy as np
import math
import logging
from PIL import Image

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_text_lines(image):
    """检测图像中的文本行"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 使用形态学操作连接相邻字符
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤小轮廓，可能是噪声
    min_area = 100
    text_lines = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    
    return text_lines

def compute_line_angles(text_lines):
    """计算文本行的角度"""
    angles = []
    for line in text_lines:
        rect = cv2.minAreaRect(line)
        angle = rect[2]
        if abs(angle) > 45:
            angle = 90 - abs(angle)
        angles.append(angle)
    return angles

def detect_dominant_orientation(angles):
    """检测主要方向"""
    angle_counts = {}
    for angle in angles:
        rounded_angle = round(angle / 5) * 5  # 将角度四舍五入到最接近的5度
        angle_counts[rounded_angle] = angle_counts.get(rounded_angle, 0) + 1
    
    dominant_angle = max(angle_counts, key=angle_counts.get)
    return dominant_angle

def detectTextOrientation(image):
    """检测文本方向并返回需要旋转的角度"""
    text_lines = detect_text_lines(image)
    if not text_lines:
        logger.warning("No text lines detected")
        return 0
    
    angles = compute_line_angles(text_lines)
    dominant_angle = detect_dominant_orientation(angles)
    
    # 只有当倾斜角度超过阈值时才进行旋转
    threshold = 5  # 可以根据需要调整这个阈值
    if abs(dominant_angle) <= threshold:
        logger.info(f"Detected angle {dominant_angle} is within threshold, no rotation needed")
        return 0
    
    # 确定旋转角度
    if -45 <= dominant_angle < 0:
        rotation_angle = -dominant_angle
    elif 0 < dominant_angle <= 45:
        rotation_angle = -dominant_angle
    elif 45 < dominant_angle <= 90:
        rotation_angle = 90 - dominant_angle
    else:
        rotation_angle = -90 - dominant_angle
    
    logger.info(f"Detected dominant angle: {dominant_angle}, Rotation angle: {rotation_angle}")
    return rotation_angle

def rotateImage(image, angle):
    """旋转图像"""
    if angle == 0:
        logger.info("No rotation needed")
        return image
    
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    
    # 计算新的图像尺寸
    if abs(angle) == 90:
        new_width, new_height = height, width
    else:
        rad = math.radians(abs(angle))
        new_width = int(abs(width * math.cos(rad)) + abs(height * math.sin(rad)))
        new_height = int(abs(width * math.sin(rad)) + abs(height * math.cos(rad)))
    
    # 调整旋转矩阵以考虑新的尺寸
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotation_matrix[0, 2] += (new_width - width) / 2
    rotation_matrix[1, 2] += (new_height - height) / 2
    
    rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    logger.info(f"Image rotated by {angle} degrees")
    return rotated

def deskew(image):
    """纠正图像倾斜"""
    angle = detectTextOrientation(image)
    return rotateImage(image, angle)
