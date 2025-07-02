import argparse
import cv2
import pytesseract
import numpy as np
import glob

def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    w, h = gray.shape[1], gray.shape[0]
    _, thresh_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    return thresh_img

def extract_digits(img):
    output = cv2.connectedComponentsWithStats(img, 4, cv2.CV_32S)
    (numLabels, labels, stats, centroids) = output

    output = img.copy()
    connected_components = []
    numbers = []

    for i in range(1, numLabels):
        # extract the connected component statistics for the current
        # label
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]
        (cX, cY) = centroids[i]

        # filter out too small and too big connected components
        if area > 500 and area < output.shape[0] * output.shape[1] // 50 and w/h > 0.3 and w/h < 5:
            extent = area / (w * h)
            if extent > 0.1 and extent < 0.9:
                connected_components.append((x, y, w, h, cX, cY, i))
                cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.circle(output, (int(cX), int(cY)), 4, (0, 0, 255), -1)

    # Sort digits from left to right, then top to bottom
    connected_components.sort(key=lambda x: (x[0], x[1]))

    print(f"Found {len(connected_components)} connected components.")

    # Process components to group nearby ones
    i = 0
    while i < len(connected_components):
        current = connected_components[i]
        x1, y1, w1, h1, cX1, cY1, label1 = current
        combined = [current]
        
        # Look ahead to find nearby components
        j = i + 1
        while j < len(connected_components):
            next_comp = connected_components[j]
            x2, y2, w2, h2, cX2, cY2, label2 = next_comp
            distance = np.sqrt((x2 - (x1+w1)) ** 2 + (y2 - y1) ** 2)

            if distance < w1 * 3 and abs(cY2 - cY1) < h1 // 2:  # Adjust threshold as needed
                combined.append(next_comp)
                j += 1
            else:
                break
        
        if len(combined) > 1:
            # Calculate combined bounding box
            xs = [comp[0] for comp in combined]
            ys = [comp[1] for comp in combined]
            ws = [comp[2] for comp in combined]
            hs = [comp[3] for comp in combined]
            
            x = min(xs)
            y = min(ys)
            w = max(x + w for x, w in zip(xs, ws)) - x
            h = max(y + h for y, h in zip(ys, hs)) - y
            cX = x + w // 2
            cY = y + h // 2
            
            numbers.append((x, y, w, h, cX, cY, [comp[6] for comp in combined]))  # Include component labels
            i = j
        else:
            numbers.append((x1, y1, w1, h1, cX1, cY1, [label1]))
            i += 1

    return numbers, output

def recognize_number(image):
    numbers, output_img = extract_digits(image)
    recognized_numbers = []

    for number in numbers:
        x, y, w, h, cX, cY, labels = number
        roi = image[y:y + h, x:x + w]

        roi = cv2.copyMakeBorder(roi, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(0, 0, 0))  # Padding
        roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        roi = cv2.GaussianBlur(roi, (3, 3), 0)
        _, roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Perform OCR
        text = pytesseract.image_to_string(roi, config='--oem 3 --psm 8 outputbase digits')
        text = ''.join(filter(str.isdigit, text)).strip()  # Keep only digits

        if len(text) > 0 and len(text) < 4:  # Filter out empty or too long results
            recognized_numbers.append((text, (x, y, w, h, cX, cY, labels)))

            # Draw the bounding box and label on the output image
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.circle(output_img, (int(cX), int(cY)), 4, (0, 0, 255), -1)
            
            # Put the recognized text and component label(s)
            label_text = f"{text}"
            cv2.putText(output_img, label_text, (x, y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)

    return recognized_numbers, output_img

def get_numbers(image_path, show_output=False):
    img = cv2.imread(image_path)
    width_in_pixels = img.shape[1] if img is not None else 0

    if img is None:
        raise FileNotFoundError(f"The image file '{image_path}' was not found or could not be loaded.")
    processed = preprocess_image(img)
    numbers, output = recognize_number(processed)

    if show_output:
        #print(f"Recognized Number: {[number[1] for number in numbers]}")
        cv2.imshow("Output", output)  # Display the output with connected components
        cv2.waitKey(0)

    return numbers, width_in_pixels

    
def clean_numbers_orientations(numbers_orientations):
    # Keep only entries where digits are two digits long
    if numbers_orientations is None or not isinstance(numbers_orientations, dict) or len(numbers_orientations) == 0:
        return {}
    cleaned = {degree: (digits, offset) for degree, (digits, offset) in numbers_orientations.items() if len(str(digits)) == 2}

    # For each unique digits value, keep the entry with the smallest offset (closest to center)
    best_orientations = {}
    for degree, (digits, offset) in cleaned.items():
        if digits not in best_orientations or abs(offset) < abs(best_orientations[digits][1]):
            best_orientations[digits] = (degree, digits)

    # Build the final dict with degree as key
    final_orientations = {digits: degree for digits, (degree, digits) in best_orientations.items()}

    # Return sorted by degree
    return dict(sorted(final_orientations.items())) if final_orientations else {}

def identify_numbers_from_files(image_paths):
    try:
        FOV = 75

        numbers_orientations = {}  # Store orientations

        for image_path in image_paths:
            print(f"Processing image: {image_path}")
            numbers, width_in_pixels = (get_numbers(image_path))

            for number in numbers:
                x, y, w, h, cX, cY, labels = number[1]
                ground_truth = int(image_path.split('images/phase2/')[1].split('.')[0].split('_')[0])  # Extract ground truth from filename
                if ground_truth < 0 or ground_truth > 360:
                    print(f"Invalid ground truth value {ground_truth} in file {image_path}. Skipping this image.")
                    continue
                digits = int(number[0])
                offset = cX - (width_in_pixels / 2)
                degrees_per_pixel = FOV / width_in_pixels
                angular_offset = offset * degrees_per_pixel
                degree = (ground_truth + angular_offset) % 360  # Normalize to [0, 360)
                numbers_orientations[(round(degree))] = (digits, offset)

        print(f"Found {len(numbers_orientations)} orientations.")

        cleaned_numbers_orientations = clean_numbers_orientations(numbers_orientations)
        return cleaned_numbers_orientations
    except Exception as e:
        print(f"Error processing images: {e}")
        return {}
