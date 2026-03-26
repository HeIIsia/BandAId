import os
import io
import base64
import threading
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageTk, ImageDraw
from dotenv import load_dotenv
from openai import OpenAI



#---------------------Theme

BG = "#151321"
CARD = "#1d1a2d"
CARD_2 = "#241f38"
ACCENT = "#9b7cff"
ACCENT_2 = "#c4b0ff"
#TEXT = "#f3efff"
TEXT = "#906cd6"
MUTED = "#b8add7"
INPUT_BG = "#0f1020"
BORDER = "#342c52"
BUTTON = "#7f5af0"
BUTTON_HOVER = "#936fff"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)


MODEL_NAME_1 = "gpt-5.4-mini"
MODEL_NAME = "gpt-5.4"



#-----------------------OpenAI

load_dotenv("keys.env")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))



#---------------------App state

selected_image_path = ""
preview_photo = None
app_icon_photo = None



#--------------------Window helpers

def center_window(win, width, height, parent=None):
    win.update_idletasks()

    if parent:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw // 2) - (width // 2)
        y = py + (ph // 2) - (height // 2)
    else:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)

    win.geometry(f"{width}x{height}+{x}+{y}")


def add_unique_value(text_widget, value):
    value = value.strip()
    if not value:
        return

    current = text_widget.get("1.0", "end-1c").strip()
    items = [item.strip() for item in current.split(",") if item.strip()]

    if value not in items:
        items.append(value)

    text_widget.delete("1.0", END)
    text_widget.insert("1.0", ", ".join(items))


def safe_text(widget):
    return widget.get("1.0", "end-1c").strip()


#------------------------Icon

def make_bandage(color_main, color_pad, hole_color):
    img = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((10, 28, 62, 44), radius=8, fill=color_main)
    d.rounded_rectangle((27, 23, 45, 49), radius=5, fill=color_pad)

    for x in (16, 21, 49, 54):
        d.ellipse((x, 32, x + 3, 35), fill=hole_color)
        d.ellipse((x, 37, x + 3, 40), fill=hole_color)

    return img


def create_bandaid_icon():
    base = Image.new("RGBA", (96, 96), (0, 0, 0, 0))

    b1 = make_bandage("#d9b48a", "#f5e5cf", "#9a7a63").rotate(
        45, expand=True, resample=Image.Resampling.BICUBIC
    )
    b2 = make_bandage("#e5c39a", "#faeddc", "#a6876c").rotate(
        -45, expand=True, resample=Image.Resampling.BICUBIC
    )

    x1 = (96 - b1.width) // 2
    y1 = (96 - b1.height) // 2
    x2 = (96 - b2.width) // 2
    y2 = (96 - b2.height) // 2

    base.alpha_composite(b1, (x1, y1))
    base.alpha_composite(b2, (x2, y2))

    final_img = base.resize((64, 64), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(final_img)



#-------------------Image helpers

def image_to_data_url(path):
    with Image.open(path) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        img.thumbnail((1024, 1024))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"


def select_file():
    global selected_image_path, preview_photo

    path = filedialog.askopenfilename(
        parent=window,
        title="Select an image",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"),
            ("All files", "*.*"),
        ],
    )

    if not path:
        return

    selected_image_path = path
    image_name_var.set(os.path.basename(path))

    try:
        img = Image.open(path)
        img.thumbnail((360, 300))
        preview_photo = ImageTk.PhotoImage(img)
        image_preview_label.config(image=preview_photo, text="")
    except Exception as e:
        messagebox.showerror("Image Error", f"Could not load image.\n\n{e}")



#-----------------Selection callbacks

def on_select_genre(event=None):
    add_unique_value(genres_selected_box, combo_genre.get())


def on_select_mood(event=None):
    mood_selected_box.delete("1.0", END)
    mood_selected_box.insert("1.0", combo_mood.get().strip())


def on_select_band(event=None):
    band_selected_var.set(combo_band.get().strip())



#--------------------Prompt builders

