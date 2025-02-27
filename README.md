# DataSetGeneration_MP

1-Detecting the surface (OCR) and then generate a geographically valid point cloud.
ImageToCP.py

This script processes an architectural plan image to extract building contours, scale them to real-world dimensions, georeference them, and export the data as a **GeoJSON point cloud**.

1. **Extract Surface Area**: Uses OCR to detect and convert the area from square meters to square centimeters.
2. **Detect Contours**: Identifies the **largest contour** as the building outline.
3. **Calculate Scale Factor**: Computes **cm per pixel** using real-world area vs. pixel area.
![image](https://github.com/user-attachments/assets/13ba4428-f93a-484b-b566-2d4ed3f6caa3)
