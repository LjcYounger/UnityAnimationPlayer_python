import os
import pygame
from pygame.locals import *

from animation_player import AnimationPlayer

# --- Configuration ---
ANIM_FOLDER = "examples/AnimationClip"  # Change to your animation folder path
IMAGE_PATH = "Images"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FONT_SIZE = 24
BACKGROUND_COLOR = (40, 44, 52)  # Dark background
UI_COLOR = (86, 182, 194)  # Cyan UI
TEXT_COLOR = (220, 220, 220)  # Light gray text

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
        
        # Animation path switching
        self.paths = []
        self.current_path_index = 0
        
        # Animation playback control
        self.animation_time = 0.0
        self.animation_speed = 1.0
        self.is_playing = True
        self.loop_animation = True

    def load_animations_list(self):
        """Load all .anim files under the AnimationClip folder"""
        if not os.path.exists(ANIM_FOLDER):
            print(f"Error: Folder '{ANIM_FOLDER}' not found!")
            return []
        
        files = [f for f in os.listdir(ANIM_FOLDER) if f.endswith('.anim')]
        # Remove suffix and sort
        anim_names = sorted([os.path.splitext(f)[0] for f in files])
        
        if not anim_names:
            print(f"No .anim files found in {ANIM_FOLDER}")
        
        return anim_names

    def draw_file_browser(self):
        """Draw file selection interface"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Title
        title = self.font.render("Select a 2D Animation File (.anim):", True, UI_COLOR)
        self.screen.blit(title, (50, 50))

        # File list
        y_offset = 100
        mouse_y = pygame.mouse.get_pos()[1]
        
        for i, name in enumerate(self.animation_names):
            # Highlight hovered item
            if y_offset <= mouse_y <= y_offset + 30:
                pygame.draw.rect(self.screen, (60, 70, 90), (45, y_offset - 5, 700, 30))
            
            # Display file name
            text = self.font.render(f"  {i+1:2d}. {name}", True, TEXT_COLOR)
            self.screen.blit(text, (50, y_offset))
            y_offset += 30
            
            # New line after every 10 items
            if i > 0 and (i + 1) % 10 == 0:
                y_offset += 20

        # Hint message
        hint = self.font.render("Click to select or press ENTER for first animation", True, (150, 150, 150))
        self.screen.blit(hint, (50, SCREEN_HEIGHT - 40))

        pygame.display.flip()

    def run_file_browser(self):
        """Run file selection logic"""
        selecting = True
        while selecting:
            self.draw_file_browser()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return None
                
                if event.type == MOUSEBUTTONDOWN and event.button == 1:  # Left click
                    # Calculate which file was clicked
                    y_click = event.pos[1]
                    # Consider multi-column layout
                    index = (y_click - 100) // 30
                    if 0 <= index < len(self.animation_names):
                        selected_anim = self.animation_names[index]
                        return selected_anim
                
                if event.type == KEYDOWN:
                    if event.key == K_RETURN and self.animation_names:
                        # Enter key loads the first one
                        return self.animation_names[0]
                    elif event.key == K_ESCAPE:
                        return None

            self.clock.tick(30)

    def load_assets(self, anim_path):
        """Load animation and images"""
        try:
            print(f"Loading animation: {anim_path}")
            
            # 1. Load animation
            self.anim_player = AnimationPlayer(anim_path)
            print(f"  - Animation duration: {self.anim_player.stop_time:.2f}s")
            
            # 2. Get all available paths (Path)
            self.paths = list(self.anim_player.anim.keys())
            if not self.paths:
                print("  - Warning: No paths found in animation!")
                self.paths = ['general']  # Default fallback
            else:
                print(self.paths)
                print(f"  - Found {len(self.paths)} path(s): {', '.join(self.paths)}")
            
            self.current_path_index = 0
            self.animation_time = 0.0
            
            # 3. Load images
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
                # Create placeholder image
                print(f"  - Image not found. Creating placeholder.")
                self.image_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
                # Draw a simple cross marker
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
        """Draw text"""
        text_surf = self.font.render(text, True, color)
        surface.blit(text_surf, (x, y))

    def draw_ui(self):
        """Draw UI interface"""
        # Semi-transparent background
        ui_bg = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 180))
        self.screen.blit(ui_bg, (0, 0))
        
        # Animation information
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
        
        # Control hints
        controls = [
            "CONTROLS:",
            "UP/DOWN: Switch Path  |  SPACE: Play/Pause",
            "LEFT/RIGHT: Speed  |  R: Reset  |  L: Toggle Loop",
            "F: Next File  |  ESC: Quit"
        ]
        
        for i, line in enumerate(controls):
            self.draw_text(self.screen, line, 20, SCREEN_HEIGHT - 90 + i * 25, (180, 180, 180))

    def apply_2d_transforms(self, frame_data, image_surface):
        """Apply 2D transforms to image"""
        if not frame_data:
            return image_surface, image_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # Default position centered
        pos_x, pos_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # 1. Apply position
        if 'position' in frame_data:
            pos_data = frame_data['position']
            if isinstance(pos_data, tuple) and len(pos_data) >= 2:
                pos_x, pos_y = SCREEN_WIDTH/2 + pos_data[0], SCREEN_HEIGHT/2 - pos_data[1]
        
        # 2. Apply scaling
        scale_x, scale_y = 1.0, 1.0
        if 'scale' in frame_data:
            scale_data = frame_data['scale']
            if isinstance(scale_data, tuple) and len(scale_data) >= 2:
                scale_x, scale_y = scale_data[0], scale_data[1]
        
        # 3. Apply rotation
        angle = 0
        if 'rotation' in frame_data:
            angle = frame_data['rotation']
            # If radians convert to degrees (assuming return is radians)
            # angle = math.degrees(angle)
        elif 'euler' in frame_data:
            angle = frame_data['euler']
            # If radians convert to degrees (assuming return is radians)
            # angle = math.degrees(angle)
        
        # Apply transforms (scale first then rotate)
        if scale_x != 1.0 or scale_y != 1.0:
            original_size = image_surface.get_size()
            new_size = (int(original_size[0] * scale_x), int(original_size[1] * scale_y))
            if new_size[0] > 0 and new_size[1] > 0:
                image_surface = pygame.transform.scale(image_surface, new_size)
        
        if angle != 0:
            image_surface = pygame.transform.rotate(image_surface, angle)
        
        # Calculate new rectangle (center point unchanged)
        transformed_rect = image_surface.get_rect(center=(pos_x, pos_y))
        
        return image_surface, transformed_rect

    def run(self):
        """Main loop"""
        # Step 1: Select file
        self.animation_names = self.load_animations_list()
        if not self.animation_names:
            print("No animation files to load. Exiting.")
            return
        
        selected_anim = self.run_file_browser()
        if not selected_anim:
            pygame.quit()
            return
        
        # Step 2: Load resources
        if not self.load_assets(os.path.join(ANIM_FOLDER, selected_anim + '.anim')):
            print("Failed to load assets. Exiting.")
            pygame.quit()
            return
        
        # Main loop
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Update animation time
            if self.is_playing:
                self.animation_time += dt * self.animation_speed
                
                # Loop handling
                if self.animation_time > self.anim_player.stop_time:
                    if self.loop_animation:
                        self.animation_time %= self.anim_player.stop_time
                    else:
                        self.animation_time = self.anim_player.stop_time
                        self.is_playing = False
            
            # Event handling
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                # Keyboard controls
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        # Previous path
                        self.current_path_index = (self.current_path_index - 1) % len(self.paths)
                        print(f"Path: {self.paths[self.current_path_index]}")
                    
                    elif event.key == K_DOWN:
                        # Next path
                        self.current_path_index = (self.current_path_index + 1) % len(self.paths)
                        print(f"Path: {self.paths[self.current_path_index]}")
                    
                    elif event.key == K_SPACE:
                        # Play/Pause
                        self.is_playing = not self.is_playing
                        print(f"{'Playing' if self.is_playing else 'Paused'}")
                    
                    elif event.key == K_r:
                        # Reset animation
                        self.animation_time = 0.0
                        print("Animation reset")
                    
                    elif event.key == K_l:
                        # Toggle loop
                        self.loop_animation = not self.loop_animation
                        print(f"Loop: {'ON' if self.loop_animation else 'OFF'}")
                    
                    elif event.key == K_LEFT:
                        # Slow down
                        self.animation_speed = max(0.1, self.animation_speed - 0.5)
                        print(f"Speed: {self.animation_speed:.1f}x")
                    
                    elif event.key == K_RIGHT:
                        # Speed up
                        self.animation_speed = min(5.0, self.animation_speed + 0.5)
                        print(f"Speed: {self.animation_speed:.1f}x")
                    
                    elif event.key == K_f:
                        # Switch to next file
                        current_index = self.animation_names.index(selected_anim)
                        next_index = (current_index + 1) % len(self.animation_names)
                        selected_anim = self.animation_names[next_index]
                        self.load_assets(os.path.join(ANIM_FOLDER, selected_anim + '.anim'))
                    
                    elif event.key == K_ESCAPE:
                        running = False
            
            # Drawing
            self.screen.fill(BACKGROUND_COLOR)
            
            if self.anim_player and self.image_surface:
                # Get current frame data
                path_name = self.paths[self.current_path_index]
                frame_data, valid = self.anim_player.play_frame(
                    nowtime=self.animation_time, 
                    path=path_name
                )
                
                if valid:
                    # Apply 2D transforms and draw
                    transformed_img, img_rect = self.apply_2d_transforms(frame_data, self.image_surface.copy())
                    self.screen.blit(transformed_img, img_rect)
                    
                    # Draw center point marker
                    pygame.draw.circle(self.screen, (0, 255, 0), img_rect.center, 5)
                    pygame.draw.circle(self.screen, (0, 150, 0), img_rect.center, 8, 1)
                else:
                    # Animation ended
                    text = self.font.render("ANIMATION ENDED", True, (255, 100, 100))
                    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    self.screen.blit(text, text_rect)
            else:
                # Load failed
                text = self.font.render("LOAD FAILED", True, (255, 0, 0))
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(text, text_rect)
            
            # Draw UI
            self.draw_ui()
            
            # Draw FPS
            self.draw_text(self.screen, f"FPS: {self.clock.get_fps():.1f}", 
                          SCREEN_WIDTH - 100, 10, (150, 150, 150))
            
            pygame.display.flip()
        
        pygame.quit()

# Run program
app = AnimationTest()
app.run()