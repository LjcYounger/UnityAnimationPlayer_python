import os
import pygame
from pygame.locals import *

from animation_player import AnimationPlayer

# --- 配置 ---
ANIM_FOLDER = "examples/AnimationClip"  # 改为你的动画文件夹路径
IMAGE_PATH = "Images"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FONT_SIZE = 24
BACKGROUND_COLOR = (40, 44, 52)  # 深色背景
UI_COLOR = (86, 182, 194)  # 青蓝色UI
TEXT_COLOR = (220, 220, 220)  # 浅灰色文字

class AnimationTest:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D Animation Player Tester")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', FONT_SIZE)
        
        self.anim_player = None
        self.image_surface = None
        self.animation_names = []
        
        # 动画路径切换
        self.paths = []
        self.current_path_index = 0
        
        # 动画播放控制
        self.animation_time = 0.0
        self.animation_speed = 1.0
        self.is_playing = True
        self.loop_animation = True

    def load_animations_list(self):
        """加载 AnimationClip 文件夹下的所有 .anim 文件"""
        if not os.path.exists(ANIM_FOLDER):
            print(f"Error: Folder '{ANIM_FOLDER}' not found!")
            return []
        
        files = [f for f in os.listdir(ANIM_FOLDER) if f.endswith('.anim')]
        # 去掉后缀并排序
        anim_names = sorted([os.path.splitext(f)[0] for f in files])
        
        if not anim_names:
            print(f"No .anim files found in {ANIM_FOLDER}")
        
        return anim_names

    def draw_file_browser(self):
        """绘制文件选择界面"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # 标题
        title = self.font.render("Select a 2D Animation File (.anim):", True, UI_COLOR)
        self.screen.blit(title, (50, 50))

        # 文件列表
        y_offset = 100
        mouse_y = pygame.mouse.get_pos()[1]
        
        for i, name in enumerate(self.animation_names):
            # 高亮鼠标悬停的项目
            if y_offset <= mouse_y <= y_offset + 30:
                pygame.draw.rect(self.screen, (60, 70, 90), (45, y_offset - 5, 700, 30))
            
            # 显示文件名称
            text = self.font.render(f"  {i+1:2d}. {name}", True, TEXT_COLOR)
            self.screen.blit(text, (50, y_offset))
            y_offset += 30
            
            # 每10个项目后换行
            if i > 0 and (i + 1) % 10 == 0:
                y_offset += 20

        # 提示信息
        hint = self.font.render("Click to select or press ENTER for first animation", True, (150, 150, 150))
        self.screen.blit(hint, (50, SCREEN_HEIGHT - 40))

        pygame.display.flip()

    def run_file_browser(self):
        """运行文件选择逻辑"""
        selecting = True
        while selecting:
            self.draw_file_browser()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return None
                
                if event.type == MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                    # 计算点击了哪个文件
                    y_click = event.pos[1]
                    # 考虑多列布局
                    index = (y_click - 100) // 30
                    if 0 <= index < len(self.animation_names):
                        selected_anim = self.animation_names[index]
                        return selected_anim
                
                if event.type == KEYDOWN:
                    if event.key == K_RETURN and self.animation_names:
                        # 回车键加载第一个
                        return self.animation_names[0]
                    elif event.key == K_ESCAPE:
                        return None

            self.clock.tick(30)

    def load_assets(self, anim_path):
        """加载动画和图片"""
        try:
            print(f"Loading animation: {anim_path}")
            
            # 1. 加载动画
            self.anim_player = AnimationPlayer(anim_path)
            print(f"  - Animation duration: {self.anim_player.stop_time:.2f}s")
            
            # 2. 获取所有可用的路径 (Path)
            self.paths = list(self.anim_player.anim.keys())
            if not self.paths:
                print("  - Warning: No paths found in animation!")
                self.paths = ['general']  # 默认回退
            else:
                print(self.paths)
                print(f"  - Found {len(self.paths)} path(s): {', '.join(self.paths)}")
            
            self.current_path_index = 0
            self.animation_time = 0.0
            
            # 3. 加载图片
            img_loaded = False
            
            img_path = IMAGE_PATH
            if os.path.exists(img_path):
                try:
                    self.image_surface = pygame.image.load(img_path).convert_alpha()
                    print(f"  - Loaded image: {img_path}")
                    img_loaded = True
                except Exception as e:
                    print(f"  - Error loading image {img_path}: {e}")
            
            if not img_loaded:
                # 创建占位图
                print(f"  - Image not found. Creating placeholder.")
                self.image_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
                # 绘制一个简单的十字标记
                pygame.draw.circle(self.image_surface, (255, 100, 100), (100, 100), 80, 3)
                pygame.draw.line(self.image_surface, (255, 100, 100), (100, 20), (100, 180), 3)
                pygame.draw.line(self.image_surface, (255, 100, 100), (20, 100), (180, 100), 3)
                
            return True
            
        except Exception as e:
            print(f"Error loading assets: {e}")
            import traceback
            traceback.print_exc()
            return False

    def draw_text(self, surface, text, x, y, color=TEXT_COLOR):
        """绘制文字"""
        text_surf = self.font.render(text, True, color)
        surface.blit(text_surf, (x, y))

    def draw_ui(self):
        """绘制UI界面"""
        # 半透明背景
        ui_bg = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 180))
        self.screen.blit(ui_bg, (0, 0))
        
        # 动画信息
        if self.anim_player:
            current_path = self.paths[self.current_path_index] if self.paths else 'None'
            
            info_lines = [
                f"Animation: {self.animation_names[0] if self.animation_names else 'None'}",
                f"Path: {current_path} ({self.current_path_index + 1}/{len(self.paths)})",
                f"Time: {self.animation_time:.2f}/{self.anim_player.stop_time:.2f}s",
                f"Speed: {self.animation_speed:.1f}x",
                f"Status: {'PLAYING' if self.is_playing else 'PAUSED'}",
                f"Loop: {'ON' if self.loop_animation else 'OFF'}"
            ]
            
            for i, line in enumerate(info_lines):
                self.draw_text(self.screen, line, 20, 10 + i * 25, UI_COLOR)
        
        # 控制提示
        controls = [
            "CONTROLS:",
            "UP/DOWN: Switch Path  |  SPACE: Play/Pause",
            "LEFT/RIGHT: Speed  |  R: Reset  |  L: Toggle Loop",
            "F: Next File  |  ESC: Quit"
        ]
        
        for i, line in enumerate(controls):
            self.draw_text(self.screen, line, 20, SCREEN_HEIGHT - 90 + i * 25, (180, 180, 180))

    def apply_2d_transforms(self, frame_data, image_surface):
        """应用2D变换到图片"""
        if not frame_data:
            return image_surface, image_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # 默认位置居中
        pos_x, pos_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # 1. 应用位置
        if 'position' in frame_data:
            pos_data = frame_data['position']
            if isinstance(pos_data, tuple) and len(pos_data) >= 2:
                pos_x, pos_y = SCREEN_WIDTH/2 + pos_data[0], SCREEN_HEIGHT/2 - pos_data[1]
        
        # 2. 应用缩放
        scale_x, scale_y = 1.0, 1.0
        if 'scale' in frame_data:
            scale_data = frame_data['scale']
            if isinstance(scale_data, tuple) and len(scale_data) >= 2:
                scale_x, scale_y = scale_data[0], scale_data[1]
        
        # 3. 应用旋转
        angle = 0
        if 'rotation' in frame_data:
            angle = frame_data['rotation']
            # 如果是弧度转换为角度（假设返回的是弧度）
            # angle = math.degrees(angle)
        elif 'euler' in frame_data:
            angle = frame_data['euler']
            # 如果是弧度转换为角度（假设返回的是弧度）
            # angle = math.degrees(angle)
        
        # 应用变换（先缩放后旋转）
        if scale_x != 1.0 or scale_y != 1.0:
            original_size = image_surface.get_size()
            new_size = (int(original_size[0] * scale_x), int(original_size[1] * scale_y))
            if new_size[0] > 0 and new_size[1] > 0:
                image_surface = pygame.transform.scale(image_surface, new_size)
        
        if angle != 0:
            image_surface = pygame.transform.rotate(image_surface, angle)
        
        # 计算新的矩形（中心点不变）
        transformed_rect = image_surface.get_rect(center=(pos_x, pos_y))
        
        return image_surface, transformed_rect

    def run(self):
        """主循环"""
        # 第一步：选择文件
        self.animation_names = self.load_animations_list()
        if not self.animation_names:
            print("No animation files to load. Exiting.")
            return
        
        selected_anim = self.run_file_browser()
        if not selected_anim:
            pygame.quit()
            return
        
        # 第二步：加载资源
        if not self.load_assets(os.path.join(ANIM_FOLDER, selected_anim + '.anim')):
            print("Failed to load assets. Exiting.")
            pygame.quit()
            return
        
        # 主循环
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # 更新动画时间
            if self.is_playing:
                self.animation_time += dt * self.animation_speed
                
                # 循环处理
                if self.animation_time > self.anim_player.stop_time:
                    if self.loop_animation:
                        self.animation_time %= self.anim_player.stop_time
                    else:
                        self.animation_time = self.anim_player.stop_time
                        self.is_playing = False
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                # 键盘控制
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        # 上一个路径
                        self.current_path_index = (self.current_path_index - 1) % len(self.paths)
                        print(f"Path: {self.paths[self.current_path_index]}")
                    
                    elif event.key == K_DOWN:
                        # 下一个路径
                        self.current_path_index = (self.current_path_index + 1) % len(self.paths)
                        print(f"Path: {self.paths[self.current_path_index]}")
                    
                    elif event.key == K_SPACE:
                        # 播放/暂停
                        self.is_playing = not self.is_playing
                        print(f"{'Playing' if self.is_playing else 'Paused'}")
                    
                    elif event.key == K_r:
                        # 重置动画
                        self.animation_time = 0.0
                        print("Animation reset")
                    
                    elif event.key == K_l:
                        # 切换循环
                        self.loop_animation = not self.loop_animation
                        print(f"Loop: {'ON' if self.loop_animation else 'OFF'}")
                    
                    elif event.key == K_LEFT:
                        # 减慢速度
                        self.animation_speed = max(0.1, self.animation_speed - 0.5)
                        print(f"Speed: {self.animation_speed:.1f}x")
                    
                    elif event.key == K_RIGHT:
                        # 加快速度
                        self.animation_speed = min(5.0, self.animation_speed + 0.5)
                        print(f"Speed: {self.animation_speed:.1f}x")
                    
                    elif event.key == K_f:
                        # 切换下一个文件
                        current_index = self.animation_names.index(selected_anim)
                        next_index = (current_index + 1) % len(self.animation_names)
                        selected_anim = self.animation_names[next_index]
                        self.load_assets(os.path.join(ANIM_FOLDER, selected_anim + '.anim'))
                    
                    elif event.key == K_ESCAPE:
                        running = False
            
            # 绘制
            self.screen.fill(BACKGROUND_COLOR)
            
            if self.anim_player and self.image_surface:
                # 获取当前帧数据
                path_name = self.paths[self.current_path_index]
                frame_data, valid = self.anim_player.play_frame(
                    nowtime=self.animation_time, 
                    path=path_name
                )
                
                if valid:
                    # 应用2D变换并绘制
                    transformed_img, img_rect = self.apply_2d_transforms(frame_data, self.image_surface.copy())
                    self.screen.blit(transformed_img, img_rect)
                    
                    # 绘制中心点标记
                    pygame.draw.circle(self.screen, (0, 255, 0), img_rect.center, 5)
                    pygame.draw.circle(self.screen, (0, 150, 0), img_rect.center, 8, 1)
                else:
                    # 动画结束
                    text = self.font.render("ANIMATION ENDED", True, (255, 100, 100))
                    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    self.screen.blit(text, text_rect)
            else:
                # 加载失败
                text = self.font.render("LOAD FAILED", True, (255, 0, 0))
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(text, text_rect)
            
            # 绘制UI
            self.draw_ui()
            
            # 绘制FPS
            self.draw_text(self.screen, f"FPS: {self.clock.get_fps():.1f}", 
                          SCREEN_WIDTH - 100, 10, (150, 150, 150))
            
            pygame.display.flip()
        
        pygame.quit()

# 运行程序
app = AnimationTest()
app.run()