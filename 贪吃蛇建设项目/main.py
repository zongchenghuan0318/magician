# -*- coding: utf-8 -*-
import ctypes
import pygame
from game.game_controller import GameController
from game.game_controller_dual import GameControllerDual  # 新增导入
from game.splash_screen import SplashScreen  # 导入启动画面
def set_english_input_method():
    try:
        # 0x0409 是英文(美国)输入法的LANGID
        # 0x04090409 是英文(美国)的HKL
        thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        hkl = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 1)
        ctypes.windll.user32.ActivateKeyboardLayout(hkl, 0)
    except Exception as e:
        print("切换输入法失败：", e)
set_english_input_method()
def main():
    # 初始化pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("贪吃蛇大冒险")
    
    # 启动画面已被禁用
    # splash = SplashScreen(screen)
    # if not splash.run():
    #     return  # 如果用户在启动画面关闭窗口，直接退出
    
    game = GameController()
    while True:
        result = game.run_menu()
        if result == "exit":
            break
            
        if result == "start":
            # 重新初始化游戏状态并开始播放音乐
            game.reset_game(play_music=True)
            result = game.run()
            if result == "exit":
                break
        elif result == "dual":  # 新增双人模式入口
            dual_game = GameControllerDual(game.screen)
            dual_game.run()
        elif result == "settings":
            game.run_settings()
        elif result == "help":
            game.run_help()
        elif result == "shop":
            game.run_shop()
        elif result == "backpack":
            game.run_backpack()
        elif result == "activity":
            game.run_activity()
if __name__ == "__main__":
    main()