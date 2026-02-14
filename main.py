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

def main():
    tracker = None
    try:
        logging.info(f"System boot at {datetime.now()}. Log Level: {getattr(config, 'LOG_LEVEL', 'ERROR')}")
        pygame.display.init()
        pygame.font.init()
        utils.check_pygame_modules()

        physical_screen = pygame.display.set_mode((400, 1280), pygame.FULLSCREEN)
        radar_surface = pygame.Surface((config.SCREEN_WIDTH + 10, config.SCREEN_HEIGHT + 10))
        
        clock = pygame.time.Clock()
        background = utils.load_background(config.BACKGROUND_PATH) if config.BACKGROUND_PATH else None
        font_cache = {'header': utils.load_font(config.HEADER_FONT_SIZE)}

        audio = AudioManager(config.ATC_STREAM_URL)
        tracker = AircraftTracker()
        tracker.start()

        radar = RadarScope(radar_surface, 205, 225, 135)
        table = DataTable(radar_surface, 395, 85, 880, config.SCREEN_HEIGHT - 110)

        last_jitter_time = time.time()
        off_x, off_y = 0, 0

        running = True
        while running:
            theme = get_current_theme()
            now = time.time()

            if now - last_jitter_time > 300:
                off_x = (off_x + 1) % 5
                off_y = (off_y + 1) % 5
                last_jitter_time = now

            if background:
                radar_surface.blit(background, (0, 0))
            else:
                radar_surface.fill(config.BLACK)

            header_text = f"{config.AREA_NAME} - {config.LAT}, {config.LON} - {datetime.now().strftime('%H:%M:%S')}"
            header = font_cache['header'].render(header_text, True, theme['amber'])
            
            radar_surface.blit(header, header.get_rect(centerx=(radar_surface.get_width() // 2) + 40, y=20))

            current_aircraft = list(tracker.aircraft)
            radar.draw(current_aircraft, theme, tracker.last_update)
            table.draw(current_aircraft, tracker.status, tracker.last_update, theme)

            rotated_final = pygame.transform.rotate(radar_surface, 90)
            physical_screen.blit(rotated_final, (-off_x, -off_y))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE)):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                    if audio: audio.toggle()

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