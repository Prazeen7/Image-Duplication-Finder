import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, Canvas, Toplevel
from PIL import Image, ImageTk
import imagehash
import os
from pathlib import Path

class DuplicateImageFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate Image Finder")
        self.root.geometry("1000x700")
        self.hash_size = 8  # For 64-bit hash
        self.image_paths = []
        self.hashes = []
        self.thumbnail_size = [100, 100]  # Default thumbnail size [width, height]
        self.displayed_images = []
        self.groups = []  # List for duplicate groups
        self.sort_ascending = False  # Initial sort order (descending)
        self.all_images = []  # For global navigation
        self.slider_timer = None  # For debouncing slider updates
        self.setup_ui()

    def setup_ui(self):
        # Folder selection
        self.folder_frame = ttk.Frame(self.root)
        self.folder_frame.pack(pady=10, padx=10, fill=tk.X)
        ttk.Button(self.folder_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT)
        self.folder_label = ttk.Label(self.folder_frame, text="No folder selected")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        # Scan and Sort options
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=5)
        ttk.Button(self.button_frame, text="Scan for Duplicates", command=self.scan_images).pack(side=tk.LEFT, padx=5)
        self.sort_button = ttk.Button(self.button_frame, text="Sort: Descending", command=self.toggle_sort)
        self.sort_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=5)

        # Results frame
        self.results_frame = ttk.Frame(self.root)
        self.results_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Text results
        self.result_text = scrolledtext.ScrolledText(self.results_frame, height=10, width=90)
        self.result_text.pack(side=tk.LEFT, fill=tk.Y)

        # Thumbnail view section
        self.thumbnail_frame = ttk.Frame(self.results_frame)
        self.thumbnail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Thumbnail size slider
        self.size_frame = ttk.Frame(self.thumbnail_frame)
        self.size_frame.pack(pady=5, fill=tk.X)
        ttk.Label(self.size_frame, text="Thumbnail Size:").pack(side=tk.LEFT)
        self.size_slider = ttk.Scale(self.size_frame, from_=50, to_=200, orient=tk.HORIZONTAL, 
                                    command=self.schedule_thumbnail_update)
        self.size_slider.set(100)
        self.size_slider.pack(side=tk.LEFT, padx=5)

        # Canvas for image display
        self.image_canvas = Canvas(self.thumbnail_frame, bg='white', width=300)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_canvas_scroll = ttk.Scrollbar(self.thumbnail_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        self.image_canvas_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_canvas.configure(yscrollcommand=self.image_canvas_scroll.set)

        # Bind mouse wheel scrolling
        self.image_canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.image_canvas.bind_all("<Button-4>", self._on_mousewheel)   # Linux (scroll up)
        self.image_canvas.bind_all("<Button-5>", self._on_mousewheel)   # Linux (scroll down)

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.image_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.image_canvas.yview_scroll(1, "units")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_label.config(text=folder)
            self.selected_folder = folder

    def calculate_dhash(self, image_path):
        try:
            with Image.open(image_path) as img:
                img = img.resize((self.hash_size, self.hash_size), Image.Resampling.LANCZOS).convert('L')
                return imagehash.dhash(img, hash_size=self.hash_size)
        except Exception:
            return None

    def create_thumbnail(self, image_path):
        try:
            with Image.open(image_path) as img:
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def schedule_thumbnail_update(self, *args):
        if self.slider_timer is not None:
            self.root.after_cancel(self.slider_timer)
        if not hasattr(self, 'selected_folder'):
            self.result_text.insert(tk.END, "Please select a folder first!\n")
            return
        self.slider_timer = self.root.after(200, self.update_thumbnails)

    def update_thumbnails(self):
        self.thumbnail_size = [int(self.size_slider.get()), int(self.size_slider.get())]
        self.display_results()

    def toggle_sort(self):
        if not hasattr(self, 'selected_folder'):
            self.result_text.insert(tk.END, "Please select a folder first!\n")
            return
        self.sort_ascending = not self.sort_ascending
        self.sort_button.config(text="Sort: Ascending" if self.sort_ascending else "Sort: Descending")
        self.display_results()

    def scan_images(self):
        if not hasattr(self, 'selected_folder'):
            self.result_text.insert(tk.END, "Please select a folder first!\n")
            return

        self.result_text.delete(1.0, tk.END)
        self.image_canvas.delete("all")
        self.displayed_images.clear()
        self.image_paths = []
        self.hashes = []
        self.groups.clear()
        self.all_images.clear()
        self.sort_ascending = False
        self.sort_button.config(text="Sort: Descending")

        # Get all image files
        supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        image_files = []
        total_files = 0

        for root, _, files in os.walk(self.selected_folder):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    image_files.append(os.path.join(root, file))
                    total_files += 1

        # Initialize progress bar
        self.progress['maximum'] = total_files
        self.progress['value'] = 0

        # Calculate hashes
        for i, image_path in enumerate(image_files):
            hash_val = self.calculate_dhash(image_path)
            if hash_val is not None:
                self.image_paths.append(image_path)
                self.hashes.append(str(hash_val))
            self.progress['value'] = i + 1
            self.root.update()

        # Find duplicates
        self.find_duplicates()

    def find_duplicates(self):
        threshold = 5
        processed = set()
        for i in range(len(self.image_paths)):
            if i in processed:
                continue
            group = [(self.image_paths[i], 0)]
            for j in range(i + 1, len(self.image_paths)):
                if j in processed:
                    continue
                dist = sum(c1 != c2 for c1, c2 in zip(self.hashes[i], self.hashes[j]))
                if dist <= threshold:
                    group.append((self.image_paths[j], dist))
                    processed.add(j)
            if len(group) > 1:
                self.groups.append(group)
            processed.add(i)
        self.display_results()

    def display_results(self):
        self.result_text.delete(1.0, tk.END)
        self.image_canvas.delete("all")
        self.displayed_images.clear()
        self.all_images.clear()

        if not self.groups:
            self.result_text.insert(tk.END, "No duplicates found!\n")
            return

        # Collect all images for global sorting
        for group_idx, images in enumerate(self.groups):
            for idx, (path, distance) in enumerate(images):
                similarity = 100 * (1 - distance / (self.hash_size * self.hash_size))
                self.all_images.append((group_idx, idx, path, distance, similarity))

        # Sort by similarity
        sorted_images = sorted(self.all_images, key=lambda x: x[4], reverse=not self.sort_ascending)
        sorted_groups = {}
        for group_idx, idx, path, distance, similarity in sorted_images:
            if group_idx not in sorted_groups:
                sorted_groups[group_idx] = []
            sorted_groups[group_idx].append((path, distance, idx))

        self.result_text.insert(tk.END, f"Found {len(self.groups)} groups of duplicate images (sorted by similarity):\n\n")
        y_position = 10

        for group_idx in sorted_groups:
            self.result_text.insert(tk.END, f"Group {group_idx + 1}:\n")
            self.image_canvas.create_text(10, y_position, text=f"Group {group_idx + 1}", anchor='nw')
            y_position += 20

            for path, distance, idx in sorted_groups[group_idx]:
                similarity = 100 * (1 - distance / (self.hash_size * self.hash_size))
                self.result_text.insert(tk.END, f"{path} (Similarity: {similarity:.2f}%)\n")
                thumbnail = self.create_thumbnail(path)
                if thumbnail:
                    image_id = self.image_canvas.create_image(10, y_position, image=thumbnail, anchor='nw')
                    self.image_canvas.create_text(20 + self.thumbnail_size[0], y_position + self.thumbnail_size[1]//2, 
                                                text=f"{Path(path).name} ({similarity:.2f}%)", anchor='w')
                    self.displayed_images.append(thumbnail)
                    self.image_canvas.tag_bind(image_id, '<Button-1>', 
                                              lambda e, g=group_idx, i=idx: self.open_fullscreen(g, i))
                    y_position += self.thumbnail_size[1] + 10
            self.result_text.insert(tk.END, "\n")
            y_position += 20

        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

    def open_fullscreen(self, group_idx, image_idx):
        fullscreen = Toplevel(self.root)
        fullscreen.title("Image Viewer")
        fullscreen.attributes('-fullscreen', True)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        image_frame = ttk.Frame(fullscreen)
        image_frame.pack(fill=tk.BOTH, expand=True)
        self.fullscreen_label = ttk.Label(image_frame)
        self.fullscreen_label.pack(fill=tk.BOTH, expand=True, anchor='center')

        nav_frame = ttk.Frame(fullscreen)
        nav_frame.pack(side=tk.BOTTOM, pady=10)
        ttk.Button(nav_frame, text="Previous", command=lambda: self.navigate_images(-1, fullscreen)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next", command=lambda: self.navigate_images(1, fullscreen)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Close", command=fullscreen.destroy).pack(side=tk.LEFT, padx=5)

        self.current_global_idx = self.get_global_index(group_idx, image_idx)
        self.update_fullscreen_image(fullscreen, screen_width, screen_height)

        fullscreen.bind('<Left>', lambda e: self.navigate_images(-1, fullscreen))
        fullscreen.bind('<Right>', lambda e: self.navigate_images(1, fullscreen))
        fullscreen.bind('<Escape>', lambda e: fullscreen.destroy())

    def get_global_index(self, group_idx, image_idx):
        for i, (g_idx, i_idx, _, _, _) in enumerate(self.all_images):
            if g_idx == group_idx and i_idx == image_idx:
                return i
        return 0

    def update_fullscreen_image(self, fullscreen, screen_width, screen_height):
        group_idx, image_idx, path, distance, similarity = self.all_images[self.current_global_idx]
        try:
            with Image.open(path) as img:
                img.thumbnail((screen_width - 20, screen_height - 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.fullscreen_label.config(image=photo, text=f"Group {group_idx + 1}: {Path(path).name} (Similarity: {similarity:.2f}%)", 
                                            compound='top', anchor='center')
                self.fullscreen_label.image = photo
        except Exception:
            pass

    def navigate_images(self, direction, fullscreen):
        self.current_global_idx = (self.current_global_idx + direction) % len(self.all_images)
        self.update_fullscreen_image(fullscreen, self.root.winfo_screenwidth(), self.root.winfo_screenheight())

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateImageFinder(root)
    root.mainloop()