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
    /* Menggunakan kelas yang lebih spesifik untuk mencegah konflik */
    .st-emotion-cache-nahz7x.e1nzilvr4 { /* Streamlit's main header/sidebar container */
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
    /* Gaya untuk semua tombol Streamlit */
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
    /* Gaya spesifik untuk tombol hapus */
    .stButton[data-testid="stButton-confirm_delete"] > button,
    .stButton[data-testid="stButton-toggle_delete_mode"] > button {
        background-color: #dc3545; /* Merah untuk hapus */
    }
    .stButton[data-testid="stButton-confirm_delete"] > button:hover,
    .stButton[data-testid="stButton-toggle_delete_mode"] > button:hover {
        background-color: #bb2d3b;
    }
    .stButton[data-testid="stButton-cancel_delete_mode"] > button {
        background-color: #6c757d; /* Abu-abu untuk batal */
    }
     .stButton[data-testid="stButton-cancel_delete_mode"] > button:hover {
        background-color: #5a6268;
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

# Inisialisasi session state untuk file uploader jika belum ada
if 'uploader_key_counter' not in st.session_state:
    st.session_state.uploader_key_counter = 0
# Inisialisasi session state untuk deskripsi gambar jika belum ada
if 'image_descriptions' not in st.session_state:
    st.session_state.image_descriptions = {}

uploaded_file_object = st.file_uploader(
    f"Pilih Foto (Max: {MAX_FILE_SIZE_MB}MB, Format: {', '.join(ALLOWED_EXTENSIONS)})",
    type=list(ALLOWED_EXTENSIONS),
    key=f"file_uploader_{st.session_state.uploader_key_counter}" # Gunakan key dinamis
)

# Tombol Unggah terpisah untuk mengontrol proses penyimpanan
if uploaded_file_object is not None:
    if st.button("Unggah Foto", key="upload_button"):
        if uploaded_file_object.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"Ukuran file terlalu besar. Maksimal {MAX_FILE_SIZE_MB}MB.")
        elif not allowed_file(uploaded_file_object.name):
            st.error(f"Jenis file tidak diizinkan. Hanya: {', '.join(ALLOWED_EXTENSIONS)}.")
        else:
            # Simpan file dengan nama unik (UUID)
            original_filename = uploaded_file_object.name
            unique_id = uuid.uuid4().hex # Gunakan seluruh UUID untuk keunikan maksimal
            _, ext = os.path.splitext(original_filename) # Ambil hanya ekstensi dari nama asli
            unique_filename = f"{unique_id}{ext}" # Nama file hanya UUID + ekstensi
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file_object.getbuffer())
                
                # Inisialisasi deskripsi untuk gambar yang baru diunggah
                st.session_state.image_descriptions[unique_filename] = "" 
                
                st.success("Foto berhasil diunggah ke Galeri WDF! 📸")
                
                # Increment counter untuk mereset file uploader pada rerun berikutnya
                st.session_state.uploader_key_counter += 1
                st.rerun() # Refresh halaman untuk menampilkan foto baru
            except Exception as e:
                st.error(f"Gagal mengunggah foto: {e}")
else:
    st.info("Pilih file di atas untuk mulai mengunggah.")


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
    
    # Sinkronisasi deskripsi: hapus deskripsi untuk file yang tidak ada lagi
    # Dan inisialisasi deskripsi kosong untuk file baru jika ada
    current_files_set = set(image_files)
    st.session_state.image_descriptions = {
        k: v for k, v in st.session_state.image_descriptions.items()
        if k in current_files_set
    }
    for img_file in image_files:
        if img_file not in st.session_state.image_descriptions:
            st.session_state.image_descriptions[img_file] = "" # Inisialisasi deskripsi kosong untuk gambar baru

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
    # Slider untuk jumlah kolom responsif
    num_cols = st.columns(1)[0].slider("Jumlah Kolom Tampilan", 1, 6, 4) 

    # Tampilkan gambar dalam grid
    cols = st.columns(num_cols)
    col_idx = 0

    for image_name in image_files:
        with cols[col_idx]:
            file_path = os.path.join(UPLOAD_FOLDER, image_name)
            try:
                img = Image.open(file_path)
                
                with st.container(border=True): # Menggunakan border=True untuk tampilan seperti kartu
                    # Perbaikan: Mengganti use_column_width dengan use_container_width
                    # Menampilkan gambar tanpa caption default
                    st.image(img, use_container_width=True) 

                    # Input teks untuk deskripsi
                    current_description = st.session_state.image_descriptions.get(image_name, "")
                    new_description = st.text_input(
                        "Deskripsi:",
                        value=current_description,
                        key=f"description_{image_name}" # Kunci unik untuk setiap input
                    )
                    # Perbarui deskripsi jika ada perubahan
                    if new_description != current_description:
                        st.session_state.image_descriptions[image_name] = new_description
                        st.rerun() # Rerun untuk memperbarui tampilan (opsional, bisa juga tanpa rerun jika tidak ada efek samping besar)

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
                        # Hapus deskripsi terkait dari session state
                        if filename_to_delete in st.session_state.image_descriptions:
                            del st.session_state.image_descriptions[filename_to_delete]
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
