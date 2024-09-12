import cv2
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import detectTextOrientation, rotateImage

def process_single_image(image_path, receipts_folder):
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

            output_path = os.path.join(receipts_folder, os.path.basename(image_path))
            cv2.imwrite(output_path, rotated)
            print(f"Processed and saved: {output_path}")
        else:
            print(f"No contours found in {image_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")

    return os.path.basename(image_path)

def detectAndCorrectReceipt(image_folder, progress_callback=None):
    receipts_folder = os.path.join(image_folder, 'receipts')
    if not os.path.exists(receipts_folder):
        os.makedirs(receipts_folder)

    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_images = len(image_files)

    processed_count = 0
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_image = {executor.submit(process_single_image, os.path.join(image_folder, image), receipts_folder): image for image in image_files}
        for future in as_completed(future_to_image):
            processed_count += 1
            if progress_callback:
                progress_callback(int(processed_count / total_images * 100), processed_count, total_images)

    print("所有图片处理完成")

# 处理图片
if __name__ == "__main__":
    detectAndCorrectReceipt('receipt/IMG_4109.jpg')