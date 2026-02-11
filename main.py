from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import json
from openai import OpenAI, responses
import os
from settings import *
from functions import *
from lyrics_samples import *
from openai import OpenAI

IMG_PATH = ""

API_KEY = "YOUR KEY"
client = OpenAI(api_key=API_KEY)


window = Tk()
window.title("BandAid")
window.config(padx=50, pady=50, width=600, height=300, bg=DARKER_TINT_COLOR)


#Description
description_box = Text(height=5, width=35, bg=DARKEST_TINT_COLOR, fg=TINT_COLOR)
#Puts cursor in textbox.
description_box.focus()
description_box.insert(END, "Description...")
description_box.grid(row=0, column=0, columnspan=2)


lyrics_to_match = ""

def select_file():
    global IMG_PATH
    root = Tk()
    root.withdraw()

    img_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=(("Image files", "*.jpg"), ("All files", "*.*")),
    )
    IMG_PATH = img_path

def on_select(event):
    selected_item = combo.get()
    genres_selected_box.insert(END, selected_item)
    genres_selected_box.insert(END, ", ")

def on_select_mood(event):
    selected_item = combo_mood.get()
    mood_selected_box.insert(END, selected_item)
    mood_selected_box.insert(END, ", ")

def on_select_lyrics(event):
    #lyrics_to_match = ""
    selected_item = combo_lyrics.get()

    if selected_item == "Bodom After Midnight":
        lyrics_to_match = Bodom_after_midnight
    elif selected_item == "Everytime I die":
        lyrics_to_match = Everytime_I_die
    elif selected_item == "Angels don't kill":
        lyrics_to_match = Angels_dont_kill
    elif selected_item == "Hatecrew Deathroll":
        lyrics_to_match = Hatecrew_deathroll
    elif selected_item == "We're Not Gonna Fall":
        lyrics_to_match = Were_not_gonna_fall





#-------------GENRES SELECTED--------------------
genres_selected_box = Text(height=3, width=35, bg=DARKEST_TINT_COLOR, fg=TINT_COLOR)
# genres_selected_box.insert(END, "Selected genres...")
genres_selected_box.grid(row=1, column=0, columnspan=2)


#-------------GENRE SELECTION--------------------

genres=["Black Metal", "Christian Metal", "Death Metal", "Metalcore", "Power Metal", "Pop", "Punk Rock", "Thrash Metal"]
combo = ttk.Combobox( width=10, values=genres, foreground=TINT_COLOR)
combo.bind("<<ComboboxSelected>>", on_select)
# combo.place(x=200, y=150)
combo.grid(row=1, column=2, columnspan=2)

#-------------LYRICS SELECTION--------------------

lyrics_list =["Bodom After Midnight", "Everytime I die", "Angels don't kill", "Hatecrew Deathroll", "We're Not Gonna Fall"]
combo_lyrics = ttk.Combobox( width=10, values=lyrics_list, foreground=TINT_COLOR)
combo_lyrics.bind("<<ComboboxSelected>>", on_select_lyrics)
combo_lyrics.grid(row=0, column=2, columnspan=2)



#-------------MOOD SELECTED--------------------
mood_selected_box = Text(height=3, width=35, bg=DARKEST_TINT_COLOR, fg=TINT_COLOR)
mood_selected_box.grid(row=2, column=0, columnspan=2)


#-------------MOOD SELECTION--------------------
mood_values = ["Aggressive/Rebellious", "Melancholic", "Energetic", "Triumphant/Empowered", "Gentle", "Emotional", "Dark", "Heart-broken"]
combo_mood = ttk.Combobox( width=10, values=mood_values, foreground=TINT_COLOR)
combo_mood.bind("<<ComboboxSelected>>", on_select_mood)
combo_mood.grid(row=2, column=2, columnspan=2)

#------------SELECT IMAGE BUTTON---------------------
select_img_button = Button(window, text="Load Image", command=select_file)
# lyrics = generate_button.bind("<Button-1>", get_lyrics)
select_img_button.place(x=80, y=200)


#-------------- RESPONSE-------------------------

lyrics_v1 = ""
lyrics_v2 = ""

description_final = description_box.get("1.0", "end")
genres_final = genres_selected_box.get("1.0", "end")
mood_final = mood_selected_box.get("1.0", "end")


def get_lyrics():
    #description_final = description_box.get("1.0", "end")
    #genres_final = genres_selected_box.get("1.0", "end")
    # mood_final = MOOD
    #mood_final = mood_selected_box.get("1.0", "end")

    print(description_final)
    print(genres_final)
    print(mood_final)

    # img = "kitteh.jpg"
    img = IMG_PATH
    base64_image = encode_image(img)

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "developer",
                "content": f"""Create song lyrics in style of Alexi Laiho from Children Of Bodom according to the user's preferences. 


                Instructions:
                1) Gather the inputs from the user. Pay the most attention to the user's selected lyrics: {lyrics_to_match}. match the style as closely as possible.
                2) If an image was passed as an input, use it to make fine adjustments to the mood and style of the lyrics.
                3) Generate a draft for original lyrics
                4) ONLY print the lyrics, no other comments."""
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": f"Genre(s): {genres_final}\n Mood: {mood_final}\nDescription: {description_final} Lyrics to match in style and mood: {lyrics_to_match}"},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpg;base64,{base64_image}",
                        # "image_url": f"data:image/jpg;base64,{base64_image}",
                    },
                ],
            }
        ]
    )
    return response.output_text


def revise_lyrics(lyrics_v1, lyrics_to_match):
    #description_final = description_box.get("1.0", "end")
    #genres_final = genres_selected_box.get("1.0", "end")
    # mood_final = MOOD
    #mood_final = mood_selected_box.get("1.0", "end")

    print(description_final)
    print(genres_final)
    print(mood_final)

    # img = "kitteh.jpg"
    img = IMG_PATH
    base64_image = encode_image(img)

    new_response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "developer",
                "content": f"""You are Alexi Laiho from Children Of Bodom. 
                Critique the previously generated lyrics and improve it, matching 
                your unique style while preserving as much of the first draft as possible: {lyrics_v1}.

                INSTRUCTIONS: 
                1) Reflect on how to improve the lyrics while staying as close to the first draft as possible.
                2) Write a feedback on what should be changed.
                3) Sharpen the imagery through metaphors and twisted, memorable lines.
                4) Slightly prioritize ideas over rhymes if necessary. 
                5) Compare the lyrics against the user's preferences.
                6) Pay the most attention to the user's selected lyrics: {lyrics_to_match}. Match the style of your lyrics to the selected one as closely as possible.
                7) Revise the first draft and write the updated version of the lyrics. DO NOT write any other comments."""

            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": f"Genre(s): {genres_final}\n Mood: {mood_final}\nDescription: {description_final}"},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpg;base64,{base64_image}",
                        # "image_url": f"data:image/jpg;base64,{base64_image}",
                    },
                ],
            }
        ]
    )
    return new_response.output_text

def pipeline():
    draft_finalized = False
    first_draft = get_lyrics()
    print(first_draft)
    print("--------------------------------------------")
    while draft_finalized == False:
        user_approved = input("Proceed with this draft? y/n: ")
        if user_approved == "y":
            final_draft = revise_lyrics(first_draft, lyrics_to_match)
            print(final_draft)
            draft_finalized = True
        elif user_approved == "n":
            first_draft = get_lyrics()
            print(first_draft)
            print("--------------------------------------------")
        else:
            print("Invalid input")



#------------GENERATE BUTTON---------------------
generate_button = Button(window, text="Generate Lyrics", command=pipeline)

generate_button.place(x=180, y=200)



window.mainloop()
