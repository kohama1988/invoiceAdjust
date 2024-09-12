import cv2
import numpy as np
import pytesseract

def detectTextOrientation(image):
    # 使用Tesseract检测文字方向
    osd = pytesseract.image_to_osd(image)
    angle = int(osd.split('\n')[2].split(':')[1].strip())
    return angle

def rotateImage(image, angle):
    # 获取图像尺寸
    (h, w) = image.shape[:2]
    
    # 计算新图像的尺寸
    (cX, cY) = (w // 2, h // 2)
    
    # 计算旋转矩阵
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    
    # 进行仿射变换
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    # 计算新图像的边界
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    
    # 调整旋转矩阵
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    
    # 执行仿射变换
    rotated = cv2.warpAffine(image, M, (nW, nH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated
