import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
import sys
import time
import logging
import traceback
from datetime import datetime
import config
import utils
from audio_manager import AudioManager
from data_fetcher import AircraftTracker
from ui_components import RadarScope, DataTable

# Map string from .ini to logging constants
log_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
current_level = log_map.get(getattr(config, 'LOG_LEVEL', 'ERROR').upper(), logging.ERROR)

logging.basicConfig(
    filename='error.log',
    filemode='w',
    level=current_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_current_theme():
    """Returns color theme based on time of day (Day/Night mode)."""
    hour = datetime.now().hour
    is_night = hour >= 20 or hour < 8
    b = 0.3 if is_night else 1.0
    return {
        'brightness': b,
        'amber': (int(255 * b), int(191 * b), 0),
        'bright_green': (0, int(255 * b), 0),
        'dim_green': (0, int(80 * b), 0),
        'red': (int(255 * b), 0, 0),
        'yellow': (int(255 * b), int(255 * b), 0)
    }

def save_privacy_screenshot(surface, font, theme):
    """
    Takes the raw landscape surface, clones it, sanitizes the location data,
    and saves it to disk.
    """
    try:
        filename = f"radar_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # 1. Clone the surface so we don't mess up the actual display
        clean_surface = surface.copy()
        
        # 2. Erase the real header (Top 50 pixels)
        # We assume the background is black for the header area
        pygame.draw.rect(clean_surface, (0, 0, 0), (0, 0, clean_surface.get_width(), 50))
        
        # 3. Render Fake Header
        fake_text = f"{config.AREA_NAME} - 12.34567, -89.10121 - {datetime.now().strftime('%H:%M:%S')}"
        fake_header = font.render(fake_text, True, theme['amber'])
        
        # 4. Blit fake header (using same centering logic as main loop)
        clean_surface.blit(fake_header, fake_header.get_rect(centerx=(clean_surface.get_width() // 2) + 40, y=20))
        
        # 5. Save directly
        # Note: 'surface' is already the landscape version (before rotation), 
        # so we don't need to rotate it back. It's already correct.
        pygame.image.save(clean_surface, filename)
        
        return filename
    except Exception as e:
        logging.error(f"Screenshot error: {e}")
        return None

def main():
    tracker = None
    try:
        logging.info(f"System boot at {datetime.now()}. Log Level: {getattr(config, 'LOG_LEVEL', 'ERROR')}")
        pygame.display.init()
        pygame.font.init()
        utils.check_pygame_modules()

        # Initialize the physical display (Portrait Mode)
        physical_screen = pygame.display.set_mode((400, 1280), pygame.FULLSCREEN)
        
        # Virtual surface for drawing (before rotation)
        radar_surface = pygame.Surface((config.SCREEN_WIDTH + 10, config.SCREEN_HEIGHT + 10))
        
        clock = pygame.time.Clock()
        background = utils.load_background(config.BACKGROUND_PATH) if config.BACKGROUND_PATH else None
        font_cache = {'header': utils.load_font(config.HEADER_FONT_SIZE)}

        audio = AudioManager(config.ATC_STREAM_URL)
        tracker = AircraftTracker()
        tracker.start()

        # GEOMETRY (Fixed for Portrait Layout):
        # Radar Center: (205, 225) | Radius: 135
        # Table Position: (395, 85) | Width: 880
        radar = RadarScope(radar_surface, 205, 225, 135)
        table = DataTable(radar_surface, 395, 85, 880, config.SCREEN_HEIGHT - 110)

        last_jitter_time = time.time()
        off_x, off_y = 0, 0

        running = True
        while running:
            theme = get_current_theme()
            now = time.time()

            # Burn-in Protection: Jitter every 5 minutes
            if now - last_jitter_time > 300:
                off_x = (off_x + 1) % 5
                off_y = (off_y + 1) % 5
                last_jitter_time = now

            # Draw Background
            if background:
                radar_surface.blit(background, (0, 0))
            else:
                radar_surface.fill(config.BLACK)

            # Draw Header (Time & Location)
            header_text = f"{config.AREA_NAME} - {config.LAT}, {config.LON} - {datetime.now().strftime('%H:%M:%S')}"
            header = font_cache['header'].render(header_text, True, theme['amber'])
            
            # Centre Offset +40px right to align visually between Radar and Table
            radar_surface.blit(header, header.get_rect(centerx=(radar_surface.get_width() // 2) + 40, y=20))

            # Fetch & Draw Data
            current_aircraft = list(tracker.aircraft)
            radar.draw(current_aircraft, theme, tracker.last_update)
            table.draw(current_aircraft, tracker.status, tracker.last_update, theme)

            # Rotate & Blit to Screen
            rotated_final = pygame.transform.rotate(radar_surface, 90)
            physical_screen.blit(rotated_final, (-off_x, -off_y))

            # --- REMOTE SCREENSHOT TRIGGER
            if os.path.exists('screenshot.trigger'):
                # Pass the RAW radar_surface (Landscape) to the privacy saver
                fname = save_privacy_screenshot(radar_surface, font_cache['header'], theme)
                if fname:
                    logging.info(f"REMOTE CAPTURE: Saved {fname}")
                    print(f"Screenshot saved: {fname}")
                    try:
                        os.remove('screenshot.trigger')
                    except: pass

            pygame.display.flip()

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE)):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                    if audio: audio.toggle()
                
                # Keyboard Shortcut (S)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                    fname = save_privacy_screenshot(radar_surface, font_cache['header'], theme)
                    if fname:
                        logging.info(f"KEYBOARD CAPTURE: Saved {fname}")

            clock.tick(config.FPS)

    except Exception:
        logging.error("Fatal exception in main loop:")
        logging.error(traceback.format_exc())
    
    finally:
        if tracker:
            tracker.running = False
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()