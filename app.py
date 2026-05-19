from flask import Flask, render_template, request, send_file, after_this_request
from PIL import Image
import os
import uuid
import threading
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
CONVERTED_FOLDER = 'static/converted'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


# Add visitors Logic

def update_visitor_count():

    count_file = 'visitor_count.txt'

    with open(count_file, 'r') as file:

        count = int(file.read())

    count += 1

    with open(count_file, 'w') as file:

        file.write(str(count))

    return count


# Start Routing

@app.route('/')
def home():
    visitor_count = update_visitor_count()
    return render_template('index.html', visitor_count=visitor_count)

@app.route('/jpg-to-png')
def jpg_to_png():

    return render_template(
        'jpg_to_png.html'
    )


@app.route('/png-to-jpg')
def png_to_jpg():

    return render_template(
        'png_to_jpg.html'
    )


@app.route('/compress-image-to-50kb')
def compress_50kb():

    return render_template(
        'compress_50kb.html'
    )


@app.route('/passport-photo-maker')
def passport_photo():

    return render_template(
        'passport_photo.html'
    )


@app.route('/image-resizer')
def image_resizer():

    return render_template(
        'image_resizer.html'
    )


@app.route('/convert', methods=['POST'])
def convert():

    file = request.files.get('image')

    if not file:
        return "No file uploaded"

    # Form data
    width = request.form.get('width')
    height = request.form.get('height')
    unit = request.form.get('unit')
    output_format = request.form.get('format')
    target_size = request.form.get('target_size')

    # Unique filename
    unique_name = str(uuid.uuid4())




    # Pillow format mapping

    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'bmp': 'BMP',
        'tiff': 'TIFF'
    }

    save_format = format_map.get(
        output_format.lower(),
        output_format.upper()
    )

    # Save uploaded file
    upload_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name + "_" + file.filename
    )

    file.save(upload_path)

    # Open image
    img = Image.open(upload_path)

    # Resize logic
    if width and height:

        width = float(width)
        height = float(height)

        # Convert units to pixels

        if unit == 'mm':

            width = int(width * 3.78)
            height = int(height * 3.78)

        elif unit == 'cm':

            width = int(width * 37.8)
            height = int(height * 37.8)

        elif unit == 'in':

            width = int(width * 96)
            height = int(height * 96)

        else:

            width = int(width)
            height = int(height)

        img = img.resize((width, height))

    # JPG/JPEG needs RGB
    # if output_format.lower() in ['jpg', 'jpeg', 'webp']:

    #     img = img.convert('RGB')

    # Handle JPG/JPEG conversion properly

    if output_format.lower() in ['jpg', 'jpeg']:

        # Remove transparency if PNG has alpha channel
        if img.mode in ('RGBA', 'LA', 'P'):

            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])

            img = background

        else:

            img = img.convert('RGB')


    # WEBP conversion
    elif output_format.lower() == 'webp':

        img = img.convert('RGB')

    # Output filename
    output_filename = f"{unique_name}.{output_format}"

    output_path = os.path.join(
        CONVERTED_FOLDER,
        output_filename
    )

    # Compression logic

    try:

        # If target size entered
        if target_size and output_format.lower() in ['jpg', 'jpeg', 'webp']:

            target_size = int(target_size) * 1024

            quality = 95

            while quality >= 10:

                img.save(
                    output_path,
                    format=save_format,
                    optimize=True,
                    quality=quality
                )

                current_size = os.path.getsize(output_path)

                if current_size <= target_size:
                    break

                quality -= 5

        else:

            img.save(
                output_path,
                format=save_format
            )

    except Exception as e:

        return f"Error during conversion: {str(e)}"

    # Always return file
    # @after_this_request
    # def remove_files(response):

    #         try:

    #             # Delete uploaded file

    #             if os.path.exists(upload_path):
    #                 os.remove(upload_path)

    #             # Delete converted file

    #             if os.path.exists(output_path):
    #                 os.remove(output_path)

    #         except Exception as e:

    #             print("Error deleting files:", e)

    #         return response

    def delete_files(upload_path, output_path):

        time.sleep(5)

        try:

            if os.path.exists(upload_path):
                os.remove(upload_path)

            if os.path.exists(output_path):
                os.remove(output_path)

            print("Temporary files deleted")

        except Exception as e:

            print("Delete Error:", e)


# Add Background Delete Thread

    threading.Thread(
        target=delete_files,
        args=(upload_path, output_path)
    ).start()



    return send_file(
        output_path,
        as_attachment=True
    )


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)