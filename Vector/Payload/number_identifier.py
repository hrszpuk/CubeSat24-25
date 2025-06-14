import argparse
import cv2
import pytesseract
import numpy as np

def preprocess_image(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    return thresh_img

def extract_digits(img):
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    # ap.add_argument("-i", "--image", required=True,
    #     help="path to input image")
    ap.add_argument("-c", "--connectivity", type=int, default=4,
        help="connectivity for connected component analysis")
    args = vars(ap.parse_args())

    output = cv2.connectedComponentsWithStats(img, args["connectivity"], cv2.CV_32S)
    (numLabels, labels, stats, centroids) = output

    output = img.copy()
    output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)

    connected_components = []
    digit_images = []

    for i in range(1, numLabels):
        # extract the connected component statistics for the current
        # label
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]
        (cX, cY) = centroids[i]

        # filter out small connected components
        #if area > 100 and area < 1000:
        if area > 500:
            connected_components.append((x, y, w, h, cX, cY))
            # # draw the connected component on the output image
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.circle(output, (int(cX), int(cY)), 4, (0, 0, 255), -1)

    for component in connected_components:
        x, y, w, h = component[:4]
        digit = img[y:y+h, x:x+w]
        digit_images.append((x, digit))
    
    # Sort digits from left to right
    digit_images.sort(key=lambda x: x[0])

    # cv2.imshow("Connected Components", output)
    # cv2.waitKey(0)

    return [digit[1] for digit in digit_images], output

def recognize_number(image):
    numbers = []
    digits, output = extract_digits(image)
    recognised_digits = []
    for digit in digits:
        #digit = cv2.resize(digit, (28, 28))  # Resize to standard size
        digit = cv2.copyMakeBorder(digit, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(0, 0, 0))  # Padding
        text = pytesseract.image_to_string(digit, config='--psm 8 outputbase digits')
        text = ''.join(filter(str.isdigit, text))  # Keep only digits 0-9
        numbers.append(text.strip())
        if text.strip() != '':
            cX, cY = cv2.moments(digit)['m10'], cv2.moments(digit)['m01']
            recognised_digits.append((cX, cY))
    
    if len(recognised_digits) >2:
        # Calculate distances between centroids and filter out distant digits using standard deviation
        distances = []
        for i, (cX1, cY1) in enumerate(recognised_digits):
            for j, (cX2, cY2) in enumerate(recognised_digits):
                if i != j:
                    distance = np.sqrt((cX2 - cX1) ** 2 + (cY2 - cY1) ** 2)
                    distances.append(distance)

        if distances:
            mean_distance = np.mean(distances)
            std_distance = np.std(distances)
            threshold = mean_distance + std_distance  # Filter out distances greater than mean + std deviation

            filtered_digits = []
            for i, (cX1, cY1) in enumerate(recognised_digits):
                for j, (cX2, cY2) in enumerate(recognised_digits):
                    if i != j:
                        distance = np.sqrt((cX2 - cX1) ** 2 + (cY2 - cY1) ** 2)
                        if distance <= threshold:
                            filtered_digits.append(numbers[i])
                            break

            numbers = filtered_digits

    return "".join(numbers), output
 
# img = cv2.imread("test_real.jpg")
# if img is None:
#     raise FileNotFoundError("The image file 'test_image.png' was not found or could not be loaded.")
# processed = preprocess_image(img)
# number, output = recognize_number(processed)

# print(f"Recognized Number: {number}")
# cv2.imshow("Processed Image", processed)
# cv2.imshow("Output", output)  # Display the output with connected components
# cv2.waitKey(0)

cap = cv2.VideoCapture(0)  # Open webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    processed = preprocess_image(frame)
    number, output = recognize_number(processed)
    
    cv2.putText(frame, f"Detected: {number}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Frame", frame)
    cv2.imshow("Processed", output)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
