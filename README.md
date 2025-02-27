# DataSetGeneration_MP

**1-Detecting the surface (OCR) and then generate a geographically valid point cloud.**
**ImageToCP.py**

This script processes an architectural plan image to extract building contours, scale them to real-world dimensions, georeference them, and export the data as a **GeoJSON point cloud**.

1. **Extract Surface Area**: Uses OCR to detect and convert the area from square meters to square centimeters.
2. **Detect Contours**: Identifies the **largest contour** as the building outline.
3. **Calculate Scale Factor**: Computes **cm per pixel** using real-world area vs. pixel area.
   
![image](https://github.com/user-attachments/assets/13ba4428-f93a-484b-b566-2d4ed3f6caa3)

4. **Resample Contour**: Generates points spaced **2.5 cm apart** in real-world dimensions.
5. **Georeference**: Uses an **Affine Transformation** with known ground control points (GCPs).
6. **Export to GeoJSON**: Saves the georeferenced **point cloud** for GIS applications.

**WEAKNESSES**:
it generates the contour of the walls doubled (thick contour)
the generated points of a window are tripeled (we describe the windows three thin lines )


![image](https://github.com/user-attachments/assets/1576be2f-77c6-4a59-b501-1dd0f8288c00)
![image](https://github.com/user-attachments/assets/b197954a-b202-46b4-9c8b-c4a1d65de72f)

**2-Generation of a cloud point file via an image with no surface detection, contours only**
**ImageToPC_2.py**
This script processes an architectural plan image to **extract skeletonized walls**, **detect contours**, **resample points**, **georeference them**, and **export the result as a GeoJSON point cloud**.

1. **Extract Skeletonized Walls**:
    - Converts the image to grayscale and applies **thresholding**.
    - Uses **skeletonization** to reduce thick walls to single-line representations.
2. **Detect Contours**:
    - Extracts all significant **wall contours** from the skeletonized image.
3. **Resample Contours**:
    - Uniformly spaces points along each detected contour (**5-pixel spacing**) to create a **denser point cloud**.
4. **Georeference the Points**:
    - Uses an **Affine Transformation** with three **ground control points (GCPs)** to convert **image pixel coordinates** into **real-world geographic coordinates**.
5. **Export to GeoJSON**:
    - Converts the georeferenced points into a **GeoJSON file** (`Nosurface_Plan7.geojson`), making it usable in GIS applications.

⇒It doesnt use the 2.5 spacing cus it has no reference about the surface or the length of the walls (which makes so much sense to me tbh)

![image](https://github.com/user-attachments/assets/78fa5912-4b66-4067-a76b-be59aeb8a8e8)

=> Another plan:
![image](https://github.com/user-attachments/assets/bfb7e7ca-7b4e-4155-9dac-f45cd5296e45)
![image](https://github.com/user-attachments/assets/4afab1b5-b3ba-4905-8a0e-3234bd5311af)

=> ps: somehow this script only detects the outer contours of some plans which is obviously not practical.

**3-Detecting the text (OCR), paints the text with the contours colors (removing the texts) and then generating the geojson file detecting contours (geographic coordinates)**
**OnlyContoursNoText.py**
This script processes an architectural plan image by:

1. **Text Handling**:
    - Uses Tesseract OCR to detect text regions.
    - Removes the detected text via inpainting.
2. **Contour Extraction**:
    - Converts the image to binary and applies skeletonization to thin wall lines.
    - Finds contours representing inner and outer walls.
3. **Contour Processing**:
    - Resamples each contour to obtain uniformly spaced points.
4. **Georeferencing**:
    - Applies an affine transformation using predefined ground control points to convert pixel coordinates to geographic coordinates.
5. **GeoJSON Output**:
    - Converts the transformed points into a GeoJSON FeatureCollection and saves it to a file.

![image](https://github.com/user-attachments/assets/a1336d69-fd3d-4124-bce1-83d6899089d2)
![image](https://github.com/user-attachments/assets/1fd66596-253c-45f2-bf58-0a639a16a8e2)

**4- Automated Extraction, Resampling, and Georeferencing of Building Plan Contours**
**ImageToCP_ALLCONTOURS.py**
This script processes a plan image by:

- **Skeleton Extraction**:
    It converts the image to grayscale, applies a binary threshold, and uses skeletonization to reduce thick walls to one-pixel-wide lines.
- **Contour Detection**:
    It finds all contours (including both outer and inner walls) from the skeletonized image.
- **Resampling**:
    Each contour is resampled to generate uniformly spaced points along its length.
- **Georeferencing**:
    The sampled points are transformed from local pixel coordinates to geographic coordinates using an affine transformation based on predefined control points.
- **GeoJSON Output**:
    Finally, the geographic coordinates are converted into a GeoJSON FeatureCollection and saved to a file.

![image](https://github.com/user-attachments/assets/305a5264-5d6b-47ea-8e9f-bb99f506191e)
![image](https://github.com/user-attachments/assets/c55ec9c6-25cb-4947-ae97-fe8d82c71302)





