from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import base64
import sys

# Importing the required modules for PDF comparison
from wage_and_apprenticeship import extract_pages
from statement_of_values import sov_main
from payment_summary import payment_summary_main
from address_search import process_file
from pdf_comparison import main_pdf_comparison  # Ensure the comparison logic is correctly imported

sys.path.insert(0, "./package")

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# HOME PAGE
@app.route('/')
def home_page():
    return render_template('index.html')


# ADDRESS SEARCH
@app.route('/address_search')
def address_search():
    return render_template('address_search.html')

@app.route('/address_search_upload', methods=['POST'])
def address_search_upload():
    uploaded_file = request.files['file']
    if uploaded_file:
        filename = uploaded_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)

        updated_file_path = process_file(file_path, filename)

        # Read the processed CSV file content
        with open(updated_file_path, 'r') as csv_file:
            csv_content = csv_file.read()

        # Send the CSV content to the frontend as JSON
        return jsonify({'filename': os.path.basename(updated_file_path), 'csv_data': csv_content})

    return 'No file uploaded', 400


# STATEMENT OF VALUES
@app.route('/statement_of_values')
def statement_of_values_page():
    return render_template('statement_of_values.html')

@app.route('/sov_upload', methods=['POST'])
def sov_upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_reply_pairs = sov_main(file_path)
        image_paths = [f'/uploads/{os.path.basename(path)}' for path in image_reply_pairs.keys()]
        csv_data = [reply for reply in image_reply_pairs.values()]
        return jsonify({'image_paths': image_paths, 'csv_data': csv_data})


# WAGE & APPRENTICESHIP
@app.route('/wage_and_apprenticeship')
def wage_and_apprenticeship_page():
    return render_template('wage_and_apprenticeship.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_reply_pairs = extract_pages(file_path)
        image_paths = [f'/uploads/{os.path.basename(path)}' for path in image_reply_pairs.keys()]
        csv_data = [reply for reply in image_reply_pairs.values()]
        return jsonify({'image_paths': image_paths, 'csv_data': csv_data})


# PAYMENT SUMMARY
@app.route('/payment_summary')
def payment_summary():
    return render_template('payment_summary.html')

@app.route('/payment_summary_upload', methods=['POST'])
def payment_summary_upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_reply_pairs = payment_summary_main(file_path)
        image_paths = [f'/uploads/{os.path.basename(path)}' for path in image_reply_pairs.keys()]
        csv_data = [reply for reply in image_reply_pairs.values()]
        return jsonify({'image_paths': image_paths, 'csv_data': csv_data})


# PDF COMPARISON
@app.route('/pdf_comparison')
def pdf_comparison():
    return render_template('pdf_comparison.html')

@app.route('/pdf_comparison_upload', methods=['POST'])
def pdf_comparison_upload():
    prior_year_file = request.files['priorYearPDF']
    current_year_file = request.files['currentYearPDF']

    prior_year_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(prior_year_file.filename))
    current_year_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(current_year_file.filename))
    
    prior_year_file.save(prior_year_path)
    current_year_file.save(current_year_path)

    try:
        annotated_pdf_path = main_pdf_comparison(prior_year_path, current_year_path)

        # Read the processed PDF file content
        with open(annotated_pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        # Encode the PDF content to Base64
        encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')

        # Send the Base64-encoded PDF content to the frontend as JSON
        return jsonify({'filename': os.path.basename(annotated_pdf_path), 'pdf_data': encoded_pdf})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


# FILE UPLOAD
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
