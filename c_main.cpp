#include <SFML/Graphics.hpp>
#include <cmath>
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <unistd.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/socket.h>
#include <string.h>
#include <stdexcept>

// CAN bus interface
class CanBus {
private:
    int sock;
    struct sockaddr_can addr;
    struct ifreq ifr;

public:
    CanBus(const std::string& interface) {
        if ((sock = socket(PF_CAN, SOCK_RAW, CAN_RAW)) < 0) {
            throw std::runtime_error("Error opening socket");
        }

        std::strcpy(ifr.ifr_name, interface.c_str());
        ioctl(sock, SIOCGIFINDEX, &ifr);

        addr.can_family = AF_CAN;
        addr.can_ifindex = ifr.ifr_ifindex;

        if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
            throw std::runtime_error("Error binding socket to interface");
        }
    }

    ~CanBus() {
        close(sock);
    }

    void send(const can_frame& frame) {
        write(sock, &frame, sizeof(struct can_frame));
    }

    can_frame recv() {
        can_frame frame;
        read(sock, &frame, sizeof(struct can_frame));
        return frame;
    }
};

// Virtual vehicle
class Vehicle {
private:
    float x, y;
    float speed;
    float direction;
    sf::Color color;
    int node;
    std::vector<std::pair<int, std::vector<uint8_t>>> sent_messages;
    std::vector<std::pair<int, std::vector<uint8_t>>> received_messages;
    std::mutex mtx;

public:
    Vehicle(float x, float y, sf::Color color, float direction, int node)
        : x(x), y(y), color(color), direction(direction), node(node) {
        speed = static_cast<float>(rand()) / RAND_MAX * 5.0f + 1.0f;
    }

    void move() {
        x += speed * std::cos(direction);
        y += speed * std::sin(direction);

        if (x < 0) x = 800;
        else if (x > 800) x = 0;
        if (y < 0) y = 600;
        else if (y > 600) y = 0;
    }

    void draw(sf::RenderWindow& window) {
        sf::CircleShape circle(20);
        circle.setFillColor(color);
        circle.setPosition(x, y);
        window.draw(circle);

        int i = 0;
        for (const auto& message : sent_messages) {
            std::string text = "Sent: ID=" + std::to_string(message.first) + ", Data=";
            for (uint8_t byte : message.second) {
                text += std::to_string(byte) + " ";
            }
            sf::Text message_text(text, font, 24);
            message_text.setPosition(10, 10 + i * 20);
            message_text.setFillColor(color);
            window.draw(message_text);
            i++;
        }

        i = 0;
        for (const auto& message : received_messages) {
            std::string text = "Received: ID=" + std::to_string(message.first) + ", Data=";
            for (uint8_t byte : message.second) {
                text += std::to_string(byte) + " ";
            }
            sf::Text message_text(text, font, 24);
            message_text.setPosition(10, 100 + i * 20);
            message_text.setFillColor(color);
            window.draw(message_text);
            i++;
        }
    }

    void send_message(int message_id, const std::vector<uint8_t>& data, CanBus& bus) {
        can_frame frame;
        frame.can_id = message_id;
        frame.can_dlc = data.size();
        std::copy(data.begin(), data.end(), frame.data);
        bus.send(frame);

        std::lock_guard<std::mutex> lock(mtx);
        sent_messages.emplace_back(message_id, data);
    }

    void receive_message(const can_frame& frame) {
        std::lock_guard<std::mutex> lock(mtx);
        received_messages.emplace_back(frame.can_id, std::vector<uint8_t>(frame.data, frame.data + frame.can_dlc));
    }

    void clear_messages() {
        std::lock_guard<std::mutex> lock(mtx);
        sent_messages.clear();
        received_messages.clear();
    }
};

int main() {
    sf::RenderWindow window(sf::VideoMode(800, 600), "V2X Communication Simulation");

    sf::Font font;
    if (!font.loadFromFile("arial.ttf")) {
        std::cerr << "Failed to load font file" << std::endl;
        return 1;
    }

    CanBus bus("vcan0");

    std::vector<Vehicle> vehicles;
    vehicles.emplace_back(200, 300, sf::Color::Red, 0, 1);
    vehicles.emplace_back(600, 300, sf::Color::Black, M_PI / 2, 2);

    std::thread receiver_thread([&]() {
        while (true) {
            can_frame frame = bus.recv();
            for (auto& vehicle : vehicles) {
                if (vehicle.node == frame.can_id / 0x100) {
                    vehicle.receive_message(frame);
                    break;
                }
            }
        }
    });

    std::thread sender_thread([&]() {
        while (true) {
            for (auto& vehicle : vehicles) {
                vehicle.send_message(vehicle.node * 0x100, {0x01, 0x02, 0x03}, bus);
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        }
    });

    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }
        }

        window.clear(sf::Color::White);

        for (auto& vehicle : vehicles) {
            vehicle.move();
            vehicle.draw(window);
            vehicle.clear_messages();
        }

        window.display();
        sf::sleep(sf::milliseconds(16));
    }

    receiver_thread.join();
    sender_thread.join();

    return 0;
}
