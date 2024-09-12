import os
import cv2
from PIL import Image

def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size

def resize_image(image_path, output_path, scale_factor=0.28):
    # 读取图像
    img = cv2.imread(image_path)
    
    # 获取原始尺寸
    height, width = img.shape[:2]
    
    # 计算新的尺寸
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # 调整图像大小
    resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # 保存调整大小后的图像
    cv2.imwrite(output_path, resized_img)

def process_images(input_folder, output_folder):
    # 确保输入文件夹路径存在
    if not os.path.exists(input_folder):
        print(f"输入文件夹 {input_folder} 不存在")
        return

    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取文件夹中的所有文件
    files = os.listdir(input_folder)

    # 筛选出图片文件（这里假设图片格式为jpg, jpeg, png）
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        print(f"在 {input_folder} 中没有找到图片文件")
        return

    # 处理每个图片文件
    for image_file in image_files:
        input_path = os.path.join(input_folder, image_file)
        output_path = os.path.join(output_folder, image_file)
        
        # 获取原始尺寸
        original_width, original_height = get_image_size(input_path)
        
        # 调整图像大小并保存
        resize_image(input_path, output_path)
        
        # 获取调整后的尺寸
        resized_width, resized_height = get_image_size(output_path)
        
        print(f"图片: {image_file}")
        print(f"  原始尺寸: {original_width}x{original_height}")
        print(f"  调整后尺寸: {resized_width}x{resized_height}")
        print()

if __name__ == "__main__":
    after_folder = 'after'
    resize_folder = 'resize'
    process_images(after_folder, resize_folder)
