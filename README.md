Duplicate Image Finder
A Python application that scans a folder and its subdirectories to detect and group duplicate images using dHash and Annoy.
Folder Structure
duplicate_image_finder/
├── duplicate_image_finder.py  # Main application code
├── requirements.txt           # Dependencies
└── README.md                 # Project documentation

Installation

Clone the repository or copy the files to your local machine.
Install Python 3.8 or higher.
Install dependencies:

pip install -r requirements.txt

Usage

Run the application:

python duplicate_image_finder.py


Click "Select Folder" to choose a directory containing images.
Click "Scan for Duplicates" to start the scanning process.
View the grouped duplicate images with their file paths and similarity percentages in the results window.

Features

Uses dHash for image hashing
Employs Annoy for efficient similarity search
Supports common image formats (.png, .jpg, .jpeg, .bmp, .gif)
Displays progress bar during scanning
Groups duplicates with similarity percentages
Handles subdirectories recursively

Notes

The application uses a hamming distance threshold of 5 for identifying duplicates.
Similarity percentages are calculated based on the hamming distance relative to the 64-bit hash size.
Error handling is implemented for invalid images or processing errors.
