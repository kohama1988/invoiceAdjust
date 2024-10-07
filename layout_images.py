import os
import math
from PIL import Image, ImageDraw, ImageFont

# A4纸的尺寸（像素，300dpi）
A4_WIDTH = 2480
A4_HEIGHT = 3508

# 最小边距和图片间距
MIN_MARGIN = 50
MIN_SPACING = 20

# 字体设置
FONT_SIZE = 60
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

def add_filename_to_image(draw, filename, position):
    font = ImageFont.load_default().font_variant(size=FONT_SIZE)
    filename_without_ext = filename.rsplit('.', 1)[0]
    left, top, right, bottom = draw.textbbox((0, 0), filename_without_ext, font=font)
    text_width = right - left
    text_height = bottom - top
    x, y = position
    draw.text((x+20, y - text_height +30), filename_without_ext, font=font, fill=FONT_COLOR)

def create_pages(pages, resized_images):
    result_pages = []
    for i, page in enumerate(pages):
        canvas = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
        draw = ImageDraw.Draw(canvas)
        for filename, size, position in page:
            img = resized_images[filename]
            canvas.paste(img, position)
            add_filename_to_image(draw, filename, position)
        result_pages.append(canvas)
    return result_pages

def main(resized_images):
    image_sizes = [(name, img.size) for name, img in resized_images.items()]
    pages = layout_images(image_sizes)
    result_pages = create_pages(pages, resized_images)
    
    print(f"Total images processed: {len(image_sizes)}")
    print(f"Total pages created: {len(result_pages)}")
    
    return result_pages

if __name__ == "__main__":
    main()