def build_user_content(description, genres, mood, band):
    content = [
        {
            "type": "input_text",
            "text": (
                f"Band to target strongly: {band or 'Not selected'}\n"
                f"Genres: {genres or 'Not selected'}\n"
                f"Mood: {mood or 'Not selected'}\n"
                f"Description: {description or 'Not provided'}"
            ),
        }
    ]

    if selected_image_path:
        content.append(
            {
                "type": "input_image",
                "image_url": image_to_data_url(selected_image_path),
            }
        )

    return content


def get_lyrics(description, genres, mood, band):
    response = client.responses.create(
        model=MODEL_NAME_1,
        input=[
            {
                "role": "developer",
                "content": (
                    "You are a professional lyricist. "
                    "Write original song lyrics based on the user's inputs. "
                    "Use the selected band as a STRONG stylistic north star only at a high level: "
                    "focus on energy, pacing, mood, imagery density, song structure, aggression, melody-vs-rhythm balance, "
                    "and recurring themes associated with that band. "
                    "If an image is attached, use it to refine atmosphere, texture, and emotional color. "
                    "Return lyrics only."
                ),
            },
            {
                "role": "user",
                "content": build_user_content(description, genres, mood, band),
            },
        ],
    )
    return (response.output_text or "").strip()


def revise_lyrics(lyrics_v1, description, genres, mood, band):
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "developer",
                "content": (
                    f"You are a the lyrics writer of the {band} band."
                    "Take the first draft and revise it so it feels MUCH closer to your band's overall hallmarks, "
                    "while preserving the core idea, hook, and strongest lines from the first draft. "
                    "Pay a LOT of attention to the selected band. Match the band's high-level feel as closely as possible "
                    "through structure, momentum, emotional intensity, imagery, vocal attitude, and phrasing density. "
                    "Use the first draft as the backbone, not as something to throw away. "
                    "If an image is attached, let it subtly influence atmosphere and detail choices. "
                    "Return only the revised lyrics.\n\n"
                    f"FIRST DRAFT:\n{lyrics_v1}"
                ),
            },
            {
                "role": "user",
                "content": build_user_content(description, genres, mood, band),
            },
        ],
    )
    return (response.output_text or "").strip()



#----------------Result popup

def show_lyrics_popup(final_lyrics, first_draft):
    popup = Toplevel(window)
    popup.title("Generated Lyrics")
    popup.config(bg=BG)

    if app_icon_photo:
        popup.iconphoto(True, app_icon_photo)

    center_window(popup, 860, 680, parent=window)

    header = Frame(popup, bg=BG)
    header.pack(fill="x", padx=18, pady=(16, 10))

    Label(
        header,
        text="Generated Lyrics",
        bg=BG,
        fg=TEXT,
        font=FONT_TITLE,
    ).pack(anchor="w")

    Label(
        header,
        text="Final version on top, first draft below.",
        bg=BG,
        fg=MUTED,
        font=FONT_BODY,
    ).pack(anchor="w", pady=(2, 0))

    notebook = ttk.Notebook(popup)
    notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    tab_final = Frame(notebook, bg=CARD)
    tab_draft = Frame(notebook, bg=CARD)
    notebook.add(tab_final, text="Final Lyrics")
    notebook.add(tab_draft, text="First Draft")

    final_box = ScrolledText(
        tab_final,
        wrap=WORD,
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=TEXT,
        font=FONT_MONO,
        relief="flat",
        padx=14,
        pady=14,
    )
    final_box.pack(fill="both", expand=True, padx=14, pady=14)
    final_box.insert("1.0", final_lyrics)
    final_box.config(state="disabled")

    draft_box = ScrolledText(
        tab_draft,
        wrap=WORD,
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=TEXT,
        font=FONT_MONO,
        relief="flat",
        padx=14,
        pady=14,
    )
    draft_box.pack(fill="both", expand=True, padx=14, pady=14)
    draft_box.insert("1.0", first_draft)
    draft_box.config(state="disabled")



#----------------Pipeline

