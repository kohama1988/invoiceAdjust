import os
import math
from PIL import Image, ImageDraw, ImageFont

# A4纸的尺寸（像素，300dpi）
A4_WIDTH = 2480
A4_HEIGHT = 3508

# 最小边距和图片间距
MIN_MARGIN = 5
MIN_SPACING = 5

# 字体设置
FONT_SIZE = 60  # 增大字体大小
FONT_COLOR = (0, 0, 0)  # 黑色

# 使用默认字体
FONT_PATH = None  # 使用默认字体

def get_image_sizes(folder_path):
    image_sizes = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            with Image.open(os.path.join(folder_path, filename)) as img:
                image_sizes.append((filename, img.size))
    return image_sizes

def can_place_image(page, x, y, width, height):
    for _, (w, h), (px, py) in page:
        if (x < px + w + MIN_SPACING and x + width + MIN_SPACING > px and
            y < py + h + MIN_SPACING and y + height + MIN_SPACING > py):
            return False
    return True

def find_position(page, image_size):
    width, height = image_size
    best_position = None
    min_waste = float('inf')

    for y in range(MIN_MARGIN, A4_HEIGHT - height - MIN_MARGIN + 1, MIN_SPACING):
        for x in range(MIN_MARGIN, A4_WIDTH - width - MIN_MARGIN + 1, MIN_SPACING):
            if can_place_image(page, x, y, width, height):
                waste = x + y  # 优先选择靠近左上角的位置
                if waste < min_waste:
                    min_waste = waste
                    best_position = (x, y)

    return best_position

def layout_images(image_sizes):
    pages = []
    current_page = []
    
    # 按面积从大到小排序图片
    image_sizes.sort(key=lambda x: x[1][0] * x[1][1], reverse=True)
    
    for filename, size in image_sizes:
        position = find_position(current_page, size)
        if position:
            current_page.append((filename, size, position))
        else:
            if current_page:
                pages.append(current_page)
                current_page = []
            position = find_position(current_page, size)
            if position:
                current_page.append((filename, size, position))
            else:
                print(f"警告：图片 {filename} 太大，将单独放置在一个页面上。")
                pages.append([(filename, size, (MIN_MARGIN, MIN_MARGIN))])

    if current_page:
        pages.append(current_page)

    return pages

def add_filename_to_image(img, filename):
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=FONT_SIZE)  # 使用默认字体
    
    # 移除文件扩展名
    filename_without_ext = os.path.splitext(filename)[0]
    
    # 添加文字阴影以增加可读性
    shadow_color = (0, 0, 0)  # 黑色阴影
    draw.text((21, 21), filename_without_ext, font=font, fill=shadow_color)
    
    # 添加黑色文字
    draw.text((20, 20), filename_without_ext, font=font, fill=FONT_COLOR)

def create_pages(pages, input_folder, output_folder):
    for i, page in enumerate(pages):
        canvas = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
        for filename, size, position in page:
            with Image.open(os.path.join(input_folder, filename)) as img:
                add_filename_to_image(img, filename)
                canvas.paste(img, position)
        canvas.save(os.path.join(output_folder, f'page_{i+1}.png'))
        print(f'Created page_{i+1}.png with {len(page)} images')

def main():
    input_folder = 'resize'
    output_folder = 'layout'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_sizes = get_image_sizes(input_folder)
    pages = layout_images(image_sizes)
    create_pages(pages, input_folder, output_folder)
    
    print(f"Total images processed: {len(image_sizes)}")
    print(f"Total pages created: {len(pages)}")

if __name__ == "__main__":
    main()