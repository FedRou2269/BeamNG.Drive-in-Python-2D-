import pygame
import pymunk
import pymunk.pygame_util
import math

WIDTH, HEIGHT = 850, 450
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

space = pymunk.Space()
space.gravity = (0, 1500) 

# --- ФУНКЦИИ ---
def create_node(pos, mass):
    body = pymunk.Body(mass, pymunk.moment_for_box(mass, (40, 40)))
    body.position = pos
    shape = pymunk.Circle(body, 7)
    shape.color = (120, 120, 120, 255)
    space.add(body, shape)
    return body

def create_wheel(pos):
    body = pymunk.Body(3.0, pymunk.moment_for_circle(3.0, 0, 32))
    body.position = pos
    shape = pymunk.Circle(body, 32)
    shape.friction = 1.8
    shape.color = (60, 130, 255, 255) # Твои синие колеса
    space.add(body, shape)
    return body

def link_frame(b1, b2):
    d = b1.position.get_distance(b2.position)
    spring = pymunk.DampedSpring(b1, b2, (0,0), (0,0), d, 6000, 100)
    space.add(spring)
    return spring

def link_suspension(b1, b2):
    d = b1.position.get_distance(b2.position)
    spring = pymunk.DampedSpring(b1, b2, (0,0), (0,0), d, 2500, 50)
    space.add(spring)
    return spring

# --- СБОРКА МАШИНЫ ---
low_back = create_node((120, 260), 25.0)
low_front = create_node((530, 260), 25.0)
up_back = create_node((200, 160), 1.0)
up_front = create_node((450, 160), 1.0)
center = create_node((325, 210), 15.0)

frame_springs = []
suspension_springs = []

links = [(low_back, low_front), (up_back, up_front), (low_back, up_back), 
         (low_front, up_front), (low_back, center), (low_front, center), 
         (up_back, center), (up_front, center)]
for b1, b2 in links:
    frame_springs.append(link_frame(b1, b2))

w_back = create_wheel((160, 350))
w_front = create_wheel((490, 350))

for w, nodes in [(w_back, [low_back, up_back, center]), 
                 (w_front, [low_front, up_front, center])]:
    for n in nodes:
        suspension_springs.append(link_suspension(w, n))

space.add(pymunk.SlideJoint(w_back, w_front, (0,0), (0,0), 300, 350))

# --- МИР (ИСПРАВЛЕННЫЕ СТЕНЫ) ---
static = space.static_body
# Пол
ground = pymunk.Segment(static, (-2000, 420), (5000, 420), 20)
ground.friction = 1.0
ground.color = (100, 100, 100, 255)
# Стены
wall_r = pymunk.Segment(static, (1600, 0), (1600, 420), 50)
wall_l = pymunk.Segment(static, (-800, 0), (-800, 420), 50)
wall_r.friction = wall_l.friction = 1.0
# Добавляем всё в пространство
space.add(ground, wall_r, wall_l)

def draw_spring(spring, color, cam_x):
    p1 = spring.a.local_to_world(spring.anchor_a)
    p2 = spring.b.local_to_world(spring.anchor_b)
    pygame.draw.line(screen, color, (p1[0] - cam_x, p1[1]), (p2[0] - cam_x, p2[1]), 4)

target_speed = 0
max_speed = 55
acc = 0.6

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: exit()

    # УПРАВЛЕНИЕ
    keys = pygame.key.get_pressed()
    is_touch = pygame.mouse.get_pressed()[0]
    mx = pygame.mouse.get_pos()[0]

    if keys[pygame.K_d] or (is_touch and mx > WIDTH/2):
        if target_speed < max_speed: target_speed += acc
    elif keys[pygame.K_a] or (is_touch and mx < WIDTH/2):
        if target_speed > -max_speed: target_speed -= acc
    else:
        target_speed *= 0.97

    w_back.angular_velocity = target_speed
    w_front.angular_velocity = target_speed

    cam_x = center.position.x - WIDTH / 2
    screen.fill((230, 235, 240))
    
    for _ in range(3): space.step(1/180.0)

    # --- 1. РИСУЕМ КОРПУС (СКИН) ---
    body_points = [
        (low_back.position.x - cam_x, low_back.position.y),
        (up_back.position.x - cam_x, up_back.position.y),
        (up_front.position.x - cam_x, up_front.position.y),
        (low_front.position.x - cam_x, low_front.position.y)
    ]
    pygame.draw.polygon(screen, (220, 80, 80), body_points) 
    pygame.draw.polygon(screen, (0, 0, 0), body_points, 3) 

    # --- 2. РИСУЕМ ПРУЖИНЫ ---
    for s in frame_springs: draw_spring(s, (80, 80, 80), cam_x)
    for s in suspension_springs: draw_spring(s, (255, 40, 40), cam_x)

    # --- 3. РИСУЕМ ФОРМЫ (КОЛЕСА И СТЕНЫ) ---
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    # DRAW_SHAPES рисует и круги, и сегменты (стены)
    draw_options.flags = pymunk.pygame_util.DrawOptions.DRAW_SHAPES
    from pymunk import Transform
    draw_options.transform = Transform(tx=-cam_x, ty=0)
    space.debug_draw(draw_options)

    pygame.display.flip()
    clock.tick(60)
