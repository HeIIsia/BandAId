from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import base64
from settings import *




# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def select_file():
    # global FILEPATH
    # global ENCODED_IMG
    root = Tk()
    root.withdraw()

    img_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=(("Image files", "*.jpg"), ("All files", "*.*")),
    )

    # print(FILEPATH)


    # print(ENCODED_IMG)
    return img_path
