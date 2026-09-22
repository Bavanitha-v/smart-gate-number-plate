# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
import os

def create_sample_video(filename="sample_traffic.mp4", duration_sec=15, fps=30):
    """
    Generate a high-quality simulated camera video with moving vehicles
    and distinct license plates for testing ANPR without a physical camera.
    """
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps

    # Test vehicles schedule: (frame_start, frame_end, plate_text, is_registered, car_color)
    vehicles = [
        (0, 220, "KA01AB1234", True, (40, 160, 220)),      # Blue SUV - Registered
        (225, 450, "UP14AB0001", False, (40, 40, 200)),    # Red Sedan - Unregistered
        (455, 675, "MH12DE5678", True, (180, 180, 40)),    # Yellow Car - Registered
    ]

    print(f"Generating sample video '{filename}' ({total_frames} frames)...")

    for f in range(total_frames):
        # Create background (Security Gate Checkpoint scene)
        frame = np.full((height, width, 3), (35, 42, 54), dtype=np.uint8)

        # Draw road layout
        cv2.rectangle(frame, (0, 360), (width, height), (60, 64, 72), -1)
        # Lane markings
        for x in range(0, width, 80):
            cv2.line(frame, (x, 540), (x + 40, 540), (255, 255, 255), 3)

        # Checkpoint booth & gate line
        cv2.rectangle(frame, (900, 200), (1150, 420), (80, 90, 110), -1)
        cv2.putText(frame, "SMART GATE CHECKPOINT", (910, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw Security Gate Barrier Arm
        gate_open = False
        # Determine active vehicle
        active_veh = None
        for v in vehicles:
            if v[0] <= f <= v[1]:
                active_veh = v
                break

        if active_veh:
            start_f, end_f, plate_text, is_reg, car_color = active_veh
            progress = (f - start_f) / (end_f - start_f)
            
            # Vehicle position moves from left to gate area and pauses
            if progress < 0.4:
                car_x = int(-350 + progress * (850 / 0.4))
            elif progress < 0.7:
                car_x = 500  # Stopped at gate for scanning
                if is_reg and progress > 0.5:
                    gate_open = True
            else:
                car_x = int(500 + (progress - 0.7) * (900 / 0.3))
                if is_reg:
                    gate_open = True

            car_y = 420

            # Draw Vehicle Body
            cv2.rectangle(frame, (car_x, car_y), (car_x + 320, car_y + 140), car_color, -1)
            cv2.rectangle(frame, (car_x + 40, car_y - 40), (car_x + 240, car_y), car_color, -1)
            # Windows
            cv2.rectangle(frame, (car_x + 60, car_y - 30), (car_x + 220, car_y - 5), (200, 230, 255), -1)
            # Wheels
            cv2.circle(frame, (car_x + 60, car_y + 140), 28, (20, 20, 20), -1)
            cv2.circle(frame, (car_x + 260, car_y + 140), 28, (20, 20, 20), -1)

            # Draw License Plate Box (High Contrast White Box with Black Text)
            plate_x = car_x + 240
            plate_y = car_y + 70
            cv2.rectangle(frame, (plate_x, plate_y), (plate_x + 130, plate_y + 40), (255, 255, 255), -1)
            cv2.rectangle(frame, (plate_x, plate_y), (plate_x + 130, plate_y + 40), (0, 0, 0), 2)
            cv2.putText(frame, plate_text, (plate_x + 6, plate_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Draw Gate Barrier
        gate_x = 850
        if gate_open:
            # Gate lifted up
            cv2.line(frame, (gate_x, 400), (gate_x, 200), (0, 255, 0), 12)
            cv2.putText(frame, "GATE OPEN", (gate_x - 40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            # Gate down horizontal
            cv2.line(frame, (gate_x, 480), (gate_x - 350, 480), (0, 0, 255), 12)
            cv2.putText(frame, "STOP / SCANNING", (gate_x - 280, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully at: {output_path}")
    return output_path

if __name__ == "__main__":
    create_sample_video()
