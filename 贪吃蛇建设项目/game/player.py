import json
import os
import sys
import shutil
from game.constants import get_resource_path

# 在打包环境中，将数据保存到用户主目录
if hasattr(sys, '_MEIPASS'):
    # 打包后的数据路径（用户主目录）
    PLAYER_DATA_PATH = os.path.join(os.path.expanduser('~'), 'snake_game_player_data.json')
else:
    # 开发环境中的路径
    PLAYER_DATA_PATH = get_resource_path('player_data.json')

# 首次运行检测
if not os.path.exists(PLAYER_DATA_PATH):
    with open(PLAYER_DATA_PATH, 'w', encoding='utf-8') as f:
        f.write('{"coins": 0, "sign_in_streak": 0, "max_sign_in_streak": 0}')

class Player:
    def __init__(self, data_file=PLAYER_DATA_PATH):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            # Default data
            return {
                "coins": 0,
                "sign_in_streak": 0,
                "max_sign_in_streak": 0,
                "purchased_skins": ["default_rectangle"],
                "equipped_skin": "default_rectangle"
            }

    def _save_data(self):
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            # 尝试写入文件
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
            return True
        except Exception as e:
            print(f"保存玩家数据失败: {e}")
            # 尝试保存到用户主目录作为备选
            try:
                alt_path = os.path.join(os.path.expanduser('~'), 'snake_game_player_data.json')
                with open(alt_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4)
                print(f"已保存数据到备用路径: {alt_path}")
                return True
            except Exception as e2:
                print(f"保存到备用路径也失败: {e2}")
                return False

    def get_coins(self):
        return self.data.get("coins", 0)

    def add_coins(self, amount):
        self.data["coins"] = self.get_coins() + amount
        self._save_data()

    def spend_coins(self, amount):
        if self.get_coins() >= amount:
            self.data["coins"] -= amount
            self._save_data()
            return True
        return False

    def get_purchased_skins(self):
        return self.data.get("purchased_skins", ["default_rectangle"])

    def add_purchased_skin(self, skin_id):
        if "purchased_skins" not in self.data:
            self.data["purchased_skins"] = []
        if skin_id not in self.data["purchased_skins"]:
            self.data["purchased_skins"].append(skin_id)
            self._save_data()

    def get_equipped_skin(self):
        return self.data.get("equipped_skin", "default_rectangle")

    def equip_skin(self, skin_id):
        if skin_id in self.get_purchased_skins():
            self.data["equipped_skin"] = skin_id
            self._save_data()

player_data = Player()