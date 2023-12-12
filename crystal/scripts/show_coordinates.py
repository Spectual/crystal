import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

def load_image():
    filepath = filedialog.askopenfilename()
    if filepath:
        image = Image.open(filepath)
        photo = ImageTk.PhotoImage(image)
        label.config(image=photo)
        label.image = photo

def show_coordinates(event):
    x, y = event.x, event.y
    coordinates_var.set(f"Coordinates: ({x}, {y})")

root = tk.Tk()
root.title("Image Viewer with Coordinates")

coordinates_var = tk.StringVar()
coordinates_label = tk.Label(root, textvariable=coordinates_var)
coordinates_label.pack()

load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack()

label = tk.Label(root)
label.bind("<Motion>", show_coordinates)
label.pack()

root.mainloop()
