import streamlit as st
import os
from PIL import Image
import uuid
from datetime import datetime
from github import Github 
from dotenv import load_dotenv 

# Muat variabel lingkungan jika berjalan secara lokal
load_dotenv() 

# Konfigurasi GitHub dari environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_UPLOAD_PATH = "gallery_images" # Sub-direktori di repositori GitHub untuk gambar

# Pastikan semua variabel lingkungan diatur
if not all([GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME]):
    st.error("Error: Variabel lingkungan GITHUB_TOKEN, GITHUB_REPO_OWNER, atau GITHUB_REPO_NAME tidak diatur.")
    st.stop() 

# Inisialisasi GitHub API
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(GITHUB_REPO_OWNER).get_repo(GITHUB_REPO_NAME)
except Exception as e:
    st.error(f"Gagal terhubung ke repositori GitHub. Pastikan token dan detail repositori benar: {e}")
    st.stop()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
MAX_FILE_SIZE_MB = 32 # Max 32MB

st.set_page_config(
    page_title="🏕️ Galeri WDF",
    page_icon="📸",
    layout="wide", # Tetap "wide" agar konten bisa mengisi lebar, tapi kita batasi dengan CSS
    initial_sidebar_state="expanded"
)

# --- CSS Styling (Tambahkan Bagian Ini atau Modifikasi yang Sudah Ada) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1a1a1a; /* Dark background for the app */
        color: #e0e0e0; /* Light text color */
    }
    /* Mengontrol lebar kontainer utama aplikasi */
    section.main[data-testid="stSidebarContent"] + section.main {
        max-width: 900px; /* Lebar maksimal konten utama, sesuaikan sesuai kebutuhan */
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Streamlit's main header/sidebar container */
    .st-emotion-cache-nahz7x.e1nzilvr4 {
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
    
    .stImage > img { /* Target gambar di dalam st.image */
        height: 200px; /* Fixed height for consistency */
        object-fit: cover; /* Crop to fill */
        border-radius: 0.3rem;
    }
    /* Menghilangkan border dari kontainer Streamlit */
    .st-emotion-cache-nahz7x div.st-emotion-cache-1r6zp11.e1nzilvr1,
    .st-emotion-cache-nahz7x div.st-emotion-cache-1r6zp11.e1nzilvr1 > div {
        border: none !important;
        box-shadow: none !important;
    }
    .st-emotion-cache-nahz7x div.st-emotion-cache-1r6zp11.e1nzilvr1 > div > img {
        border: none !important;
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

if 'uploader_key_counter' not in st.session_state:
    st.session_state.uploader_key_counter = 0

uploaded_file_object = st.file_uploader(
    f"Pilih Foto (Max: {MAX_FILE_SIZE_MB}MB, Format: {', '.join(ALLOWED_EXTENSIONS)})",
    type=list(ALLOWED_EXTENSIONS),
    key=f"file_uploader_{st.session_state.uploader_key_counter}"
)

if uploaded_file_object is not None:
    if st.button("Unggah Foto", key="upload_button"):
        if uploaded_file_object.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"Ukuran file terlalu besar. Maksimal {MAX_FILE_SIZE_MB}MB.")
        elif not allowed_file(uploaded_file_object.name):
            st.error(f"Jenis file tidak diizinkan. Hanya: {', '.join(ALLOWED_EXTENSIONS)}.")
        else:
            original_filename = uploaded_file_object.name
            unique_id = uuid.uuid4().hex
            _, ext = os.path.splitext(original_filename)
            github_filename = f"{unique_id}{ext}" 
            github_filepath = f"{GITHUB_UPLOAD_PATH}/{github_filename}"

            try:
                repo.create_file(
                    path=github_filepath,
                    message=f"Upload {github_filename} from Streamlit app",
                    content=uploaded_file_object.getvalue(), 
                    branch="main" 
                )
                st.success("Foto berhasil diunggah ke Galeri WDF di GitHub! 📸")
                
                st.session_state.uploader_key_counter += 1
                st.rerun() 
            except Exception as e:
                st.error(f"Gagal mengunggah foto ke GitHub: {e}")
else:
    st.info("Pilih file di atas untuk mulai mengunggah.")

st.markdown("---")

# --- Bagian Galeri ---
st.header("Koleksi Foto")

image_files_github = []
try:
    contents = repo.get_contents(GITHUB_UPLOAD_PATH)
    for content_file in contents:
        if content_file.type == "file" and allowed_file(content_file.name):
            image_files_github.append(content_file.name)
    
    image_files_github.sort(reverse=True) 
    
except Exception as e:
    st.error(f"Gagal mengambil daftar foto dari GitHub: {e}")

if not image_files_github:
    st.info("Belum ada foto di Galeri WDF. Jadilah yang pertama mengunggah! 🌟")
else:
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

    num_cols = st.columns(1)[0].slider("Jumlah Kolom Tampilan", 1, 6, 4) 

    cols = st.columns(num_cols)
    col_idx = 0

    for image_name in image_files_github:
        with cols[col_idx]:
            image_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/{GITHUB_UPLOAD_PATH}/{image_name}"
            
            try:
                with st.container():
                    st.image(image_url, use_container_width=True) 

                    if st.session_state.delete_mode:
                        checkbox_key = f"delete_cb_{image_name}"
                        is_checked = image_name in st.session_state.selected_for_delete
                        
                        if st.checkbox(f"Pilih untuk hapus", value=is_checked, key=checkbox_key):
                            st.session_state.selected_for_delete.add(image_name)
                        else:
                            if image_name in st.session_state.selected_for_delete:
                                st.session_state.selected_for_delete.remove(image_name)

            except Exception as e:
                st.error(f"Tidak dapat memuat gambar {image_name} dari GitHub: {e}")
            
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
            type="primary"
        ):
            deleted_count = 0
            error_count = 0

            for filename_to_delete in st.session_state.selected_for_delete:
                github_filepath_to_delete = f"{GITHUB_UPLOAD_PATH}/{filename_to_delete}"
                try:
                    file_content = repo.get_contents(github_filepath_to_delete)
                    repo.delete_file(
                        path=file_content.path,
                        message=f"Delete {filename_to_delete} from Streamlit app",
                        sha=file_content.sha,
                        branch="main"
                    )
                    deleted_count += 1
                except Exception as e:
                    error_count += 1
                    st.error(f"Gagal menghapus {filename_to_delete} dari GitHub: {e}")

            if deleted_count > 0:
                st.success(f'{deleted_count} foto berhasil dihapus dari GitHub.')
            if error_count > 0:
                st.error(f'{error_count} foto gagal dihapus atau tidak ditemukan.')

            st.session_state.delete_mode = False
            st.session_state.selected_for_delete = set()
            st.rerun() 
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
