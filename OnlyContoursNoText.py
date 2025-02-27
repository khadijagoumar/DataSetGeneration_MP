import cv2
import numpy as np
import json
from skimage.morphology import skeletonize
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def detect_text_regions(image):
    """
    Detects text regions in the image using Tesseract OCR.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Detect text using pytesseract
    d = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    text_boxes = []
    for i in range(len(d['text'])):
        if d['text'][i].strip() != "":
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            text_boxes.append((x, y, x + w, y + h))
    return text_boxes


def remove_text(image, text_boxes):
    """
    Removes detected text using inpainting.
    """
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    for (x1, y1, x2, y2) in text_boxes:
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)
    
    inpainted_image = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    return inpainted_image


def extract_skeleton(image):
    """
    Extracts a single-line skeleton of thick walls.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    skeleton = skeletonize(binary // 255)
    return (skeleton * 255).astype(np.uint8)


def get_all_contours(image):
    """
    Extracts all significant contours (outer & inner walls).
    """
    skeleton = extract_skeleton(image)
    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours if contours else []


def resample_contour(contour, pixel_spacing=5):
    """
    Resamples points along the contour to have uniform spacing.
    """
    points = contour.reshape(-1, 2)
    dists = [0.0]
    for i in range(1, len(points)):
        d = np.linalg.norm(points[i] - points[i - 1])
        dists.append(dists[-1] + d)
    total_length = dists[-1]
    num_points = max(int(total_length // pixel_spacing), 5)
    sample_dists = np.linspace(0, total_length, num_points, endpoint=False)
    j, new_points = 0, []
    for d in sample_dists:
        while j < len(dists) - 1 and d > dists[j+1]:
            j += 1
        t = (d - dists[j]) / (dists[j+1] - dists[j]) if (dists[j+1] - dists[j]) != 0 else 0
        pt = (1 - t) * points[j] + t * points[j+1]
        new_points.append(pt)
    return np.array(new_points)


def apply_affine_transform(points, matrix):
    """
    Applies an affine transformation to convert local coordinates to geographic coordinates.
    """
    ones = np.ones((points.shape[0], 1), dtype=np.float32)
    transformed = np.dot(np.hstack([points, ones]), matrix.T)
    return transformed


def convert_to_geojson_geo(points_geo):
    """
    Converts geographic coordinates into a GeoJSON FeatureCollection.
    """
    features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(pt[0]), float(pt[1])]}, "properties": {}} for pt in points_geo]
    return {"type": "FeatureCollection", "features": features}


def main(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Error loading image.")
        return

    # Step 1: Detect and remove text
    text_boxes = detect_text_regions(image)
    clean_image = remove_text(image, text_boxes)
    
    # Step 2: Extract all contours (inner + outer walls)
    building_contours = get_all_contours(clean_image)
    if not building_contours:
        print("No valid contours found.")
        return

    print(f"Extracted {len(building_contours)} contours.")
    
    # Step 3: Resample each contour with uniform spacing
    all_sampled_points = np.array([pt for contour in building_contours for pt in resample_contour(contour, pixel_spacing=5)])
    
    if len(all_sampled_points) < 10:
        print("Warning: Very few points detected, try adjusting parameters.")
        return

    # Step 4: Apply georeferencing transformation
    gcp_local_pixels = np.float32([[100, 200], [500, 200], [100, 600]])
    gcp_geo = np.float32([[2.2945, 48.8584], [2.2955, 48.8584], [2.2945, 48.8574]])
    affine_matrix = cv2.getAffineTransform(gcp_local_pixels, gcp_geo)
    geo_transformed_points = apply_affine_transform(all_sampled_points.astype(np.float32), affine_matrix)

    # Step 5: Convert to GeoJSON and save
    geojson = convert_to_geojson_geo(geo_transformed_points)
    output_filename = "Processed_Plan.geojson"
    with open(output_filename, "w") as f:
        json.dump(geojson, f, indent=2)
    
    print(f"GeoJSON file saved as '{output_filename}' with {len(geo_transformed_points)} points.")


# Run the script
image_path = "Plan1.jpeg"
main(image_path)
