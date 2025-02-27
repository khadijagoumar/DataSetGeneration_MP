import cv2
import numpy as np
import re
import json
import math
import pytesseract
from skimage.morphology import skeletonize, thin

# Set Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_for_ocr(image):
    """
    Preprocess the image to enhance text detection.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Morphological operations to remove small noise
    kernel = np.ones((3,3), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return processed

def extract_surface_area(image):
    """
    Extracts the surface area using OCR after preprocessing.
    """
    preprocessed = preprocess_for_ocr(image)
    ocr_result = pytesseract.image_to_string(preprocessed, config='--psm 6')
    
    pattern = re.compile(r'(\d+(\.\d+)?)\s*(m2|sqm|m²|ni)', re.IGNORECASE)
    matches = pattern.findall(ocr_result)
    
    if matches:
        value_str, _, unit = matches[0]
        value = float(value_str)
        real_area_cm2 = value * 10000  # Convert m² to cm²
        return real_area_cm2
    else:
        print("No surface area found in OCR results.")
        return None

def extract_skeleton(image):
    """
    Extracts a single-line skeleton of thick walls.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Use morphological thinning to reduce wall thickness to a single line
    skeleton = skeletonize(binary // 255)  # Skeletonize expects binary (0/1)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    return skeleton

def get_main_contour(image):
    """
    Extracts the largest contour after skeletonization.
    """
    skeleton = extract_skeleton(image)
    
    # Find contours
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No contours found.")
        return None
    
    # Get the largest contour (assumed to be the building)
    main_contour = max(contours, key=cv2.contourArea)
    return main_contour

def resample_contour(contour, pixel_spacing):
    """
    Resamples points along the contour to have uniform spacing.
    """
    points = contour.reshape(-1, 2)
    dists = [0.0]
    
    for i in range(1, len(points)):
        d = np.linalg.norm(points[i] - points[i - 1])
        dists.append(dists[-1] + d)
    
    total_length = dists[-1]
    num_points = int(total_length // pixel_spacing)
    if num_points < 2:
        return points

    new_points = []
    sample_dists = np.linspace(0, total_length, num_points, endpoint=False)
    j = 0
    for d in sample_dists:
        while j < len(dists) - 1 and d > dists[j+1]:
            j += 1
        t = (d - dists[j]) / (dists[j+1] - dists[j]) if (dists[j+1] - dists[j]) != 0 else 0
        pt = (1 - t) * points[j] + t * points[j+1]
        new_points.append(pt)
    
    return np.array(new_points)

def apply_affine_transform(points, matrix):
    """
    Applies an affine transformation to points.
    """
    ones = np.ones((points.shape[0], 1), dtype=np.float32)
    points_aug = np.hstack([points, ones])
    transformed = np.dot(points_aug, matrix.T)
    return transformed

def convert_to_geojson_geo(points_geo):
    """
    Converts geographic coordinates into a GeoJSON FeatureCollection.
    """
    features = [{"type": "Feature",
                 "geometry": {"type": "Point",
                              "coordinates": [float(pt[0]), float(pt[1])]},
                 "properties": {}} for pt in points_geo]
    return {"type": "FeatureCollection", "features": features}

def main():
    image_path = "Plan22.png"  # Update with your actual image path
    image = cv2.imread(image_path)
    if image is None:
        print("Error loading image.")
        return

    # Step 1: Extract surface area using OCR
    real_area_cm2 = extract_surface_area(image)
    if real_area_cm2 is None:
        print("Surface area could not be determined from the image.")
        return
    print("Detected surface area (cm²):", real_area_cm2)

    # Step 2: Extract single-line skeleton contour
    building_contour = get_main_contour(image)
    if building_contour is None:
        return

    pixel_area = cv2.contourArea(building_contour)
    print("Building pixel area:", pixel_area)

    # Step 3: Calculate scale factor (cm per pixel)
    scale_factor = math.sqrt(real_area_cm2 / pixel_area)
    print("Scale factor (cm per pixel):", scale_factor)

    # Step 4: Resample contour with uniform spacing of 2.5 cm
    desired_spacing_cm = 2.5
    pixel_spacing = desired_spacing_cm / scale_factor
    sampled_points = resample_contour(building_contour, pixel_spacing)

    # Convert sampled points to local coordinates (cm)
    local_points_cm = sampled_points * scale_factor

    # Step 5: Apply georeferencing transformation
    gcp_local_pixels = np.float32([[100, 200], [500, 200], [100, 600]])
    gcp_local_cm = gcp_local_pixels * scale_factor
    gcp_geo = np.float32([[2.2945, 48.8584], [2.2955, 48.8584], [2.2945, 48.8574]])

    affine_matrix = cv2.getAffineTransform(gcp_local_cm, gcp_geo)
    geo_transformed_points = apply_affine_transform(local_points_cm.astype(np.float32), affine_matrix)

    # Step 6: Convert to GeoJSON and save
    geojson = convert_to_geojson_geo(geo_transformed_points)
    output_filename = "Walls_points_Plan22.geojson"
    with open(output_filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON file saved as '{output_filename}'.")

if __name__ == "__main__":
    main()
