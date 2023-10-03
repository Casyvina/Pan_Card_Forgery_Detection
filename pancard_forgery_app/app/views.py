from app import app
from flask import request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from skimage.metrics import structural_similarity
import os
import imutils
import cv2
from PIL import Image 

app.config['INITIAL_FILE_UPLOADS'] = 'app/static/uploads'
app.config['EXISTING_FILE'] = 'app/static/original'
app.config['GENERATED_FILE'] = 'app/static/generated'

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg',])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def upload_image():

    if request.method == "GET":
        return render_template("index.html")
    
    if request.method == "POST":

        if 'file_upload' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file_upload = request.files['file_upload']
        if file_upload.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file_upload and allowed_file(file_upload.filename):
            filename = secure_filename(file_upload.filename)
            flash('Image sucessfullly uploaded and displayed below')

            uploaded_image = Image.open(file_upload).resize((250, 160))
            uploaded_image.save(os.path.join(app.config['INITIAL_FILE_UPLOADS'], 'image.jpg'))

            original_image = Image.open(os.path.join(app.config['EXISTING_FILE'], 'image.jpg')).resize((250, 160))
            original_image.save(os.path.join(app.config['EXISTING_FILE'], 'image.jpg'))

            original_image = cv2.imread(os.path.join(app.config['EXISTING_FILE'], 'image.jpg'))
            uploaded_image= cv2.imread(os.path.join(app.config['INITIAL_FILE_UPLOADS'], 'image.jpg'))

            original_gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
            uploaded_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)

            (score, diff) = structural_similarity(original_gray, uploaded_gray, full=True)
            diff = (diff * 255).astype("uint8")

            thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(original_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(uploaded_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_original.jpg'), original_image)
            cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_uploaded.jpg'), uploaded_image)
            cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_diff.jpg'), diff)
            cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_thresh.jpg'), thresh)

            file_url = url_for('get_file', filename='image.jpg')
            return render_template('index.html', pred=str(round(score*100,2)) + '%' + ' correct', file_url=file_url)
        else:
            flash('Allowed image types are - jpg, jpeg')
            return redirect(request.url)

@app.route('/static/uploads/<filename>')
def get_file(filename):
    return send_from_directory('static/uploads', filename)


if __name__ == '__main__':
    app.run(debug=True)