import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Get actual screen resolution
screen_width, screen_height = pyautogui.size()

# Initialize camera
cap = cv2.VideoCapture(0)

# Disable pyautogui failsafe (so mouse doesn't get stuck in corners)
pyautogui.FAILSAFE = False

# Variables for smoothing the mouse movement
smoothening = 5
plocX, plocY = 0, 0 # Previous locations
clocX, clocY = 0, 0 # Current locations

# Area inside the camera that will map to the full screen
frameR = 100 

# Click state to prevent spamming clicks
is_clicking = False

# Setup the window to be always on top
window_name = "Virtual Gesture Mouse"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

print("Starting Virtual Mouse... Press 'q' in the video window to quit.")

while True:
    success, img = cap.read()
    if not success:
        print("Failed to grab camera frame")
        break

    # Flip the image horizontally so it acts like a mirror
    img = cv2.flip(img, 1)
    h, w, c = img.shape

    # Draw the active tracking area box
    cv2.rectangle(img, (frameR, frameR), (w - frameR, h - frameR), (255, 0, 255), 2)

    # Convert BGR to RGB for MediaPipe
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get coordinates for Index Finger Tip (8) and Thumb Tip (4)
            index_finger = hand_landmarks.landmark[8]
            thumb = hand_landmarks.landmark[4]

            # Convert to pixel coordinates
            ix, iy = int(index_finger.x * w), int(index_finger.y * h)
            tx, ty = int(thumb.x * w), int(thumb.y * h)

            # 1. Move the Mouse
            # Map the index finger position (within the inner box) to the full screen resolution
            screen_x = np.interp(ix, (frameR, w - frameR), (0, screen_width))
            screen_y = np.interp(iy, (frameR, h - frameR), (0, screen_height))
            
            # Smooth the movement
            clocX = plocX + (screen_x - plocX) / smoothening
            clocY = plocY + (screen_y - plocY) / smoothening
            
            try:
                pyautogui.moveTo(clocX, clocY)
                plocX, plocY = clocX, clocY
            except Exception as e:
                pass # Ignore if it tries to go slightly out of bounds

            # 2. Handle Clicks
            # Calculate distance between thumb and index finger
            distance = math.hypot(tx - ix, ty - iy)
            
            # If they pinch (distance is small), it's a click
            if distance < 40:
                cv2.circle(img, (ix, iy), 15, (0, 255, 0), cv2.FILLED) # Draw green circle on pinch
                if not is_clicking:
                    pyautogui.click()
                    is_clicking = True
            else:
                is_clicking = False

    # Resize the image to make it a small pop-up (about 20% of screen height)
    display_height = int(screen_height * 0.2)
    display_width = int((display_height / h) * w)
    img_resized = cv2.resize(img, (display_width, display_height))

    # Show the video pop-up
    cv2.imshow(window_name, img_resized)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
