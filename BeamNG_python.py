import pygame
import pymunk
import pymunk.pygame_util

# --- ИНИЦИАЛИЗАЦИЯ ---
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", int(HEIGHT * 0.05), bold=True)

space = pymunk.Space()
space.gravity = (0, 1500) 

# --- ТОЧКА СПАВНА ---
SPAWN_X = WIDTH // 4
SPAWN_Y = HEIGHT * 0.65 # Машина будет ближе к дороге при спавне

# --- ПАРАМЕТРЫ ФИЗИКИ v0.2 ---
MASS_LOW, MASS_UP, MASS_CENTER = 45.0, 2.0, 15.0
STIFF_FRAME, DAMP_FRAME = 15000, 450
STIFF_SUSP, DAMP_SUSP = 3200, 300

def create_node(pos, mass):
    body = pymunk.Body(mass, pymunk.moment_for_box(mass, (40, 40)))
    body.position = pos
    shape = pymunk.Circle(body, 7)
    shape.filter = pymunk.ShapeFilter(group=1)
    space.add(body, shape)
    return body

def create_wheel(pos):
    body = pymunk.Body(4.0, pymunk.moment_for_circle(4.0, 0, 32))
    body.position = pos
    shape = pymunk.Circle(body, 32)
    shape.friction = 2.0
    shape.filter = pymunk.ShapeFilter(group=1)
    space.add(body, shape)
    return body

def link_spring(b1, b2, stiffness, damping):
    d = b1.position.get_distance(b2.position)
    spring = pymunk.DampedSpring(b1, b2, (0,0), (0,0), d, stiffness, damping)
    space.add(spring)
    return spring

# Сборка
low_back = create_node((SPAWN_X, SPAWN_Y), MASS_LOW)
low_front = create_node((SPAWN_X + 350, SPAWN_Y), MASS_LOW)
up_back = create_node((SPAWN_X + 70, SPAWN_Y - 90), MASS_UP)
up_front = create_node((SPAWN_X + 280, SPAWN_Y - 90), MASS_UP)
center = create_node((SPAWN_X + 175, SPAWN_Y - 45), MASS_CENTER)

links = [(low_back, low_front), (up_back, up_front), (low_back, up_back), 
         (low_front, up_front), (low_back, center), (low_front, center), 
         (up_back, center), (up_front, center)]
frame_springs = [link_spring(b1, b2, STIFF_FRAME, DAMP_FRAME) for b1, b2 in links]

w_back = create_wheel((SPAWN_X + 30, SPAWN_Y + 80))
w_front = create_wheel((SPAWN_X + 320, SPAWN_Y + 80))

suspension_springs = []
for w, nodes in [(w_back, [low_back, up_back, center]), (w_front, [low_front, up_front, center])]:
    for n in nodes:
        suspension_springs.append(link_spring(w, n, STIFF_SUSP, DAMP_SUSP))

space.add(pymunk.SlideJoint(w_back, w_front, (0,0), (0,0), 280, 300))

# Мир
static = space.static_body
ground_y = HEIGHT * 0.85
ground = pymunk.Segment(static, (-100000, ground_y), (100000, ground_y), 25)
ground.friction = 1.2

wall_pos_x = int(WIDTH * 3.5)
wall = pymunk.Segment(static, (wall_pos_x, 0), (wall_pos_x, ground_y), 60)
space.add(ground, wall)

# Управление
target_speed = 0
max_speed = 70
accel = 0.5
handbrake = False

bw, bh = int(WIDTH * 0.18), int(HEIGHT * 0.15)
btn_gas = pygame.Rect(WIDTH - bw - 20, HEIGHT - bh - 20, bw, bh)
btn_rev = pygame.Rect(20, HEIGHT - bh - 20, bw, bh)
btn_brake = pygame.Rect(20, HEIGHT - bh*2 - 40, bw, bh)
btn_reset = pygame.Rect(WIDTH // 2 - bw // 2, 20, bw, int(bh * 0.7))

while True:
    mouse_pos = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()[0]
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if btn_reset.collidepoint(event.pos):
                low_back.position = (SPAWN_X, SPAWN_Y)
                low_front.position = (SPAWN_X + 350, SPAWN_Y)
                up_back.position = (SPAWN_X + 70, SPAWN_Y - 90)
                up_front.position = (SPAWN_X + 280, SPAWN_Y - 90)
                center.position = (SPAWN_X + 175, SPAWN_Y - 45)
                w_back.position = (SPAWN_X + 30, SPAWN_Y + 80)
                w_front.position = (SPAWN_X + 320, SPAWN_Y + 80)
                for b in space.bodies:
                    b.velocity = (0,0); b.angular_velocity = 0; b.angle = 0
                target_speed = 0

    handbrake = False
    if mouse_down:
        if btn_gas.collidepoint(mouse_pos):
            if target_speed < max_speed: target_speed += accel
        elif btn_rev.collidepoint(mouse_pos):
            if target_speed > -max_speed: target_speed -= accel
        elif btn_brake.collidepoint(mouse_pos): handbrake = True
    else: target_speed *= 0.92 

    w_back.angular_velocity = w_front.angular_velocity = 0 if handbrake else target_speed

    for _ in range(3): space.step(1/180.0)
    cam_x = center.position.x - WIDTH / 2
    
    screen.fill((220, 225, 230))
    
    # --- ОТРИСОВКА СЕТКИ (GROUND GRID) ---
    grid_size = 200
    start_grid = int(cam_x // grid_size) * grid_size
    for x in range(int(start_grid - grid_size), int(start_grid + WIDTH + grid_size), grid_size):
        pygame.draw.line(screen, (200, 205, 210), (x - cam_x, 0), (x - cam_x, ground_y), 2)

    def to_s(p): return (p[0] - cam_x, p[1])

    # Подвеска и кузов
    for s in suspension_springs:
        pygame.draw.line(screen, (200, 50, 50), to_s(s.a.position), to_s(s.b.position), 3)

    body_p = [to_s(n.position) for n in [low_back, up_back, up_front, low_front]]
    pygame.draw.polygon(screen, (220, 60, 60), body_p)
    pygame.draw.polygon(screen, (40, 40, 40), body_p, 3)

    opts = pymunk.pygame_util.DrawOptions(screen)
    opts.flags, opts.transform = pymunk.pygame_util.DrawOptions.DRAW_SHAPES, pymunk.Transform(tx=-cam_x)
    space.debug_draw(opts)

    # UI
    def draw_ui(rect, text, color):
        pygame.draw.rect(screen, color, rect, border_radius=20)
        pygame.draw.rect(screen, (30, 30, 30), rect, 4, border_radius=20)
        t = font.render(text, True, (255, 255, 255))
        screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    draw_ui(btn_gas, "GAS", (60, 160, 60))
    draw_ui(btn_rev, "REV", (170, 60, 60))
    draw_ui(btn_brake, "BRAKE", (210, 130, 0) if handbrake else (100, 100, 100))
    draw_ui(btn_reset, "RESET", (70, 70, 70))

    screen.blit(font.render(f"{abs(int(w_back.angular_velocity*1.5))} km/h", True, (0,0,0)), (30, 30))
    pygame.display.flip()
    clock.tick(60)
