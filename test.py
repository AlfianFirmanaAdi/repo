import streamlit as st
import os
from PIL import Image
import uuid # Untuk nama file unik
from datetime import datetime # Untuk tahun di footer

# Konfigurasi
UPLOAD_FOLDER = 'uploads_galeri_wdf'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
MAX_FILE_SIZE_MB = 32 # Max 32MB

# Buat folder upload jika belum ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

st.set_page_config(
    page_title="🏕️ Galeri WDF",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1a1a1a; /* Dark background for the app */
        color: #e0e0e0; /* Light text color */
    }
    .st-emotion-cache-nahz7x { /* Adjust header background if needed */
        background-color: #2c3034;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #e9ecef;
    }
    .stFileUploader {
        color: #e0e0e0;
    }
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0a58ca;
    }
    .stButton>button:active {
        background-color: #084298;
    }
    .delete-button {
        background-color: #dc3545 !important;
    }
    .delete-button:hover {
        background-color: #bb2d3b !important;
    }
    .stAlert {
        color: #e0e0e0;
        background-color: #343a40;
        border-color: #495057;
    }
    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
    }
    .gallery-item {
        background-color: #2c3034;
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 0.25rem 0.75rem rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 0.5rem;
    }
    .gallery-item img {
        width: 100%;
        height: 200px; /* Fixed height for consistency */
        object-fit: cover; /* Crop to fill */
        border-radius: 0.3rem;
    }
    .footer {
        text-align: center;
        padding: 1.5rem 0;
        margin-top: 3rem;
        background-color: #1c1c1e;
        color: #adb5bd;
        position: relative;
        bottom: 0;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏕️ Galeri WDF")
st.markdown("---")

# --- Bagian Upload Foto ---
st.header("Bagikan Foto ke Galeri WDF")

uploaded_file = st.file_uploader(
    f"Pilih Foto (Max: {MAX_FILE_SIZE_MB}MB, Format: {', '.join(ALLOWED_EXTENSIONS)})",
    type=list(ALLOWED_EXTENSIONS),
    key="file_uploader"
)

if uploaded_file is not None:
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(f"Ukuran file terlalu besar. Maksimal {MAX_FILE_SIZE_MB}MB.")
    elif not allowed_file(uploaded_file.name):
        st.error(f"Jenis file tidak diizinkan. Hanya: {', '.join(ALLOWED_EXTENSIONS)}.")
    else:
        # Simpan file
        filename = uploaded_file.name
        unique_id = uuid.uuid4().hex[:8]
        base, ext = os.path.splitext(filename)
        unique_filename = f"{base}_{unique_id}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Foto berhasil diunggah ke Galeri WDF! 📸")
            st.rerun() # Refresh halaman untuk menampilkan foto baru
        except Exception as e:
            st.error(f"Gagal mengunggah foto: {e}")

st.markdown("---")

# --- Bagian Galeri ---
st.header("Koleksi Foto")

image_files = []
if os.path.exists(UPLOAD_FOLDER):
    valid_files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    # Urutkan berdasarkan waktu modifikasi terbaru
    image_files = sorted(
        valid_files,
        key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)),
        reverse=True
    )

if not image_files:
    st.info("Belum ada foto di Galeri WDF. Jadilah yang pertama mengunggah! 🌟")
else:
    # Mode Hapus
    if 'delete_mode' not in st.session_state:
        st.session_state.delete_mode = False
    if 'selected_for_delete' not in st.session_state:
        st.session_state.selected_for_delete = set()

    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        if st.session_state.delete_mode:
            if st.button("🚫 Batal Hapus", key="cancel_delete_mode"):
                st.session_state.delete_mode = False
                st.session_state.selected_for_delete = set()
                st.rerun()
        else:
            if st.button("🗑️ Pilih Hapus", key="toggle_delete_mode"):
                st.session_state.delete_mode = True
                st.rerun()

    if st.session_state.delete_mode:
        st.warning("Pilih foto yang ingin Anda hapus. Klik lagi untuk membatalkan pilihan.")

    # Tampilkan Galeri
    num_cols = st.columns(1)[0].slider("Jumlah Kolom", 1, 6, 4) # Slider for responsive columns

    # Display images in a grid
    cols = st.columns(num_cols)
    col_idx = 0

    for image_name in image_files:
        with cols[col_idx]:
            file_path = os.path.join(UPLOAD_FOLDER, image_name)
            try:
                img = Image.open(file_path)
                
                # Gunakan st.container untuk membungkus gambar dan checkbox
                with st.container(border=True): # Menggunakan border=True untuk tampilan seperti kartu
                    st.image(img, caption=image_name, use_column_width=True)

                    if st.session_state.delete_mode:
                        checkbox_key = f"delete_cb_{image_name}"
                        is_checked = image_name in st.session_state.selected_for_delete
                        
                        if st.checkbox(f"Pilih untuk hapus", value=is_checked, key=checkbox_key):
                            st.session_state.selected_for_delete.add(image_name)
                        else:
                            if image_name in st.session_state.selected_for_delete:
                                st.session_state.selected_for_delete.remove(image_name)

            except Exception as e:
                st.error(f"Tidak dapat memuat gambar {image_name}: {e}")
        
        col_idx = (col_idx + 1) % num_cols

    if st.session_state.delete_mode and st.session_state.selected_for_delete:
        st.markdown("---")
        st.markdown(
            f"<h3 style='text-align: center; color: #e9ecef;'>{len(st.session_state.selected_for_delete)} Foto Terpilih</h3>",
            unsafe_allow_html=True
        )
        if st.button(
            f"Hapus {len(st.session_state.selected_for_delete)} Foto Terpilih",
            key="confirm_delete",
            type="primary" # Menggunakan type primary untuk tombol utama
        ):
            deleted_count = 0
            error_count = 0
            upload_folder_abs = os.path.abspath(UPLOAD_FOLDER)

            for filename_to_delete in st.session_state.selected_for_delete:
                file_path_abs = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename_to_delete))

                # Validasi keamanan untuk mencegah path traversal
                if not file_path_abs.startswith(upload_folder_abs) or '..' in filename_to_delete:
                    st.error(f"Nama file tidak valid atau akses ditolak: {filename_to_delete}")
                    error_count += 1
                    continue

                if os.path.exists(file_path_abs):
                    try:
                        os.remove(file_path_abs)
                        deleted_count += 1
                    except Exception as e:
                        error_count += 1
                        st.error(f"Gagal menghapus {filename_to_delete}: {e}")
                else:
                    st.warning(f"File {filename_to_delete} tidak ditemukan.")
                    error_count += 1

            if deleted_count > 0:
                st.success(f'{deleted_count} foto berhasil dihapus.')
            if error_count > 0:
                st.error(f'{error_count} foto gagal dihapus atau tidak ditemukan.')

            st.session_state.delete_mode = False
            st.session_state.selected_for_delete = set()
            st.rerun() # Refresh halaman setelah penghapusan
    elif st.session_state.delete_mode and not st.session_state.selected_for_delete:
        st.info("Pilih foto untuk mengaktifkan tombol hapus.")


# --- Footer ---
st.markdown("---")
st.markdown(
    f"""
    <div class="footer">
        <p>&copy; {datetime.now().year} Galeri WDF. Dibuat untuk Kenangan.</p>
    </div>
    """,
    unsafe_allow_html=True
)
