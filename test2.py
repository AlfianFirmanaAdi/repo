import streamlit as st
import os
from PIL import Image # Penting untuk memproses gambar
import uuid
from datetime import datetime
from github import Github
from dotenv import load_dotenv
from io import BytesIO
import json
import base64

# Muat variabel lingkungan jika berjalan secara lokal
load_dotenv()

# Konfigurasi GitHub dari environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_UPLOAD_PATH = "gallery_images" # Sub-direktori di repositori GitHub untuk gambar
GITHUB_CAPTIONS_FILE = f"{GITHUB_UPLOAD_PATH}/captions.json" # Lokasi file captions.json

# --- Inisialisasi Session State Global (PENTING: Harus di awal script) ---
# Ini memastikan semua variabel session state ada sebelum digunakan oleh widget
if 'uploader_key_counter' not in st.session_state:
    st.session_state.uploader_key_counter = 0
if 'image_captions' not in st.session_state:
    st.session_state.image_captions = {} # Akan dimuat dari GitHub nanti
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'selected_for_edit' not in st.session_state:
    st.session_state.selected_for_edit = None
if 'delete_mode' not in st.session_state:
    st.session_state.delete_mode = False
# --- Akhir Inisialisasi Session State Global ---


# Pastikan semua variabel lingkungan diatur sebelum mencoba koneksi GitHub
if not all([GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME]):
    st.error("Error: Variabel lingkungan GITHUB_TOKEN, GITHUB_REPO_OWNER, atau GITHUB_REPO_NAME tidak diatur. Pastikan sudah ada di Streamlit Secrets (jika di-deploy) atau di file .env (jika lokal).")
    st.stop()

# Inisialisasi GitHub API
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(GITHUB_REPO_OWNER).get_repo(GITHUB_REPO_NAME)
    # Coba akses konten untuk memastikan koneksi dan repo valid
    # Ini akan memicu error jika repo atau path tidak ditemukan
    repo.get_contents(GITHUB_UPLOAD_PATH)
except Exception as e:
    st.error(f"Gagal terhubung ke repositori GitHub atau path '{GITHUB_UPLOAD_PATH}' tidak ditemukan. Pastikan token, detail repositori, dan folder '{GITHUB_UPLOAD_PATH}' di repo benar: {e}")
    st.info(f"Detail error: {type(e).__name__}: {e}")
    st.stop()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'} # HEIC tetap diizinkan untuk upload
MAX_FILE_SIZE_MB = 32 # Max 32MB

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Fungsi untuk Mengelola Caption di GitHub ---
# Fungsi-fungsi ini memuat/menyimpan caption ke/dari GitHub, dan menggunakan session_state.image_captions
def load_captions_from_github():
    """Memuat caption dari captions.json di GitHub."""
    try:
        contents = repo.get_contents(GITHUB_CAPTIONS_FILE)
        decoded_content = base64.b64decode(contents.content).decode('utf-8')
        return json.loads(decoded_content)
    except Exception as e:
        st.warning(f"Tidak dapat memuat captions.json dari GitHub atau file kosong/rusak. Menginisialisasi caption baru. Detail: {e}")
        return {}

def save_captions_to_github(captions_data):
    """Menyimpan caption ke captions.json di GitHub."""
    try:
        json_string = json.dumps(captions_data, indent=4)
        encoded_content = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

        try:
            contents = repo.get_contents(GITHUB_CAPTIONS_FILE)
            repo.update_file(
                path=GITHUB_CAPTIONS_FILE,
                message="Update captions.json from Streamlit app",
                content=encoded_content,
                sha=contents.sha, # SHA diperlukan untuk update
                branch="main"
            )
            st.success("Caption berhasil diperbarui di GitHub.")
        except Exception as e: # Buat file baru jika belum ada
            repo.create_file(
                path=GITHUB_CAPTIONS_FILE,
                message="Create captions.json from Streamlit app",
                content=encoded_content,
                branch="main"
            )
            st.success("Caption berhasil disimpan ke GitHub.")
    except Exception as e:
        st.error(f"Gagal menyimpan caption ke GitHub: {e}")
        st.exception(e)
