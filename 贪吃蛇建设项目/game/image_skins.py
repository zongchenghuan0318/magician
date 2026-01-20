# -*- coding: utf-8 -*-
import pygame
import os
import json
from .constants import GRID_SIZE, get_resource_path

class ImageSkinManager:
    """图片皮肤管理器，用于加载和管理蛇头和蛇身的图片皮肤"""
    
    def __init__(self):
        self.image_cache = {}  # 缓存已加载的图片
        self.skins_data = {}   # 皮肤数据
        self.rotated_cache = {}  # 缓存旋转后的图片 (image_name, size, angle, is_head) -> Surface
        self.load_image_skins()
    
    def load_image_skins(self):
        """加载图片皮肤数据"""
        # 构建到image_skins.json的路径
        skins_path = get_resource_path('image_skins.json')
        
        try:
            with open(skins_path, 'r', encoding='utf-8') as f:
                self.skins_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # print(f"警告：无法加载 'image_skins.json': {e}")
            # 创建默认的图片皮肤数据
            self.skins_data = {
                "default_image": {
                    "name": "默认图片皮肤",
                    "price": 0,
                    "head_image": "snake_head_default.png",
                    "body_image": "snake_body_default.png",
                    "type": "image"
                }
            }
            # 保存默认数据
            self.save_image_skins()
    
    def save_image_skins(self):
        """保存图片皮肤数据到文件"""
        skins_path = get_resource_path('image_skins.json')
        
        try:
            with open(skins_path, 'w', encoding='utf-8') as f:
                json.dump(self.skins_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # print(f"错误：无法保存 'image_skins.json': {e}")
            pass
    
    def get_image(self, image_path, size=None):
        """获取图片，支持缓存"""
        # 使用图片路径和尺寸作为缓存key
        cache_key = (image_path, size)
        
        if cache_key not in self.image_cache:
            try:
                # 构建图片文件的完整路径
                images_dir = get_resource_path('snake_images')
                full_path = os.path.join(images_dir, image_path)
                
                if os.path.exists(full_path):
                    image = pygame.image.load(full_path).convert_alpha()
                    if size:
                        image = pygame.transform.scale(image, size)
                    self.image_cache[cache_key] = image
                else:
                    # print(f"警告：图片文件不存在: {full_path}")
                    return None
            except Exception as e:
                # print(f"错误：无法加载图片 {image_path}: {e}")
                return None
        
        return self.image_cache[cache_key]
    
    def get_skin_data(self, skin_id):
        """获取皮肤数据"""
        return self.skins_data.get(skin_id)
    
    def get_skin_audio_config(self, skin_id):
        """获取皮肤的音频配置"""
        skin_data = self.get_skin_data(skin_id)
        if skin_data and "audio" in skin_data:
            audio_config = skin_data["audio"].copy()  # 复制一份配置
            
            # 处理音频文件路径
            if "background_music" in audio_config:
                audio_config["background_music"] = get_resource_path(audio_config["background_music"])
            
            return audio_config
        return None
    
    def has_audio(self, skin_id):
        """检查皮肤是否有音频配置"""
        return self.get_skin_audio_config(skin_id) is not None
    
    def is_image_skin(self, skin_id):
        """检查是否为图片皮肤"""
        skin_data = self.get_skin_data(skin_id)
        return skin_data and skin_data.get("type") == "image"
    
    def draw_image_segment(self, surface, center_pos, direction, skin_id, is_head=False):
        """绘制图片皮肤段"""
        skin_data = self.get_skin_data(skin_id)
        if not skin_data:
            return False
        
        # 确定使用哪个图片
        if is_head:
            image_name = skin_data.get("head_image")
        else:
            image_name = skin_data.get("body_image")
        
        if not image_name:
            return False
        
        # 确保图片大小严格为一个格子大小
        image_size = int(GRID_SIZE * 4 / 3)  # 将图片放大三分之一
        
        # 获取图片
        image = self.get_image(image_name, (image_size, image_size))
        if not image:
            return False
        
        # 直接使用传入的像素中心坐标
        center_x, center_y = center_pos
        
        # 处理图片变换
        transformed_image = image
        
        # 根据方向旋转图片（蛇头和蛇身都旋转）
        # 以原始图片朝上为基准
        angle = 0
        if direction == (0, -1):      # 向上
            angle = 180
        elif direction == (1, 0):     # 向右
            angle = 90
        elif direction == (0, 1):     # 向下
            angle = 0
        elif direction == (-1, 0):    # 向左
            angle = 270
        # 蛇头需要特殊处理
        if is_head:
            if direction == (0, -1):      # 向上
                angle = 0
            elif direction == (1, 0):     # 向右
                angle = 270
            elif direction == (0, 1):     # 向下
                angle = 180
            elif direction == (-1, 0):    # 向左
                angle = 90
        
        # 旋转图片（带缓存）
        cache_key = (image_name, image.get_size(), angle, is_head)
        rotated_image = self.rotated_cache.get(cache_key)
        if rotated_image is None:
            rotated_image = pygame.transform.rotate(transformed_image, angle)
            self.rotated_cache[cache_key] = rotated_image
        
        # 获取最终图片的矩形
        rect = rotated_image.get_rect(center=(center_x, center_y))
        surface.blit(rotated_image, rect)
        
        return True
    
    def add_image_skin(self, skin_id, name, price, head_image, body_image):
        """添加新的图片皮肤"""
        self.skins_data[skin_id] = {
            "name": name,
            "price": price,
            "head_image": head_image,
            "body_image": body_image,
            "type": "image"
        }
        self.save_image_skins()
    
    def get_all_image_skins(self):
        """获取所有图片皮肤"""
        return {k: v for k, v in self.skins_data.items() if v.get("type") == "image"}
    
    def clear_cache(self):
        """清除图片缓存"""
        self.image_cache.clear()
        self.rotated_cache.clear()

# 创建全局实例
image_skin_manager = ImageSkinManager() 