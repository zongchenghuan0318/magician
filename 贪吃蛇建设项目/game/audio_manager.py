# -*- coding: utf-8 -*-
import pygame
import os
from typing import Optional
from game.constants import get_resource_path

class AudioManager:
    def __init__(self):
        """初始化音频管理器"""
        self.music_playing = False
        self.current_music = None
        self.music_volume = 0.5  # 默认音量50%
        self.sound_volume = 0.7  # 音效音量70%
        self.sounds = {}
        self.music_enabled = True
        self.sound_enabled = True
        
        # 初始化pygame音频（容错处理：无声卡/占用时不崩溃）
        self._mixer_ready = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.music.set_volume(self.music_volume)
            self._mixer_ready = True
        except Exception:
            # 禁用音乐与音效，避免后续调用失败
            self.music_enabled = False
            self.sound_enabled = False
    
    def load_music(self, music_path: str) -> bool:
        """
        加载音乐文件
        
        Args:
            music_path: 音乐文件路径
            
        Returns:
            bool: 加载是否成功
        """
        # 获取资源的绝对路径
        abs_path = get_resource_path(music_path)
        if not os.path.exists(abs_path):
            return False
            
        try:
            # 检查文件格式
            if not abs_path.lower().endswith('.mp3'):
                return False
                
            self.current_music = abs_path
            return True
        except Exception as e:
            return False
    
    def play_music(self, music_path: Optional[str] = None, loop: bool = True) -> bool:
        """
        播放音乐
        
        Args:
            music_path: 音乐文件路径，如果为None则使用当前加载的音乐
            loop: 是否循环播放
            
        Returns:
            bool: 播放是否成功
        """
        if not self.music_enabled or not getattr(self, '_mixer_ready', False):
            return False
            
        # 如果提供了新的音乐路径，先停止当前音乐
        if music_path:
            self.stop_music()
            if not self.load_music(music_path):
                return False
        
        if not self.current_music:
            return False
            
        try:
            # 确保停止之前的音乐
            if self._mixer_ready:
                pygame.mixer.music.stop()
            # 加载并播放新音乐
            if not self._mixer_ready:
                return False
            pygame.mixer.music.load(self.current_music)
            pygame.mixer.music.play(-1 if loop else 0)
            self.music_playing = True
            return True
        except Exception as e:
            self.music_playing = False
            return False
    
    def stop_music(self):
        """停止音乐播放"""
        try:
            if self._mixer_ready:
                pygame.mixer.music.stop()
            self.music_playing = False
        except Exception:
            self.music_playing = False
    
    def pause_music(self):
        """暂停音乐播放"""
        if self.music_playing and self._mixer_ready:
            try:
                pygame.mixer.music.pause()
            except Exception as e:
                pass
    
    def unpause_music(self):
        """恢复音乐播放"""
        if self.music_playing and self._mixer_ready:
            try:
                pygame.mixer.music.unpause()
            except Exception as e:
                pass
    
    def set_music_volume(self, volume: float):
        """
        设置音乐音量
        
        Args:
            volume: 音量值 (0.0 - 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        if self._mixer_ready:
            pygame.mixer.music.set_volume(self.music_volume)
    
    def get_music_volume(self) -> float:
        """获取当前音乐音量"""
        return self.music_volume
    
    def toggle_music(self):
        """切换音乐开关"""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
    
    def is_music_playing(self) -> bool:
        """检查音乐是否正在播放"""
        return self.music_playing and self.music_enabled
    
    def load_sound(self, sound_name: str, sound_path: str) -> bool:
        """
        加载音效
        
        Args:
            sound_name: 音效名称
            sound_path: 音效文件路径
            
        Returns:
            bool: 加载是否成功
        """
        # 获取资源的绝对路径
        abs_path = get_resource_path(sound_path)
        if not os.path.exists(abs_path) or not getattr(self, '_mixer_ready', False):
            return False
            
        try:
            if not self._mixer_ready:
                return False
            self.sounds[sound_name] = pygame.mixer.Sound(abs_path)
            self.sounds[sound_name].set_volume(self.sound_volume)
            return True
        except Exception as e:
            return False
    
    def play_sound(self, sound_name: str) -> bool:
        """
        播放音效
        
        Args:
            sound_name: 音效名称
            
        Returns:
            bool: 播放是否成功
        """
        if not self.sound_enabled or not getattr(self, '_mixer_ready', False) or sound_name not in self.sounds:
            return False
            
        try:
            self.sounds[sound_name].play()
            return True
        except Exception as e:
            return False
    
    def set_sound_volume(self, volume: float):
        """
        设置音效音量
        
        Args:
            volume: 音量值 (0.0 - 1.0)
        """
        self.sound_volume = max(0.0, min(1.0, volume))
        if self._mixer_ready:
            for sound in self.sounds.values():
                sound.set_volume(self.sound_volume)
    
    def get_sound_volume(self) -> float:
        """获取当前音效音量"""
        return self.sound_volume
    
    def toggle_sound(self):
        """切换音效开关"""
        self.sound_enabled = not self.sound_enabled
    
    def cleanup(self):
        """清理音频资源"""
        self.stop_music()
        if getattr(self, '_mixer_ready', False):
            pygame.mixer.quit()