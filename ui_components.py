import pygame
import time
import math
import json
import os
import config
import utils

class TerrainOverlay:
    """Logic for loading and filtering local GeoJSON data."""
    def __init__(self, filepath: str):
        self.paths = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    for feature in data.get('features', []):
                        geom = feature.get('geometry', {})
                        props = feature.get('properties', {})
                        f_type = 'water' if 'waterway' in props or props.get('natural') == 'water' else 'road' if 'highway' in props else 'generic'
                        if geom.get('type') == 'LineString': 
                            self.paths.append((geom['coordinates'], f_type))
                        elif geom.get('type') in ['Polygon', 'MultiLineString']:
                            for ring in geom['coordinates']:
                                if isinstance(ring[0], list): self.paths.append((ring, f_type))
            except Exception: pass

class RadarScope:
    """The circular PPI display with 12 RPM sweep and breadcrumbs."""
    def __init__(self, screen, center_x, center_y, radius):
        self.screen, self.center_x, self.center_y, self.radius = screen, center_x, center_y, radius
        self.font = utils.load_font(config.RADAR_FONT_SIZE)
        self.degree_font = utils.load_font(int(config.RADAR_FONT_SIZE * 0.8))
        self.sweep_angle, self.rotation = 0, getattr(config, 'RADAR_ROTATION', 0)
        self.show_terrain = getattr(config, 'TERRAIN', False)
        self.terrain = TerrainOverlay('terrain.json') if self.show_terrain else None
        self.history = {} 

    def project(self, lat, lon):
        try:
            lat_dist = (lat - config.LAT) * 111.2
            lon_dist = (lon - config.LON) * (111.2 * math.cos(math.radians(config.LAT)))
            angle_rad = math.radians(-self.rotation)
            rlon = lon_dist * math.cos(angle_rad) - lat_dist * math.sin(angle_rad)
            rlat = lon_dist * math.sin(angle_rad) + lat_dist * math.cos(angle_rad)
            range_km = config.RADIUS_NM * 1.852
            return int(self.center_x + (rlon / range_km) * self.radius), int(self.center_y - (rlat / range_km) * self.radius)
        except: return self.center_x, self.center_y

    def draw_terrain(self, theme):
        if not self.terrain: return
        colors = {'water': (0, int(45 * theme['brightness']), 0), 'road': (0, int(90 * theme['brightness']), 0), 'generic': (0, int(35 * theme['brightness']), 0)}
        for path, f_type in self.terrain.paths:
            color, pts = colors.get(f_type, colors['generic']), []
            for i in range(0, len(path), 2):
                lon, lat = path[i]
                px, py = self.project(lat, lon)
                if (px - self.center_x)**2 + (py - self.center_y)**2 <= self.radius**2: pts.append((px, py))
            if len(pts) > 1: pygame.draw.lines(self.screen, color, False, pts, 1)

    def draw_instrumentation(self, theme):
        for degree in range(0, 360, 10):
            rad = math.radians(degree - self.rotation)
            tl = 15 if degree % 20 == 0 else 8
            sx, sy = int(self.center_x + self.radius * math.sin(rad)), int(self.center_y - self.radius * math.cos(rad))
            ex, ey = int(self.center_x + (self.radius - tl) * math.sin(rad)), int(self.center_y - (self.radius - tl) * math.cos(rad))
            pygame.draw.line(self.screen, theme['bright_green'], (sx, sy), (ex, ey), 2)
            if degree % 20 == 0:
                lx, ly = int(self.center_x + (self.radius + 18) * math.sin(rad)), int(self.center_y - (self.radius + 18) * math.cos(rad))
                txt = pygame.transform.rotate(self.degree_font.render(f"{degree:03d}", True, theme['dim_green']), -(degree - self.rotation))
                self.screen.blit(txt, txt.get_rect(center=(lx, ly)))
        
        for label, angle in [("N", 0), ("E", 90), ("S", 180), ("W", 270)]:
            rad = math.radians(angle - self.rotation)
            tx, ty = int(self.center_x + (self.radius + 42) * math.sin(rad)), int(self.center_y - (self.radius + 42) * math.cos(rad))
            surf = self.font.render(label, True, theme['amber'])
            self.screen.blit(surf, surf.get_rect(center=(tx, ty)))

    def draw(self, aircraft_list, theme, last_update):
        if self.show_terrain: self.draw_terrain(theme)
        
        for ring in range(1, 4):
            r = int((ring / 3) * self.radius)
            pygame.draw.circle(self.screen, theme['dim_green'], (self.center_x, self.center_y), r, 1)
            surf = self.font.render(f"{round((ring/3)*config.RADIUS_NM)}NM", True, theme['dim_green'])
            self.screen.blit(surf, (self.center_x + r - surf.get_width() - 8, self.center_y - 22))

        self.draw_instrumentation(theme)
        
        pygame.draw.line(self.screen, theme['dim_green'], (self.center_x - self.radius, self.center_y), (self.center_x + self.radius, self.center_y), 1)
        pygame.draw.line(self.screen, theme['dim_green'], (self.center_x, self.center_y - self.radius), (self.center_x, self.center_y + self.radius), 1)
        pygame.draw.circle(self.screen, theme['bright_green'], (self.center_x, self.center_y), self.radius, 2)

        self.sweep_angle = (self.sweep_angle + 2.4) % 360
        for i in range(12):
            rad = math.radians(self.sweep_angle - i)
            ex, ey = int(self.center_x + self.radius * math.sin(rad)), int(self.center_y - self.radius * math.cos(rad))
            p_val = max(0, int((255 - (i * 20)) * theme['brightness']))
            pygame.draw.line(self.screen, (0, p_val, 0), (self.center_x, self.center_y), (ex, ey), 2)

        dt, blink = time.time() - last_update, int(time.time() * 2) % 2
        for a in aircraft_list:
            if not getattr(a, 'lat', 0): continue
            
            spd = getattr(a, 'speed', 0) or 0
            trk = getattr(a, 'track', 0) or 0
            e_lat, e_lon = a.lat, a.lon
            if 0 < dt < 10 and spd > 0:
                try:
                    dist = (spd / 3600.0) * dt
                    e_lat = a.lat + (dist * math.cos(math.radians(trk))) / 60.0
                    e_lon = a.lon + (dist * math.sin(math.radians(trk))) / (60.0 * math.cos(math.radians(a.lat)))
                except: pass

            pos = self.project(e_lat, e_lon)
            if (pos[0]-self.center_x)**2 + (pos[1]-self.center_y)**2 <= self.radius**2:
                is_mil = getattr(a, 'is_military', False)
                
                # COLOR PRIORITY: Emergency > Military > Standard
                sq = getattr(a, 'squawk', '')
                if sq in ['7700', '7500']: c = theme['red']
                elif sq == '7600': c = theme['amber']
                elif sq == '1200': c = (220, 220, 220) # White
                elif is_mil: c = theme['red']
                else: c = theme['bright_green']
                
                # Breadcrumbs - pretty sure this is broken
                a_hex = getattr(a, 'hex', 'none')
                if a_hex not in self.history: self.history[a_hex] = []
                if dt < 0.2 and (not self.history[a_hex] or self.history[a_hex][-1] != (a.lat, a.lon)):
                    self.history[a_hex].append((a.lat, a.lon))
                    if len(self.history[a_hex]) > 6: self.history[a_hex].pop(0)
                
                for pt in self.history[a_hex]:
                    h_pos = self.project(pt[0], pt[1])
                    pygame.draw.circle(self.screen, (int(c[0]*0.2), int(c[1]*0.2), int(c[2]*0.2)), h_pos, 1)

                if not is_mil or blink:
                    pygame.draw.circle(self.screen, c, pos, 5)
                    rad_v = math.radians((trk - self.rotation) % 360)
                    v_len = 15 + (30 * min(spd, 450) / 450)
                    pygame.draw.line(self.screen, c, pos, (int(pos[0]+v_len*math.sin(rad_v)), int(pos[1]-v_len*math.cos(rad_v))), 2)
                    self.screen.blit(self.font.render(str(getattr(a, 'callsign', '???')), True, c), (pos[0] + 8, pos[1] - 12))