def pipeline():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        messagebox.showerror("Missing API Key", "OPENAI_API_KEY was not found in keys.env.")
        return

    description = safe_text(description_box)
    genres = safe_text(genres_selected_box)
    mood = safe_text(mood_selected_box)
    band = band_selected_var.get().strip()

    if description == "Description...":
        description = ""

    if not band:
        messagebox.showwarning("Missing band", "Please select a band first.")
        return

    generate_button.config(state="disabled", text="Generating...")

    def worker():
        try:
            first_draft = get_lyrics(description, genres, mood, band)
            final_draft = revise_lyrics(first_draft, description, genres, mood, band)

            window.after(0, lambda: show_lyrics_popup(final_draft, first_draft))
        except Exception as e:
            error_text = f"Could not generate lyrics.\n\n{e}"
            window.after(
                0,
                lambda msg=error_text: messagebox.showerror("Generation Error", msg)
            )
        finally:
            window.after(
                0,
                lambda: generate_button.config(state="normal", text="Generate Lyrics")
            )

    threading.Thread(target=worker, daemon=True).start()



#--------------Main window

window = Tk()
window.title("BandAid")
window.config(bg=BG)
center_window(window, 1100, 640)

app_icon_photo = create_bandaid_icon()
window.iconphoto(True, app_icon_photo)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TCombobox",
    fieldbackground=INPUT_BG,
    background=INPUT_BG,
    foreground=TEXT,
    bordercolor=BORDER,
    lightcolor=BORDER,
    darkcolor=BORDER,
    arrowcolor=ACCENT_2,
)

style.configure("TNotebook", background=BG, borderwidth=0)
style.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 10, "bold"))



#--------------------Header

header_frame = Frame(window, bg=BG)
header_frame.pack(fill="x", padx=24, pady=(20, 14))

Label(
    header_frame,
    text="BandAid",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 24, "bold"),
).pack(anchor="w")

Label(
    header_frame,
    text="Describe the song, choose the mood, set the band, and let the image shape the atmosphere.",
    bg=BG,
    fg=MUTED,
    font=FONT_BODY,
).pack(anchor="w", pady=(4, 0))


#-----------------Main content

content = Frame(window, bg=BG)
content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

left_card = Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
left_card.pack(side="left", fill="both", expand=True, padx=(0, 12))

right_card = Frame(content, bg=CARD_2, highlightbackground=BORDER, highlightthickness=1)
right_card.pack(side="left", fill="both", expand=False, padx=(12, 0))



#----------------Left card content

left_inner = Frame(left_card, bg=CARD)
left_inner.pack(fill="both", expand=True, padx=18, pady=18)

Label(left_inner, text="Description", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=0, column=0, sticky="w")
description_box = Text(
    left_inner,
    height=6,
    width=44,
    bg=INPUT_BG,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=FONT_BODY,
)
description_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 16))
description_box.insert("1.0", "Description...")
description_box.focus()

Label(left_inner, text="Selected genres", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=2, column=0, sticky="w")
genres_selected_box = Text(
    left_inner,
    height=3,
    width=44,
    bg=INPUT_BG,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=FONT_BODY,
)
genres_selected_box.grid(row=3, column=0, sticky="ew", pady=(6, 12), padx=(0, 12))

Label(left_inner, text="Add genre", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=2, column=1, sticky="w")
combo_genre = ttk.Combobox(
    left_inner,
    values=[
        "Black Metal",
        "Thrash Metal",
        "Death Metal",
        "Industrial Metal",
        "Metalcore",
        "Power Metal",
        "Pop Rock",
        "Alternative Rock",
        "Punk Rock",
        "Christian Metal"

    ],
    state="readonly",
    width=24,
)
combo_genre.grid(row=3, column=1, sticky="ew", pady=(6, 12))
combo_genre.bind("<<ComboboxSelected>>", on_select_genre)

Label(left_inner, text="Selected mood", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=4, column=0, sticky="w")
mood_selected_box = Text(
    left_inner,
    height=2,
    width=44,
    bg=INPUT_BG,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=FONT_BODY,
)
mood_selected_box.grid(row=5, column=0, sticky="ew", pady=(6, 12), padx=(0, 12))

