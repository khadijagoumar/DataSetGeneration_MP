import json
import matplotlib.pyplot as plt

def load_geojson(file_path):
    """Load GeoJSON or JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def plot_feature(feature, ax):
    """Plot individual GeoJSON features."""
    geometry = feature.get("geometry", {})
    geom_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    if geom_type == "Point":
        x, y = coordinates
        ax.scatter(x, y, color='red', label="Point")

    elif geom_type == "LineString":
        x, y = zip(*coordinates)
        ax.plot(x, y, color='blue', label="LineString")

    elif geom_type == "Polygon":
        for polygon in coordinates:  # Handles multiple rings
            x, y = zip(*polygon)
            ax.fill(x, y, alpha=0.5, edgecolor='black', label="Polygon")

def plot_geojson(file_path):
    """Main function to read and plot a GeoJSON file."""
    data = load_geojson(file_path)

    fig, ax = plt.subplots(figsize=(5, 5))  # Smaller window size
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("GeoJSON Visualization")

    # Check if it's a FeatureCollection
    if "features" in data:
        for feature in data["features"]:
            plot_feature(feature, ax)
    else:
        print("Invalid GeoJSON format!")

    plt.legend()
    plt.show()

# Example Usage
file_path = "WallsTO_points_Plan2.geojson"  # Change this to your file
plot_geojson(file_path)
