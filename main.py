import pygame
import math
import random
import can
import threading
import time
import socket
from server import start_server
from generate_vehicle_data import generate_data, decode_can_frame

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

try:
    # Create virtual CAN bus
    bus_send = can.interface.Bus('test', bustype='virtual')
    bus_recv = can.interface.Bus('test', bustype='virtual')
    print("Virtual CAN bus initialized successfully.")
except Exception as e:
    print("Error initializing virtual CAN bus:", e)


# Load a font
font = pygame.font.Font(None, 24)  # None means default font, 24 is the size

# Define a class for virtual vehicles
class Vehicle:
    def __init__(self, x, y, color, direction, node_id):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, MAX_SPEED)
        self.direction = direction
        self.color = color
        self.node = node_id
        self.sent_messages = []
        self.received_messages = []

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

        # Display sent messages
        for i, (message_id, data) in enumerate(self.sent_messages):
            message_text = f"Sent: ID={message_id}, Data={data}"
            text_surface = font.render(message_text, True, self.color)
            screen.blit(text_surface, (10, 10 + i * 20))

        # Display received messages
        for i, (message_id, data) in enumerate(self.received_messages):
            message_text = f"Received: ID={message_id}, Data={data}"
            text_surface = font.render(message_text, True, self.color)
            screen.blit(text_surface, (10, 100 + i * 20))
    

    def connect_to_server(self):
        # Connect to the server
        server_host = "127.0.0.1"  # Change this to the IP address of your server
        server_port = 8888

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))
        return client_socket




vehicles = [
    Vehicle(random.randint(0,SCREEN_WIDTH),random.randint(0, SCREEN_HEIGHT), color = RED, direction=0, node_id = 1),
    Vehicle(random.randint(0,SCREEN_WIDTH),random.randint(0, SCREEN_HEIGHT), color = BLACK, direction=math.pi/2, node_id = 2)]

def receive_messages(vehicle, vehicle_socket):
    while True:
        msg = bus_recv.recv()
        if msg is not None:
            print(f"Vehicle {vehicle.node}: Received message - ID: {msg.arbitration_id}, Data: {msg.data}")
            response = vehicle_socket.recv(1024)
            print("Server response:", decode_can_frame(response))
        time.sleep(1)

def send_messages(vehicle, vehicle_socket):
    while True:
        # Define your message IDs and data here
        message_id = vehicle.node * 0x100
        # data = bytearray([0x01, 0x02, 0x03])  # Example data as bytes
        data = generate_data()
        # Create CAN message and send it
        msg = can.Message(arbitration_id=message_id, data=data)
        bus_send.send(msg)

        # Send data over the socket
        vehicle_socket.send(data)

        print(f"Vehicle {vehicle.node}: Sent message - ID: {message_id}, Data: {data}")

        # Adjust the sleep interval as needed
        time.sleep(1)

# Main loop
sockets = []

# Start a separate thread to start the server
threading.Thread(target=start_server).start()

for vehicle in vehicles:
    # Establish socket connection for each vehicle
    vehicle_socket = vehicle.connect_to_server()
    sockets.append(vehicle_socket)


    # Start a separate thread for message reception for each vehicle
    threading.Thread(target=receive_messages, args=(vehicle, vehicle_socket), daemon=True).start()

    # Start a separate thread for sending messages for each vehicle
    threading.Thread(target=send_messages, args=(vehicle, vehicle_socket), daemon=True).start()




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
    
    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()
bus_send.shutdown()
bus_recv.shutdown()