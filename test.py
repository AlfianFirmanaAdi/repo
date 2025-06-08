# app.py
import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import uuid # Untuk nama file unik
from datetime import datetime # Untuk tahun di footer

UPLOAD_FOLDER = 'uploads_galeri_wdf'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # Naikkan batas Max 32MB (opsional)
app.secret_key = "kunciRahasiaGaleriWDF789!"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

INDEX_HTML = """
<!DOCTYPE html>
<html lang="id" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏕️ Galeri WDF</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            margin-bottom: 2rem;
        }
        .gallery-container {
            column-count: 4;
            column-gap: 1rem;
            padding: 0 0.5rem; /* Sedikit padding agar tidak terlalu mepet tepi */
        }
        .gallery-item-wrapper {
            break-inside: avoid-column;
            margin-bottom: 1rem;
            display: inline-block; /* Penting untuk column layout */
            width: 100%;
            background-color: #2c3034; /* Latar belakang "kartu" */
            border-radius: 0.3rem;
            overflow: hidden; /* Untuk memastikan border-radius berlaku pada gambar */
            position: relative; /* Untuk potensi overlay atau badge di masa depan */
        }
        .gallery-image {
            width: 100%; /* Gambar mengisi lebar wrapper */
            height: auto;  /* Tinggi otomatis menjaga rasio aspek */
            object-fit: contain; /* Pastikan seluruh gambar terlihat */
            display: block;
            border-radius: 0.25rem 0.25rem 0 0; /* Lengkungan hanya di atas jika ada footer di kartu */
            transition: transform 0.2s ease-in-out, opacity 0.2s ease-in-out;
            cursor: pointer;
        }
        .gallery-image:hover:not(.selected-for-delete) { /* Hanya hover jika tidak dalam mode hapus & belum terpilih */
            transform: scale(1.03);
        }
        .page-title {
            color: #e9ecef;
        }
        .footer {
            text-align: center;
            padding: 1.5rem 0;
            margin-top: 3rem;
            background-color: #1c1c1e;
            color: #adb5bd;
        }
        .lightbox {
            display: none; position: fixed; z-index: 9999; top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.9); justify-content: center; align-items: center;
            backdrop-filter: blur(5px);
        }
        .lightbox img { max-width: 90%; max-height: 90%; border-radius: 5px; box-shadow: 0 0 25px rgba(0,0,0,0.5); }
        .lightbox-close {
            position: absolute; top: 20px; right: 30px; font-size: 2.5rem; color: #bbb;
            cursor: pointer; text-decoration: none; line-height: 1;
        }
        .lightbox-close:hover { color: white; }
        .alert a.alert-link { color: var(--bs-dark-text-emphasis); }

        /* Gaya untuk Mode Hapus */
        .gallery-image.selected-for-delete {
            border: 3px solid var(--bs-danger);
            opacity: 0.7;
            transform: scale(0.95); /* Sedikit mengecil saat dipilih */
        }
        .delete-mode-active .gallery-image { /* Saat mode hapus aktif, ubah cursor gambar */
            cursor: cell !important; /* Paksa cursor cell */
        }
        .delete-mode-active .gallery-image:hover {
             transform: scale(1.0); /* Matikan efek hover zoom normal */
        }


        /* Responsive column counts */
        @media (max-width: 1199px) { .gallery-container { column-count: 3; } } /* xl */
        @media (max-width: 991px)  { .gallery-container { column-count: 2; } } /* lg */
        @media (max-width: 767px)  { .gallery-container { column-count: 2; } } /* md */
        @media (max-width: 575px)  { .gallery-container { column-count: 1; } } /* sm */

    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{{ url_for('index') }}">Galeri WDF</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item me-2" id="addPhotoNavItem">
                        <a class="btn btn-light" href="{{ url_for('upload_file_page') }}">➕ Tambah Foto</a>
                    </li>
                    <li class="nav-item">
                        <button class="btn btn-outline-danger" id="toggleDeleteModeBtn">🗑️ Pilih Hapus</button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=True) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category if category else 'secondary' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <h2 class="mb-4 text-center page-title">Koleksi Foto</h2>

        {% if images %}
            <form id="deleteForm" method="post" action="{{ url_for('delete_photos') }}">
                <div class="gallery-container">
                    {% for image_name in images %}
                        <div class="gallery-item-wrapper">
                            <img src="{{ url_for('serve_uploaded_file', filename=image_name) }}"
                                 alt="Foto Galeri WDF {{ loop.index }}"
                                 class="gallery-image"
                                 data-filename="{{ image_name }}" 
                                 onclick="handleImageClick(this, '{{ url_for('serve_uploaded_file', filename=image_name) }}')">
                            <input class="delete-checkbox d-none" type="checkbox" name="selected_images" value="{{ image_name }}" id="cb-{{ image_name | replace('.', '-') }}">
                        </div>
                    {% endfor %}
                </div>
                <div id="deleteConfirmArea" class="mt-4 text-center" style="display:none;">
                // TOMBOL HAPUS YANG BERADA DIBAWAH
                    <button type="button" class="btn btn-danger btn-lg" id="confirmDeletionBtn">Hapus <span id="deleteCount">0</span> Foto Terpilih</button>
                    <button type="button" class="btn btn-secondary btn-lg ms-2" id="cancelDeleteModeBtn">Batal</button>
                </div>
                
            </form>
        {% else %}
            <div class="col-12">
                <div class="alert alert-secondary text-center" role="alert">
                    Belum ada foto di Galeri WDF. <a href="{{ url_for('upload_file_page') }}" class="alert-link">Jadilah yang pertama mengunggah!</a>
                </div>
            </div>
        {% endif %}
    </div>

    <div id="myLightbox" class="lightbox" onclick="closeLightbox(event)">
        <a href="javascript:void(0)" class="lightbox-close" onclick="closeLightbox(event)">&times;</a>
        <img id="lightboxImage" src="" alt="Gambar Diperbesar">
    </div>

    <footer class="footer">
        <p>&copy; {{ current_year }} Galeri WDF. Dibuat untuk Kenangan.</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const lightbox = document.getElementById('myLightbox');
        const lightboxImage = document.getElementById('lightboxImage');
        let deleteMode = false;
        const selectedForDelete = new Set();

        const toggleDeleteModeBtn = document.getElementById('toggleDeleteModeBtn');
        const addPhotoNavItem = document.getElementById('addPhotoNavItem');
        const deleteConfirmArea = document.getElementById('deleteConfirmArea');
        const confirmDeletionBtn = document.getElementById('confirmDeletionBtn');
        const cancelDeleteModeBtn = document.getElementById('cancelDeleteModeBtn');
        const deleteCountSpan = document.getElementById('deleteCount');
        const galleryImages = document.querySelectorAll('.gallery-image');
        const deleteForm = document.getElementById('deleteForm');
        const bodyElement = document.body;


        function openLightbox(imageUrl) {
            if (deleteMode) return; // Jangan buka lightbox jika dalam mode hapus
            lightboxImage.src = imageUrl;
            lightbox.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox(event) {
            if (event && event.target && (event.target === lightbox || event.target.classList.contains('lightbox-close'))) {
                lightbox.style.display = 'none';
                lightboxImage.src = '';
                document.body.style.overflow = 'auto';
            }
        }
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && lightbox.style.display === 'flex') {
                closeLightbox({ target: lightbox });
            }
        });

        function updateDeleteButtonState() {
            deleteCountSpan.textContent = selectedForDelete.size;
            confirmDeletionBtn.disabled = selectedForDelete.size === 0;
        }

        function enterDeleteMode() {
            deleteMode = true;
            bodyElement.classList.add('delete-mode-active');
            if(toggleDeleteModeBtn) {
                toggleDeleteModeBtn.textContent = '🚫 Batal Hapus';
                toggleDeleteModeBtn.classList.remove('btn-outline-danger');
                toggleDeleteModeBtn.classList.add('btn-warning');
            }
            if(addPhotoNavItem) addPhotoNavItem.style.display = 'none';
            if(deleteConfirmArea) deleteConfirmArea.style.display = 'block';
            updateDeleteButtonState();
        }

        function exitDeleteMode() {
            deleteMode = false;
            bodyElement.classList.remove('delete-mode-active');
            if(toggleDeleteModeBtn) {
                toggleDeleteModeBtn.textContent = '🗑️ Pilih Hapus';
                toggleDeleteModeBtn.classList.remove('btn-warning');
                toggleDeleteModeBtn.classList.add('btn-outline-danger');
            }
            if(addPhotoNavItem) addPhotoNavItem.style.display = 'list-item'; // Sesuaikan dengan display aslinya
            if(deleteConfirmArea) deleteConfirmArea.style.display = 'none';
            
            selectedForDelete.clear();
            galleryImages.forEach(img => {
                img.classList.remove('selected-for-delete');
                const checkboxId = 'cb-' + img.dataset.filename.replace(/\./g, '-');
                const checkbox = document.getElementById(checkboxId);
                if(checkbox) checkbox.checked = false;
            });
            updateDeleteButtonState();
        }

        function handleImageClick(imgElement, imageUrlForLightbox) {
            if (deleteMode) {
                const filename = imgElement.dataset.filename;
                const checkboxId = 'cb-' + filename.replace(/\./g, '-'); // Titik diganti strip untuk ID valid
                const checkbox = document.getElementById(checkboxId);

                if (selectedForDelete.has(filename)) {
                    selectedForDelete.delete(filename);
                    imgElement.classList.remove('selected-for-delete');
                    if(checkbox) checkbox.checked = false;
                } else {
                    selectedForDelete.add(filename);
                    imgElement.classList.add('selected-for-delete');
                    if(checkbox) checkbox.checked = true;
                }
                updateDeleteButtonState();
            } else {
                openLightbox(imageUrlForLightbox);
            }
        }
        
        if(toggleDeleteModeBtn) {
            toggleDeleteModeBtn.addEventListener('click', () => {
                if (deleteMode) {
                    exitDeleteMode();
                } else {
                    enterDeleteMode();
                }
            });
        }

        if(cancelDeleteModeBtn) {
            cancelDeleteModeBtn.addEventListener('click', exitDeleteMode);
        }

        if(confirmDeletionBtn && deleteForm) {
    confirmDeletionBtn.addEventListener('click', () => {
        if (selectedForDelete.size === 0) {
            alert('Pilih setidaknya satu foto untuk dihapus.');
            return;
        }
        if (confirm(`Anda yakin ingin menghapus ${selectedForDelete.size} foto yang dipilih? Operasi ini tidak dapat dibatalkan.`)) {
            // Langkah Tambahan: Pastikan hanya checkbox yang relevan yang tercentang
            // 1. Hapus centang semua checkbox delete terlebih dahulu
            document.querySelectorAll('input[name="selected_images"].delete-checkbox').forEach(cb => {
                cb.checked = false;
            });

            // 2. Centang hanya checkbox yang ada di selectedForDelete
            let foundAllCheckboxes = true;
            selectedForDelete.forEach(filename => {
                const checkboxId = 'cb-' + filename.replace(/\./g, '-');
                const checkbox = document.getElementById(checkboxId);
                if (checkbox) {
                    checkbox.checked = true;
                } else {
                    console.warn("Peringatan saat konfirmasi hapus: Checkbox tidak ditemukan untuk file terpilih:", filename);
                    foundAllCheckboxes = false; // Tandai jika ada checkbox yang tidak ditemukan
                }
            });

            // Opsional: Jika ada checkbox yang tidak ditemukan, mungkin ada masalah sinkronisasi
            if (!foundAllCheckboxes) {
                // Anda bisa memilih untuk menghentikan submit atau memberi tahu pengguna
                // Untuk saat ini, kita biarkan proses submit berlanjut, 
                // tapi log console di atas akan membantu debugging.
            }
            
            deleteForm.submit();
        }
    });
}

    </script>
</body>
</html>
"""