Label(left_inner, text="Mood", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=4, column=1, sticky="w")
combo_mood = ttk.Combobox(
    left_inner,
    values=[
        "Aggressive/Rebellious",
        "Melancholic",
        "Energetic",
        "Triumphant/Empowered",
        "Gentle",
        "Emotional",
        "Dark",
        "Heart-broken",
    ],
    state="readonly",
    width=24,
)
combo_mood.grid(row=5, column=1, sticky="ew", pady=(6, 12))
combo_mood.bind("<<ComboboxSelected>>", on_select_mood)

Label(left_inner, text="Band", bg=CARD, fg=TEXT, font=FONT_LABEL).grid(row=6, column=0, sticky="w")
band_selected_var = StringVar(value="")
combo_band = ttk.Combobox(
    left_inner,
    values=[
        "Children Of Bodom",
        "Pantera",
        "Metallica",
        "Megadeth",
        "Rammstein",
        "Dave Matthews Band",
        "Phish",
    ],
    state="readonly",
    width=30,
)
combo_band.grid(row=7, column=0, sticky="ew", pady=(6, 16))
combo_band.bind("<<ComboboxSelected>>", on_select_band)

selected_band_label = Label(
    left_inner,
    textvariable=band_selected_var,
    bg=INPUT_BG,
    fg=ACCENT_2,
    anchor="w",
    padx=10,
    pady=10,
    font=("Segoe UI", 10, "bold"),
)
selected_band_label.grid(row=7, column=1, sticky="ew", pady=(6, 16))

button_row = Frame(left_inner, bg=CARD)
button_row.grid(row=8, column=0, columnspan=2, sticky="w")

select_img_button = Button(
    button_row,
    text="Load Image",
    command=select_file,
    bg=BUTTON,
    fg="white",
    activebackground=BUTTON_HOVER,
    activeforeground="white",
    relief="flat",
    padx=16,
    pady=10,
    font=("Segoe UI", 10, "bold"),
)
select_img_button.pack(side="left", padx=(0, 10))

generate_button = Button(
    button_row,
    text="Generate Lyrics",
    command=pipeline,
    bg=BUTTON,
    fg="white",
    activebackground=BUTTON_HOVER,
    activeforeground="white",
    relief="flat",
    padx=16,
    pady=10,
    font=("Segoe UI", 10, "bold"),
)
generate_button.pack(side="left")

left_inner.grid_columnconfigure(0, weight=1)
left_inner.grid_columnconfigure(1, weight=1)



#-----------------Right card content

right_inner = Frame(right_card, bg=CARD_2)
right_inner.pack(fill="both", expand=True, padx=18, pady=18)

Label(
    right_inner,
    text="Visual Atmosphere",
    bg=CARD_2,
    fg=TEXT,
    font=FONT_TITLE,
).pack(anchor="w")

Label(
    right_inner,
    text="The selected image is previewed here and also sent with the prompt.",
    bg=CARD_2,
    fg=MUTED,
    font=FONT_BODY,
).pack(anchor="w", pady=(4, 14))

image_name_var = StringVar(value="No image selected")

Label(
    right_inner,
    textvariable=image_name_var,
    bg=CARD_2,
    fg=ACCENT_2,
    font=("Segoe UI", 10, "bold"),
    wraplength=340,
    justify="left",
).pack(anchor="w", pady=(0, 10))

preview_frame = Frame(
    right_inner,
    bg=INPUT_BG,
    width=380,
    height=320,
    highlightbackground=BORDER,
    highlightthickness=1,
)
preview_frame.pack()
preview_frame.pack_propagate(False)

image_preview_label = Label(
    preview_frame,
    text="No image loaded",
    bg=INPUT_BG,
    fg=MUTED,
    font=("Segoe UI", 11),
)
image_preview_label.pack(expand=True)

Label(
    right_inner,
    text="Tip: darker, colder, busier, or emptier images can subtly steer the lyrical atmosphere.",
    bg=CARD_2,
    fg=MUTED,
    font=("Segoe UI", 9),
    wraplength=360,
    justify="left",
).pack(anchor="w", pady=(14, 0))


window.mainloop()