# --- Akhir Fungsi Pengelola Caption ---

st.set_page_config(
    page_title="🏕️ Galeri WDF",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    section.main[data-testid="stSidebarContent"] + section.main {
        max-width: 900px;
        padding-left: 1rem;
        padding-right: 1rem;
    }
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
    /* Gaya spesifik untuk tombol hapus dan edit */
    .stButton[data-testid*="confirm_delete"] > button,
    .stButton[data-testid*="toggle_delete_mode"] > button {
        background-color: #dc3545;
    }
    .stButton[data-testid*="confirm_delete"] > button:hover,
    .stButton[data-testid*="toggle_delete_mode"] > button:hover {
        background-color: #bb2d3b;
    }
    .stButton[data-testid*="toggle_edit_mode"] > button { /* Gaya untuk tombol edit global */
        background-color: #ffc107;
        color: #212529;
    }
    .stButton[data-testid*="toggle_edit_mode"] > button:hover {
        background-color: #e0a800;
    }
    .stButton[data-testid*="cancel_delete_mode"] > button,
    .stButton[data-testid*="cancel_edit_mode"] > button,
    .stButton[data-testid*="cancel_add_photo"] > button { /* Gaya untuk batal */
        background-color: #6c757d;
    }
    .stButton[data-testid*="cancel_delete_mode"] > button:hover,
    .stButton[data-testid*="cancel_edit_mode"] > button:hover,
    .stButton[data-testid*="cancel_add_photo"] > button:hover {
        background-color: #5a6268;
    }

    .stAlert {
        color: #e0e0e0;
        background-color: #343a40;
        border-color: #495057;
    }

    .stImage > img {
        height: 200px;
        object-fit: cover;
        border-radius: 0.3rem;
    }
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

# --- Bagian Unggah Foto (Selalu Terlihat) ---
st.header("Unggah Foto Baru")
st.markdown("---") # Garis pemisah untuk kejelasan

# Input Caption
# Disable jika mode edit atau delete sedang aktif
upload_widgets_disabled = st.session_state.edit_mode or st.session_state.delete_mode
new_photo_caption = st.text_input("Tulis Caption untuk Foto Ini:", key="new_photo_caption_input", 
                                  disabled=upload_widgets_disabled)

# File Uploader
uploaded_file_object = st.file_uploader(
    f"Pilih Berkas Foto (Max: {MAX_FILE_SIZE_MB}MB, Format: {', '.join(ALLOWED_EXTENSIONS)})",
    type=list(ALLOWED_EXTENSIONS),
    key=f"file_uploader_new_photo_{st.session_state.uploader_key_counter}",
    disabled=upload_widgets_disabled
)

# Pesan untuk File HEIC
st.info("""
    **Catatan Penting untuk File HEIC (.heic):**
    Jika Anda mengunggah file `.HEIC` dan mengalami masalah (misalnya, gambar tidak muncul atau ada error),
    mohon konversi file `.HEIC` Anda ke format `.JPG` atau `.PNG` terlebih dahulu menggunakan aplikasi pengeditan foto
    atau konverter online sebelum mengunggahnya. Terima kasih!
""")

# Tombol Simpan Foto
if st.button("💾 Simpan Foto", key="save_photo_button", disabled=upload_widgets_disabled):
    if uploaded_file_object is None:
        st.error("Mohon pilih berkas foto sebelum menyimpan.")
    elif uploaded_file_object.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(f"Ukuran file terlalu besar. Maksimal {MAX_FILE_SIZE_MB}MB.")
    elif not allowed_file(uploaded_file_object.name):
        st.error(f"Jenis file tidak diizinkan. Hanya: {', '.join(ALLOWED_EXTENSIONS)}.")
    else:
        original_filename = uploaded_file_object.name
        unique_id = uuid.uuid4().hex
        base_name, ext = os.path.splitext(original_filename)

        content_to_upload = None
        file_mimetype = None

        if ext.lower() == '.heic':
            st.info("Mendeteksi file HEIC. Mencoba mengonversi ke JPEG...")
            try:
                img_bytes = uploaded_file_object.getvalue()
                
                try:
                    temp_img_info = Image.open(BytesIO(img_bytes))
                    st.info(f"Pillow berhasil mengidentifikasi file HEIC: {temp_img_info.format}, {temp_img_info.size}")
                    temp_img_info.close()
                except Exception as img_id_e:
                    st.warning(f"Pillow TIDAK dapat mengidentifikasi file HEIC sebagai gambar yang valid: {img_id_e}. Ini mungkin file rusak atau format tidak sepenuhnya didukung.")
                    st.stop()

                img = Image.open(BytesIO(img_bytes))
                output_buffer = BytesIO()
                img.save(output_buffer, format="jpeg", quality=90)
                output_buffer.seek(0)

                github_filename = f"{unique_id}.jpeg"
                content_to_upload = output_buffer.getvalue()
                file_mimetype = "image/jpeg"
                st.success("Konversi HEIC ke JPEG berhasil!")
            except Exception as e:
                st.error(f"Gagal memproses atau mengonversi file HEIC: {e}. Pastikan 'pillow-heif' terinstal dan file HEIC tidak rusak.")
                st.exception(e)
                st.stop()
        else:
            github_filename = f"{unique_id}{ext}"
            content_to_upload = uploaded_file_object.getvalue()
            file_mimetype = uploaded_file_object.type
            st.info(f"Mengunggah file {ext} asli.")

        if content_to_upload is None:
            st.error("Tidak ada konten yang siap untuk diunggah setelah pemrosesan.")
            st.stop()

        github_filepath = f"{GITHUB_UPLOAD_PATH}/{github_filename}"

        try:
            repo.create_file(
                path=github_filepath,
                message=f"Upload {github_filename} from Streamlit app",
                content=content_to_upload,
                branch="main"
            )
            st.success("Foto berhasil diunggah ke Galeri WDF di GitHub! 📸")
            
            st.session_state.image_captions[github_filename] = new_photo_caption
            save_captions_to_github(st.session_state.image_captions)

            st.session_state.uploader_key_counter += 1
            st.rerun()
        except Exception as e:
            st.error(f"Gagal mengunggah foto ke GitHub: {e}")
            st.exception(e)
st.markdown("---")


# --- Bagian Galeri ---
st.header("Koleksi Foto")

# Muat captions setelah GitHub API diinisialisasi
# Ini memastikan st.session_state.image_captions memiliki data yang sudah dimuat dari GitHub
# jika ada di awal skrip
if not st.session_state.image_captions: # Hanya muat jika belum ada data atau masih kosong
    st.session_state.image_captions = load_captions_from_github()

image_files_github = []
try:
    contents = repo.get_contents(GITHUB_UPLOAD_PATH)
    for content_file in contents:
        if content_file.type == "file" and allowed_file(content_file.name) and content_file.name != "captions.json":
            image_files_github.append(content_file.name)

    image_files_github.sort(reverse=True)

except Exception as e:
    st.error(f"Gagal mengambil daftar foto dari GitHub: {e}")
    st.info("Ini mungkin karena folder 'gallery_images' belum ada di repositori Anda, atau masalah izin/koneksi lainnya.")
    st.exception(e)

if not image_files_github:
    st.info("Belum ada foto di Galeri WDF. Jadilah yang pertama mengunggah! 🌟")
else:
    # --- Tombol Mode Hapus dan Edit ---
    # Menggunakan kolom dengan rasio untuk menempatkan tombol di kanan
    # [3] untuk kolom kosong yang mendorong, [1] untuk Pilih Hapus, [1] untuk Edit Caption
    col_gallery_actions = st.columns([3, 1, 1])
    
    with col_gallery_actions[2]: # Tempatkan Pilih Hapus di kolom kedua
        # Tombol Toggle Hapus
        if st.session_state.delete_mode:
            if st.button("🚫 Batal Hapus", key="cancel_delete_mode"):
                st.session_state.delete_mode = False
                st.session_state.selected_for_delete = set()
                st.rerun()
        else:
            # Disable jika mode edit aktif
            delete_button_disabled = st.session_state.edit_mode 
            if st.button("🗑️ Pilih Hapus", key="toggle_delete_mode", disabled=delete_button_disabled):
                st.session_state.delete_mode = True
                st.rerun()

    with col_gallery_actions[2]: # Tempatkan Edit Caption di kolom ketiga (paling kanan)
        # Tombol Toggle Edit
        if st.session_state.edit_mode:
            if st.button("↩️ Batal Edit", key="cancel_edit_mode"):
                st.session_state.edit_mode = False
                st.session_state.selected_for_edit = None
                st.rerun()
        else:
            # Disable jika mode hapus aktif
            edit_button_disabled = st.session_state.delete_mode 
            if st.button("✏️ Edit Caption", key="toggle_edit_mode", disabled=edit_button_disabled):
                st.session_state.edit_mode = True
                st.rerun()
    # Kolom pertama col_gallery_actions[0] akan kosong untuk mendorong tombol ke kanan


    # --- Tampilan Form Edit Caption Global ---
    if st.session_state.edit_mode and st.session_state.selected_for_edit:
        st.markdown("---")
        st.subheader(f"Edit Caption: {st.session_state.selected_for_edit}")
        
        current_caption_for_edit = st.session_state.image_captions.get(st.session_state.selected_for_edit, "Tidak ada caption")
        new_caption_edit_global = st.text_input(
            "Tulis Caption Baru:",
            value=current_caption_for_edit,
            key=f"edit_caption_global_input"
        )
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("✅ Simpan Perubahan", key="save_edited_caption_global"):
                st.session_state.image_captions[st.session_state.selected_for_edit] = new_caption_edit_global
                save_captions_to_github(st.session_state.image_captions)
                st.session_state.edit_mode = False
                st.session_state.selected_for_edit = None
                st.rerun()
        with col_cancel:
            if st.button("❌ Batal", key="cancel_edit_caption_global"):
                st.session_state.edit_mode = False
                st.session_state.selected_for_edit = None
                st.rerun()
        st.markdown("---")

    # Pesan mode
    if st.session_state.delete_mode:
        st.warning("Pilih foto yang ingin Anda hapus. Klik lagi untuk membatalkan pilihan.")
    elif st.session_state.edit_mode and not st.session_state.selected_for_edit:
        st.info("Pilih satu foto untuk mengedit caption-nya.")
    elif st.session_state.edit_mode and st.session_state.selected_for_edit:
        st.info(f"Anda sedang mengedit caption untuk: {st.session_state.selected_for_edit}")

    num_cols = st.columns(1)[0].slider("Jumlah Kolom Tampilan", 1, 6, 4)

    cols = st.columns(num_cols)
    col_idx = 0

    for image_name in image_files_github:
        with cols[col_idx]:
            image_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/{GITHUB_UPLOAD_PATH}/{image_name}"
            
            try:
                with st.container():
                    st.image(image_url, use_container_width=True)

                    current_caption = st.session_state.image_captions.get(image_name, "Tidak ada caption")
                    st.markdown(f"**Caption:** {current_caption}")

                    if st.session_state.delete_mode:
                        checkbox_key = f"delete_cb_{image_name}"
                        is_checked = image_name in st.session_state.selected_for_delete
                        
                        if st.checkbox(f"Pilih untuk hapus", value=is_checked, key=checkbox_key):
                            st.session_state.selected_for_delete.add(image_name)
                        else:
                            if image_name in st.session_state.selected_for_delete:
                                st.session_state.selected_for_delete.remove(image_name)
                    elif st.session_state.edit_mode:
                        radio_key = f"select_edit_{image_name}"
                        if st.radio("Pilih Foto Ini", (image_name, ), key=radio_key, index=None):
                            st.session_state.selected_for_edit = image_name
                            st.rerun()
            except Exception as e:
                st.error(f"Tidak dapat memuat gambar {image_name} dari GitHub: {e}")
                st.exception(e)

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
                    if filename_to_delete in st.session_state.image_captions:
                        del st.session_state.image_captions[filename_to_delete]
                    deleted_count += 1
                except Exception as e:
                    error_count += 1
                    st.error(f"Gagal menghapus {filename_to_delete} dari GitHub: {e}")
                    st.exception(e)

            save_captions_to_github(st.session_state.image_captions)

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
