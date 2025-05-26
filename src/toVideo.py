import cv2
import os
import natsort # For natural sorting of filenames

# --- Configuration ---
image_folder = 'frames'  # E.g., 'frames' or 'C:/Users/YourName/Desktop/MyFrames'
video_name = 'output_video.mp4'
fps = 24  # Frames per second
image_extension = '.jpg' # Change if your images are .jpg, .jpeg, etc.
# --- End Configuration ---

# Get all image file names from the folder
images = [img for img in os.listdir(image_folder) if img.endswith(image_extension)]

# Sort the images by name in natural order (e.g., frame1, frame2, ..., frame10)
# This is important if your filenames aren't zero-padded (e.g., 1.png, 2.png, ..., 10.png)
# If they are already correctly named like frame001.png, frame002.png, simple sort() might also work.
images = natsort.natsorted(images)

if not images:
    print(f"No images found in '{image_folder}' with extension '{image_extension}'. Please check the path and extension.")
    exit()

# Read the first image to get the frame dimensions
first_image_path = os.path.join(image_folder, images[0])
frame = cv2.imread(first_image_path)
if frame is None:
    print(f"Error reading the first image: {first_image_path}. Check the file.")
    exit()
height, width, layers = frame.shape

# Define the codec and create VideoWriter object
# For MP4, 'mp4v' or 'XVID' are common. 'XVID' is generally more compatible.
# You might need to install codecs separately on your system if it fails.
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Or use 'XVID', 'MJPG', etc.
video = cv2.VideoWriter(video_name, fourcc, float(fps), (width, height))

if not video.isOpened():
    print(f"Error: Could not open video writer. Check the video_name, fourcc, fps, or frame dimensions.")
    exit()

print(f"Starting video creation: {video_name} ({width}x{height} @ {fps}fps)")

# Loop through all images and write them to the video
for i, image_name in enumerate(images):
    image_path = os.path.join(image_folder, image_name)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Warning: Skipping image {image_path}, could not read.")
        continue
    video.write(img)
    # Optional: Print progress
    print(f"Processing frame {i+1}/{len(images)}: {image_name}")


# Release the video writer object
video.release()
cv2.destroyAllWindows() # Not strictly necessary for this script but good practice

print(f"Video '{video_name}' created successfully in the script's directory!")