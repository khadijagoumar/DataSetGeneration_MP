import cv2
import numpy as np
import json
from skimage.morphology import skeletonize

def extract_skeleton(image):
    """
    Extracts a single-line skeleton of thick walls.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # Skeletonize (ensure single-line representation of walls)
    skeleton = skeletonize(binary // 255)  # Convert to binary (0/1)
    skeleton = (skeleton * 255).astype(np.uint8)

    return skeleton

def get_main_contours(image):
    """
    Extracts ALL significant contours from the skeletonized image.
    """
    skeleton = extract_skeleton(image)
    
    # Find contours
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No contours found.")
        return []
    
    return contours  # Return all detected contours

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
    num_points = int(total_length // pixel_spacing)
    if num_points < 5:  # Ensure we keep a minimum number of points
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
    Applies an affine transformation to convert local coordinates to geographic coordinates.
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
    image_path = "Plan7.png"  # Update with your actual image path
    image = cv2.imread(image_path)
    if image is None:
        print("Error loading image.")
        return

    # Step 1: Extract all major contours
    building_contours = get_main_contours(image)
    if not building_contours:
        print("No valid contours found.")
        return

    print(f"Extracted {len(building_contours)} contours.")

    # Step 2: Resample each contour with uniform spacing
    all_sampled_points = []
    pixel_spacing = 5  # Reduce spacing for denser point cloud

    for contour in building_contours:
        sampled_points = resample_contour(contour, pixel_spacing)
        all_sampled_points.extend(sampled_points)

    all_sampled_points = np.array(all_sampled_points)

    print(f"Total sampled points: {len(all_sampled_points)}")

    if len(all_sampled_points) < 10:  # Safety check to ensure enough points
        print("Warning: Very few points detected, try adjusting parameters.")
        return

    # Step 3: Apply georeferencing transformation
    # Example: Define control points (modify with real coordinates)
    gcp_local_pixels = np.float32([[100, 200], [500, 200], [100, 600]])
    gcp_geo = np.float32([[2.2945, 48.8584], [2.2955, 48.8584], [2.2945, 48.8574]])

    # Compute affine transformation matrix
    affine_matrix = cv2.getAffineTransform(gcp_local_pixels, gcp_geo)
    geo_transformed_points = apply_affine_transform(all_sampled_points.astype(np.float32), affine_matrix)

    # Step 4: Convert to GeoJSON and save
    geojson = convert_to_geojson_geo(geo_transformed_points)
    output_filename = "Nosurface_Plan7.geojson"
    with open(output_filename, "w") as f:
        json.dump(geojson, f, indent=2)
    
    print(f"GeoJSON file saved as '{output_filename}' with {len(geo_transformed_points)} points.")

if __name__ == "__main__":
    main()
