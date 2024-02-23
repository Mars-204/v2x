import struct
import random


# Define the structure of the CAN frame
# Each field has a fixed size and position within the frame
# Here, we use a simple example with 4 fields: Vehicle Speed, Engine Speed, Coolant Temperature, Fuel Level
# Adjust the sizes and positions based on your requirements
CAN_FRAME_FORMAT = '>HHHH'  # Fixed format for the CAN frame (2 bytes)

# Define the bit positions and sizes for each field within the frame
FIELD_POSITIONS = {
    "vehicle_speed": (0, 10),        # Start position: 0, Size: 10 bits
    "engine_speed": (10, 14),        # Start position: 10, Size: 14 bits
    "coolant_temp": (24, 8),  # Start position: 24, Size: 8 bits
    "fuel_level": (32, 8)            # Start position: 32, Size: 8 bits
}

# Function to generate random CAN data for vehicle parameters
def generate_data():
    # Generate random values for different vehicle parameters
    # Generate random values for vehicle parameters using random.uniform
    vehicle_speed = round(random.uniform(0, 1023))  # 10-bit field
    engine_speed = round(random.uniform(0, 16383))  # 14-bit field
    coolant_temp =round(random.uniform(0, 255 * (2 ** 8)))  # 8-bit field
    fuel_level = round(random.uniform(0, 255 * (2 ** 8)))   # 8-bit field

    # Encode the vehicle parameters into a CAN frame
    can_frame = encode_can_frame(vehicle_speed, engine_speed, coolant_temp, fuel_level)
    return can_frame

# Function to encode vehicle parameters into a CAN frame
def encode_can_frame(vehicle_speed, engine_speed, coolant_temp, fuel_level):
    can_data_values = []

    # Encode each field into the CAN frame
    for field, (start, size) in FIELD_POSITIONS.items():
        value = locals()[field.replace(" ", "_")]  # Get the value of the corresponding variable
        value &= (1 << size) - 1  # Mask to ensure the value fits within the specified size
        can_data_values.append(value)  # Add the value to the list

    # Pack the CAN frame into bytes
    return struct.pack(CAN_FRAME_FORMAT, *can_data_values)

# Function to decode a CAN frame into vehicle parameters
def decode_can_frame(can_frame):
    can_data = struct.unpack(CAN_FRAME_FORMAT, can_frame)[0]

    # Decode each field from the CAN frame
    vehicle_parameters = {}
    for field, (start, size) in FIELD_POSITIONS.items():
        mask = (1 << size) - 1  # Mask to extract the value from the frame
        value = (can_data >> start) & mask  # Shift and mask to get the value
        vehicle_parameters[field] = value

    return vehicle_parameters

# # Example usage:
# if __name__ == "__main__":
#     # Generate random values for vehicle parameters
#     can_frame = generate_data()
#     print("Encoded CAN frame:", can_frame.hex())

#     dec = decode_can_frame(can_frame)
#     print('Decode can frame:',dec)
