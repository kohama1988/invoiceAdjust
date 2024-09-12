import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from utils import detectTextOrientation, rotateImage

def detectAndCorrectReceipt(image_path, ls=180, hs=255):
    # 读取图像
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, ls, hs, cv2.THRESH_BINARY)

    # 检测轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 找到最大的轮廓（假设是发票）
    max_contour = max(contours, key=cv2.contourArea)

    # 获取最小面积矩形
    rect = cv2.minAreaRect(max_contour)
    box = cv2.boxPoints(rect)
    box = np.int32(box)

    # 获取矩形的宽度和高度
    width = int(rect[1][0])
    height = int(rect[1][1])

    # 保持原始的宽高比
    src_pts = box.astype("float32")
    dst_pts = np.array([[0, height-1],
                        [0, 0],
                        [width-1, 0],
                        [width-1, height-1]], dtype="float32")

    # 计算透视变换矩阵
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # 应用透视变换
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

    # 确保 'after' 文件夹存在
    after_folder = 'after'
    if not os.path.exists(after_folder):
        os.makedirs(after_folder)

    # 获取原始文件名
    base_name = os.path.basename(image_path)

    # 构建输出文件路径
    output_path = os.path.join(after_folder, base_name)

    # 保存处理后的图像
    cv2.imwrite(output_path, rotated)
    print(f"处理后的图像已保存到: {output_path}")

    # 显示原始图像和纠正后的图像
    plt.figure(figsize=(10, 5))
    plt.subplot(121), plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), plt.title('Original')
    plt.subplot(122), plt.imshow(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)), plt.title('Abstracted')
    plt.show()

# 处理图片
if __name__ == "__main__":
    detectAndCorrectReceipt('receipt/IMG_4109.jpg')