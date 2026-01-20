import os
from PIL import Image

def check_image_sizes():
    """检查snake_images文件夹中所有图片的尺寸"""
    image_dir = "snake_images"
    
    if not os.path.exists(image_dir):
        return
    
    for filename in os.listdir(image_dir):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(image_dir, filename)
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    file_size = os.path.getsize(filepath)
            except Exception as e:
                pass

if __name__ == "__main__":
    check_image_sizes() 