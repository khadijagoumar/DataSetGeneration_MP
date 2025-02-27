import cv2
import numpy as np
import re
import json
import math
import pytesseract

# Set the Tesseract executable path (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_surface_area(image):
    """
    Preprocess the image for OCR and extract the surface area.
    Expected formats: e.g., "100 m2", "100 sqm", or "100 m²".
    Returns the area in square centimeters.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    ocr_result = pytesseract.image_to_string(thresh)
    pattern = re.compile(r'(\d+(\.\d+)?)\s*(m2|sqm|m²|ni)', re.IGNORECASE)
    matches = pattern.findall(ocr_result)
    if matches:
        value_str, _, unit = matches[0]
        value = float(value_str)
        # Convert square meters to square centimeters
        real_area_cm2 = value * 10000
        return real_area_cm2
    else:
        print("No surface area found in OCR results.")
        return None

def resample_contour(contour, pixel_spacing):
    """
    Resamples points along a contour such that each point is approximately pixel_spacing apart.
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
        if dists[j+1] - dists[j] != 0:
            t = (d - dists[j]) / (dists[j+1] - dists[j])
        else:
            t = 0
        pt = (1 - t) * points[j] + t * points[j+1]
        new_points.append(pt)
    return np.array(new_points)

def apply_affine_transform(points, matrix):
    """
    Applies an affine transformation (using a 2x3 matrix) to an array of points.
    Points should be an array of shape (N, 2).
    """
    ones = np.ones((points.shape[0], 1), dtype=np.float32)
    points_aug = np.hstack([points, ones])
    transformed = np.dot(points_aug, matrix.T)
    return transformed

def convert_to_geojson_geo(points_geo):
    """
    Converts geographic coordinates (lon, lat) into a GeoJSON FeatureCollection.
    """
    features = []
    for pt in points_geo:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(pt[0]), float(pt[1])]  # [longitude, latitude]
            },
            "properties": {}
        }
        features.append(feature)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson

def main():
    # Load your architectural plan image
    image_path = "Plan1.jpeg"  # update with your actual image path
    image = cv2.imread(image_path)
    if image is None:
        print("Error loading image.")
        return

    # Step 1: Extract the surface area from the image via OCR
    real_area_cm2 = extract_surface_area(image)
    if real_area_cm2 is None:
        print("Surface area could not be determined from the image.")
        return
    print("Detected surface area (cm²):", real_area_cm2)
    
    # Step 2: Detect contours in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Invert threshold if needed based on your plan's background
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No contours found.")
        return

    # Step 3: Identify the building contour as the one with the largest area
    building_contour = max(contours, key=cv2.contourArea)
    pixel_area = cv2.contourArea(building_contour)
    print("Building pixel area:", pixel_area)
    
    # Step 4: Calculate the scale factor using the area.
    # Linear scale factor (cm per pixel) = sqrt(real_area_cm2 / pixel_area)
    scale_factor = math.sqrt(real_area_cm2 / pixel_area)
    print("Scale factor (cm per pixel):", scale_factor)
    
    # Step 5: Resample the building contour using a desired spacing of 2.5 cm in the real world.
    desired_spacing_cm = 2.5
    pixel_spacing = desired_spacing_cm / scale_factor
    sampled_points = resample_contour(building_contour, pixel_spacing)
    
    # Convert sampled points from pixel coordinates to local coordinates (in cm)
    local_points_cm = sampled_points * scale_factor

    # ---------------------------
    # Step 6: Apply an affine transformation to georeference the points.
    # Replace the following example ground control points (GCPs) with your actual data.
    #
    # Example:
    #  - gcp_local_pixels: Known pixel coordinates (e.g., corners in the image)
    #  - Multiply these by scale_factor to get local coordinates in cm.
    #  - gcp_geo: Their corresponding geographic coordinates (longitude, latitude) in EPSG:4326.
    #
    # Here we use three sample points.
    gcp_local_pixels = np.float32([
        [100, 200],
        [500, 200],
        [100, 600]
    ])
    gcp_local_cm = gcp_local_pixels * scale_factor  # convert to cm using our scale factor
    gcp_geo = np.float32([
        [2.2945, 48.8584],   # Replace with your actual geographic coordinates
        [2.2955, 48.8584],
        [2.2945, 48.8574]
    ])
    
    # Compute the affine transformation matrix from local (cm) to geographic coordinates.
    affine_matrix = cv2.getAffineTransform(gcp_local_cm, gcp_geo)
    print("Affine transformation matrix:\n", affine_matrix)
    
    # Transform the local building points (in cm) to geographic coordinates.
    geo_transformed_points = apply_affine_transform(local_points_cm.astype(np.float32), affine_matrix)
    
    # ---------------------------
    # Step 7: Convert the transformed geographic points to a GeoJSON file.
    geojson = convert_to_geojson_geo(geo_transformed_points)
    output_filename = "WallsTO_points_Plan2.geojson"
    with open(output_filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON file saved as '{output_filename}'.")

if __name__ == "__main__":
    main()