UPLOAD_HTML = """
<!DOCTYPE html>
<html lang="id" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galeri WDF</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding-top: 70px; /* Padding untuk fixed-top navbar yang sedikit lebih tinggi */
        }
        .upload-container {
            max-width: 600px;
            margin: 2rem auto;
            padding: 2.5rem; 
            border-radius: 0.5rem;
            background-color: #2c3034; /* Background kartu untuk form */
            box-shadow: 0 0.25rem 0.75rem rgba(0,0,0,0.2);
        }
         .page-title {
            color: #e9ecef;
        }
        .footer {
            text-align: center;
            padding: 1.5rem 0;
            margin-top: 3rem;
            background-color: #1c1c1e;
            color: #adb5bd;
        }
        .form-label {
            color: #c6cdd5; /* Warna label lebih terang */
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{{ url_for('index') }}">Galeri WDF</a>
             <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="btn btn-outline-light btn-sm" href="{{ url_for('index') }}">&larr; Kembali ke Galeri</a>
                </li>
            </ul>
        </div>
    </nav>

    <div class="container upload-container">
        <h1 class="mb-4 text-center page-title">Bagikan Foto ke Galeri WDF</h1>
        
        {% with messages = get_flashed_messages(with_categories=True) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category if category else 'secondary' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <label for="file" class="form-label">Pilih Foto (Max: {{ app.config['MAX_CONTENT_LENGTH'] // (1024*1024) }}MB, Format: {{ ', '.join(ALLOWED_EXTENSIONS) }})</label>
                <input class="form-control form-control-lg" type="file" id="file" name="file" required>
            </div>
            <div class="d-grid gap-2 mt-4">
                <button type="submit" class="btn btn-light btn-lg">Unggah Foto</button>
            </div>
        </form>
    </div>

    <footer class="footer">
        <p>&copy; {{ current_year }} Galeri WDF.</p>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year, 'ALLOWED_EXTENSIONS': ALLOWED_EXTENSIONS, 'app': app}


@app.route('/')
def index():
    image_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        valid_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
        image_files = sorted(
            valid_files,
            key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)),
            reverse=True
        )
    return render_template_string(INDEX_HTML, images=image_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Tidak ada bagian file terdeteksi.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Tidak ada file yang dipilih.', 'warning')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_id = uuid.uuid4().hex[:8]
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{unique_id}{ext}"
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            flash('Foto berhasil diunggah ke Galeri WDF!', 'success')
            return redirect(url_for('index'))
        else:
            flash(f"Jenis file tidak diizinkan. Hanya: {', '.join(ALLOWED_EXTENSIONS)}.", 'danger')
            return redirect(request.url)
    return render_template_string(UPLOAD_HTML)

@app.route('/delete_photos', methods=['POST'])
def delete_photos():
    if request.method == 'POST':
        selected_images = request.form.getlist('selected_images')

        if not selected_images:
            flash('Tidak ada foto yang dipilih untuk dihapus.', 'warning')
            return redirect(url_for('index'))

        deleted_count = 0
        error_count = 0

        upload_folder_abs = os.path.abspath(app.config['UPLOAD_FOLDER'])

        for filename_to_delete in selected_images:
            file_path_abs = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete))

            # Validasi keamanan untuk mencegah path traversal
            if not file_path_abs.startswith(upload_folder_abs) or '..' in filename_to_delete:
                flash(f"Nama file tidak valid atau akses ditolak: {filename_to_delete}", 'danger')
                error_count += 1
                continue

            if os.path.exists(file_path_abs):
                try:
                    os.remove(file_path_abs)
                    deleted_count += 1
                except Exception as e:
                    error_count += 1
                    flash(f"Gagal menghapus {filename_to_delete}: {str(e)}", 'danger')
            else:
                flash(f"File {filename_to_delete} tidak ditemukan.", 'warning')
                error_count +=1 

        if deleted_count > 0:
            flash(f'{deleted_count} foto berhasil dihapus.', 'success')
        if error_count > 0 :
             flash(f'{error_count} foto gagal dihapus atau tidak ditemukan.', 'danger' if deleted_count == 0 else 'warning')

    return redirect(url_for('index'))


@app.route('/uploads_galeri_wdf/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)