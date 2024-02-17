import pygame
import math
import random
import can


# initialize pygame
pygame.init()


# Set up the screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("V2X Communication Simulation")

# Define parameters for virtual vehicles
NUM_VEHICLES = 5
VEHICLE_RADIUS = 20
MAX_SPEED = 5

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)


# Define CAN message IDs
MESSAGE_ID_1 = 0x100
MESSAGE_ID_2 = 0x200

# Create virtual CAN bus
bus = can.interface.Bus(channel='virtual', bustype='virtual')

# Define a class for virtual vehicles
class Vehicle:
    def __init__(self, x, y, color, direction, node_id):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, MAX_SPEED)
        self.direction = direction
        self.color = color
        self.node = node_id

    def move(self):
        self.x += self.speed * math.cos(self.direction)
        self.y += self.speed * math.sin(self.direction)
        
        # Wrap around the screen if the vehicle goes off-screen
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT
        elif self.y > SCREEN_HEIGHT:
            self.y = 0

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), VEHICLE_RADIUS)

    def send_message(self, message_id, data):
        msg = can.Message(arbitration_id=message_id, data=data, is_extended_id=False)
        bus.send(msg)
        print(f"Vehicle {self.node}: Sent message - ID: {message_id}, Data: {data}")

    def receive_message(self):
        msg = bus.recv(timeout=1)
        if msg is not None:
            print(f"Vehicle {self.node}: Received message - ID: {msg.arbitration_id}, Data: {msg.data}")


class Communication:
    def __init__(self) -> None:
        pass
        
    def broadcast_message(self, message):
        for vehicle in vehicles:
            if vehicle != self and math.sqrt((self.x - vehicle.x)**2 + (self.y - vehicle.y)**2) <= COMMUNICATION_RANGE:
                vehicle.receive_message(message)

    def receive_message(self, message):
        self.messages.append(message)

# Create virtual vehicles
# vehicles = [Vehicle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(NUM_VEHICLES)]
vehicle1 = Vehicle(random.randint(0,SCREEN_WIDTH),random.randint(0, SCREEN_HEIGHT), color = RED, direction=0, node_id = 1)
vehicle2 = Vehicle(random.randint(0,SCREEN_WIDTH),random.randint(0, SCREEN_HEIGHT), color = BLACK, direction=math.pi/2, node_id = 2)

vehicles = [vehicle1, vehicle2]



# Main loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill(WHITE)

    # Move and draw vehicles
    for vehicle in vehicles:
        vehicle.move()
        vehicle.draw()

    # Simulate message exchange between vehicles
    vehicle1.send_message(MESSAGE_ID_1, [0x01, 0x02, 0x03])
    vehicle2.send_message(MESSAGE_ID_2, [0x04, 0x05, 0x06])
    
    vehicle1.receive_message()
    vehicle2.receive_message()
    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()
bus.shutdown()