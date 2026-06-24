import sys
import math
import pygame

# Initialize Pygame
pygame.init()

# --- CONFIGURATION & CONSTANTS ---
WIDTH, HEIGHT = 800, 800
FPS = 60
CENTER = (WIDTH // 2, HEIGHT // 2)

# Colors (RGBA for surface blending)
BG_COLOR = (5, 8, 20)
OUTLINE_COLOR = (51, 68, 85)
TEXT_COLOR = (102, 238, 255)
HOLE_BG_COLOR = (12, 18, 40) 

# Setup Window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3-Lobe Fidget Resonance (RGB) - Mirror Mode")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)

# --- HELPER FUNCTIONS FOR VISUAL EFFECTS ---

def draw_glow_circle(surface, color, center, max_radius, opacity=0.55):
	"""Draws a soft radial gradient light source using layered transparency."""
	glow_surf = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)
	cx, cy = max_radius, max_radius
	
	for i in range(steps := 30):
		r = max_radius * (1 - i / steps)
		alpha = int(255 * opacity * ((1 - i / steps) ** 2)) 
		pygame.draw.circle(glow_surf, (*color, alpha), (cx, cy), int(r))
		
	surface.blit(glow_surf, (center[0] - max_radius, center[1] - max_radius))

def get_fidget_points(center, scale=180):
	"""Generates a geometrically accurate 3-lobe spinner profile."""
	cx, cy = center
	points = []
	for i in range(360):
		rad = math.radians(i)
		r = scale * (1.3 + 0.7 * math.cos(3 * rad)) 
		x = cx + r * math.cos(rad)
		y = cy + r * math.sin(rad)
		points.append((x, y))
	return points

def get_lobe_tips(center, scale=175):
	"""Calculates the center positions of the 3 lobe tips."""
	cx, cy = center
	tips = []
	for deg in [0, 120, 240]:
		rad = math.radians(deg)
		r = scale * (1.3 + 0.7 * math.cos(3 * rad))
		x = cx + r * math.cos(rad)
		y = cy + r * math.sin(rad)
		tips.append((int(x), int(y)))
	return tips


class LightSource:
	"""Manages an individual draggable RGB light with wave animations."""
	def __init__(self, x, y, color, label):
		self.x = x
		self.y = y
		self.base_color = color  
		self.label = label
		self.is_dragging = False
		self.radius = 12
		self.drag_offset_x = 0
		self.drag_offset_y = 0
		
		self.wave_timers = [0.0, 1.13, 2.26]
		self.wave_duration = 3.4
		self.max_wave_radius = 450 

	def update(self, dt):
		for i in range(len(self.wave_timers)):
			self.wave_timers[i] += dt
			if self.wave_timers[i] >= self.wave_duration:
				self.wave_timers[i] -= self.wave_duration

	def draw_waves(self, surface, mask_surface):
		"""Draws expanding ripples bound to the mask canvas layer."""
		for timer in self.wave_timers:
			progress = timer / self.wave_duration
			r = 25 + (self.max_wave_radius - 25) * progress
			alpha = int(255 * 0.9 * (1 - progress))
			
			if alpha > 0:
				wave_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
				width = max(2, int(8 * (1 - progress * 0.5)))
				pygame.draw.circle(wave_surf, (*self.base_color, alpha), (int(self.x), int(self.y)), int(r), width)
				
				wave_surf.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
				surface.blit(wave_surf, (0, 0))

	def draw_core(self, surface):
		"""Draws the main bloom glow and white center node."""
		draw_glow_circle(surface, self.base_color, (int(self.x), int(self.y)), 100, opacity=0.55)
		pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius)

	def check_click(self, mouse_pos):
		mx, my = mouse_pos
		distance = math.hypot(mx - self.x, my - self.y)
		if distance <= self.radius + 15:  
			self.is_dragging = True
			self.drag_offset_x = self.x - mx
			self.drag_offset_y = self.y - my
			return True
		return False

	def handle_drag(self, mouse_pos):
		if self.is_dragging:
			mx, my = mouse_pos
			self.x = mx + self.drag_offset_x
			self.y = my + self.drag_offset_y


# --- INITIALIZATION ---

# Setup lights
lights = [
	LightSource(400, 260, (255, 68, 68), "Red"),       
	LightSource(275, 470, (68, 255, 68), "Green"),     
	LightSource(525, 470, (0, 187, 255), "Blue")       
]

fidget_poly = get_fidget_points(CENTER, scale=175)
hole_centers = get_lobe_tips(CENTER, scale=175)
hole_radius = 24

fidget_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
pygame.draw.polygon(fidget_mask, (255, 255, 255, 255), fidget_poly)
for hole_pos in hole_centers:
	pygame.draw.circle(fidget_mask, (255, 255, 255, 255), hole_pos, hole_radius)

# --- MAIN LOOP ---
running = True
active_light = None

while running:
	dt = clock.tick(FPS) / 1000.0  
	mouse_pos = pygame.mouse.get_pos()
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
			
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:  
				for light in reversed(lights):
					if light.check_click(mouse_pos):
						active_light = light
						break
						
		elif event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1 and active_light:
				active_light.is_dragging = False
				active_light = None

	# Handle Drag and Symmetrical Reflection Updates
	if active_light:
		# 1. Update the position of the light currently being dragged
		active_light.handle_drag(mouse_pos)
		
		# 2. Mirror the remaining lights based on the active node's distance to center
		# Center-relative coordinates of the active light
		dx = active_light.x - CENTER[0]
		dy = active_light.y - CENTER[1]
		
		# Rotational offset depends on which light is active to keep things balanced
		active_idx = lights.index(active_light)
		
		for idx, light in enumerate(lights):
			if light != active_light:
				# Calculate the angular step between lights (120 and 240 degrees difference)
				angle_offset = math.radians((idx - active_idx) * 120)
				
				# Apply rotation matrix around the center canvas vector
				# This causes them to mimic each other's distance/movement perfectly
				new_x = CENTER[0] + (dx * math.cos(angle_offset) - dy * math.sin(angle_offset))
				new_y = CENTER[1] + (dx * math.sin(angle_offset) + dy * math.cos(angle_offset))
				
				light.x = new_x
				light.y = new_y

	# Physics & Object Parameter Updates
	for light in lights:
		light.update(dt)

	# --- RENDERING ---
	screen.fill(BG_COLOR)
	
	# 1. Draw Background Radial Depth Style
	draw_glow_circle(screen, (24, 32, 64), CENTER, 400, opacity=0.3)

	# 2. Render RGB Waves Restricted to Fidget Boundaries + Lobe Openings
	for light in lights:
		light.draw_waves(screen, fidget_mask)

	# 3. Draw Fidget Outlined Contour
	pygame.draw.polygon(screen, OUTLINE_COLOR, fidget_poly, 16)

	# 4. Draw the Holes Cut Into the Tips
	for hole_pos in hole_centers:
		pygame.draw.circle(screen, OUTLINE_COLOR, hole_pos, hole_radius + 4, 4)
		pygame.draw.circle(screen, HOLE_BG_COLOR, hole_pos, hole_radius)

	# 5. Draw Core Glow & Light Knobs
	for light in lights:
		light.draw_core(screen)

	# 6. UI Text Render Overlay
	ui_text = font.render("3-Lobe Resonance • Symmetrical Mirror Drag", True, TEXT_COLOR)
	text_rect = ui_text.get_rect(centerx=WIDTH // 2, top=20)
	screen.blit(ui_text, text_rect)

	pygame.display.flip()

pygame.quit()
sys.exit()