class DataTable:
    def __init__(self, screen, x, y, width, height):
        self.screen, self.rect, self.font = screen, pygame.Rect(x, y, width, height), utils.load_font(config.TABLE_FONT_SIZE)
        self.last_alt = {}

    def draw(self, aircraft_list, status, last_update, theme):
        pygame.draw.rect(self.screen, theme['bright_green'], self.rect, 3)
        title = self.font.render("ADSB AIRCRAFT DATA", True, theme['amber'])
        self.screen.blit(title, title.get_rect(centerx=self.rect.centerx, y=self.rect.y + 10))
        
        headers = ["AIRLINE", "CALLSIGN", "TYPE", "  SQWK", "   ALT", "SPD", "DIST", "TRK"]
        
        ratios = [0.21, 0.20, 0.10, 0.10, 0.14, 0.10, 0.09, 0.06]
        
        col_pos = []
        curr_x = self.rect.x + 20
        for i, h in enumerate(headers):
            col_pos.append(curr_x)
            self.screen.blit(self.font.render(h, True, theme['amber']), (curr_x, self.rect.y + 40))
            curr_x += int((self.rect.width - 40) * ratios[i])
        
        pygame.draw.line(self.screen, theme['dim_green'], (self.rect.x+8, self.rect.y+65), (self.rect.right-8, self.rect.y+65), 1)

        sorted_list = sorted(aircraft_list, key=lambda x: getattr(x, 'distance', 999))[:10]
        for i, a in enumerate(sorted_list):
            y_pos = self.rect.y + 70 + i * config.TABLE_FONT_SIZE
            is_mil = getattr(a, 'is_military', False)
            sq = getattr(a, 'squawk', '')
            
            # COLOR LOGIC: Emergency > Radio > VFR > Military > Standard
            if sq in ['7700', '7500']: c = theme['red']
            elif sq == '7600': c = theme['amber']
            elif sq == '1200': c = (220, 220, 220) # White
            elif is_mil: c = theme['red']
            else: c = theme['bright_green']
            
            a_hex = getattr(a, 'hex', str(i))
            alt = getattr(a, 'altitude', 0)
            trend = "↑" if a_hex in self.last_alt and alt > self.last_alt[a_hex] + 100 else "↓" if a_hex in self.last_alt and alt < self.last_alt[a_hex] - 100 else " "
            self.last_alt[a_hex] = alt
            
            vals = [
                f"{str(getattr(a, 'own_op', '')):<7}",
                f"{str(getattr(a, 'callsign', '???')):<8}",
                f"{str(getattr(a, 'type', '???')):<4}", 
                f"{str(sq):<4}",
                f"{int(alt):>5}{trend}", 
                f"{int(getattr(a, 'speed', 0)):>3}", 
                f"{getattr(a, 'distance', 0):>4.1f}", 
                f"{int(getattr(a, 'track', 0)):>3.0f}°"
            ]
            for j, v in enumerate(vals): 
                self.screen.blit(self.font.render(v, True, c), (col_pos[j], y_pos))

        f_y = self.rect.bottom - (2 * config.TABLE_FONT_SIZE) - 15
        mil_count = sum(1 for a in aircraft_list if getattr(a, 'is_military', False))
        self.screen.blit(self.font.render(f"STATUS: {status}", True, theme['bright_green']), (self.rect.x + 20, f_y))
        self.screen.blit(self.font.render(f"CONTACTS: {len(aircraft_list)} ({mil_count} MIL)", True, theme['bright_green']), (self.rect.x + 20, f_y + config.TABLE_FONT_SIZE))
        
        rs_txt = self.font.render(f"RANGE: {config.RADIUS_NM}NM", True, theme['bright_green'])
        self.screen.blit(rs_txt, (self.rect.right - rs_txt.get_width() - 20, f_y))
        
        hb_c = theme['amber'] if (time.time() - last_update) < 0.6 else theme['dim_green']
        text_y = f_y + config.TABLE_FONT_SIZE
        self.screen.blit(self.font.render("SYNC", True, hb_c), (self.rect.right - 110, text_y))
        pygame.draw.rect(self.screen, hb_c, (self.rect.right - 45, text_y + 6, 19, 19))