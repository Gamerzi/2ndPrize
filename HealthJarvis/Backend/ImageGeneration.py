import asyncio
from random import randint
from PIL import Image
import requests
import os
from time import sleep

def open_images(prompt):
    # Ensure the output folder is relative to this file (in backend)
    folder_path = os.path.join(os.path.dirname(__file__), "Data")
    prompt_formatted = prompt.replace(" ", "_")  # Replace spaces with underscores
    
    # Generate the filenames for the images
    files = [f"{prompt_formatted}{i}.jpg" for i in range(1, 5)]
    
    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            # Try to open and display the image
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)  # Pause for 1 second before showing the next image
        except IOError:
            print(f"Unable to open {image_path}")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# Hard coded Hugging Face API key (replace with your actual API key)
HUGGING_FACE_API_KEY = ""
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}

# Async function to send a query to the Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return b""
    return response.content

# Async function to generate images based on the given prompt
async def generate_images(prompt: str):
    # Ensure the output folder exists (relative to the backend file)
    output_folder = os.path.join(os.path.dirname(__file__), "Data")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    tasks = []
    # Create 4 image generation tasks
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed = {randint(0, 1000000)}",
            "options": {"wait_for_model": True}
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)
    
    # Wait for all tasks to complete
    image_bytes_list = await asyncio.gather(*tasks)
    
    # Save the generated images to disk
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:  # Only save if non-empty bytes were returned
            image_filename = f"{prompt.replace(' ', '_')}{i + 1}.jpg"
            image_path = os.path.join(output_folder, image_filename)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            print(f"Saved image to {image_path}")
        else:
            print(f"No image generated for task {i + 1}")

# Wrapper function to generate and open images
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))  # Run the async image generation
    open_images(prompt)  # Open the generated images

def get_data_file_path():
    # Construct the path relative to this backend file.
    # Assuming the backend folder and Frontend folder are siblings:
    return os.path.join(os.path.dirname(__file__), "..", "Frontend", "Files", "ImageGeneration.data")

while True:
    try:
        data_file_path = get_data_file_path()
        # Read the status and prompt from the data file
        with open(data_file_path, "r") as f:
            data: str = f.read()
        
        Prompt, Status = data.split(",")
        
        # If the status indicates an image generation request
        if Status.strip() == "True":
            print("Generating Images...")
            GenerateImages(prompt=Prompt)
            
            # Reset the status in the file after generating images
            with open(data_file_path, "w") as f:
                f.write("False,False")
            break  # Exit the loop after processing the request
        else:
            sleep(1)  # Wait 1 second before checking again
    except Exception as e:
        print("Exception:", e)
        sleep(1)
