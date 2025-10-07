import streamlit as st
import mysql.connector
import hashlib
import time
import os
import plotly.express as px
import pandas as pd
import io
from cloudinary import uploader
from Cloudinary_utils import upload_to_cloudinary

caption = """Selamat datang di website prototype AnTik.
            website ini adalah perwujudan dari tugas akademis 🎓 yang dikembangkan oleh <b>Wira Triono</b> dari Prodi <b>STATISTIKA</b> Universitas Negeri Medan,
            untuk pemenuhan tugas Project Mata Kuliah <b>BASIS DATA DAN PENELUSURAN DATA-SQL</b>. Saya ucapkan terima kasih 
            atas kesempatan yang diberikan oleh dosen pengampu mata kuliah ini, Ibu <b>Sisti Nadia Amalia, S.Pd., M.Stat.</b>
            Harapannya project ini membantu terkhususnya mahasiswa dan dosen dari prodi STATISTIKA UNIMED untuk berkembang menjadi lebih baik lagi.
            Mohon diperhatikan bahwa website ini masih dalam tahap pengembangan awal (versi alfa) dan ditujukan untuk keperluan demonstrasi.
            Jadi tolong bagi siapapun yang berkunjung ke website ini, jadi lah dewasa dan gunakan dengan bijak!!!.
        """

if 'page' not in st.session_state:
    st.session_state.page = 'Home'
    st.session_state.logged_in = False

def go_to(page_name):
    st.session_state.page = page_name

def hash_password(pw):
    return hashlib.sha256(str.encode(pw)).hexdigest()

# fungsi untuk melihat info selengkapnya
def go_to_dataset_more(dataset_id):
    st.session_state.page = "dataset_more"
    st.session_state.selected_dataset_id = dataset_id

def go_to_komentar(q_id, q_judul):
    st.session_state.page = "komentar_pertanyaan"
    st.session_state.q_id = q_id
    st.session_state.q_judul = q_judul

def go_to_dataset_delete(dataset):
    st.session_state.dataset_delete = dataset
    st.session_state.page = "dataset_delete"

def go_to_dataset_update(dataset):
    st.session_state.dataset_update = dataset
    st.session_state.page = "dataset_update"

def go_to_pertanyaan_delete(q):
    st.session_state.pertanyaan_delete = q
    st.session_state.page = 'pertanyaan_delete'

# --- koneksi ke MySQL ---
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"])

# --- halaman utama ---
def home_page():
    st.title("📊 Project Basis Data 💻 Dashboard AnTik (Anak Statistik) ")
    st.markdown(f'<div style="text-align: justify;">{caption}</div>', unsafe_allow_html=True)
    st.caption("Seluruh hak cipta atas karya ini dimiliki oleh Wira Triono © 2025.")

    st.info(f"### Untuk Pengalaman Yang Lebih Interaktif Disarankan Membuka Dalam Mode Desktop")
    col1, col2, col3 = st.columns([4,4,2])
    col1.write("")
    col1.button("Login", use_container_width=True, type="primary", on_click=go_to, args=("Login",))
    col2.write("")
    col2.button("Register", use_container_width=True, on_click=go_to, args=("Register", ))

    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM users")
            jumlah = c.fetchone()[0]
            col3.metric("jumlah user aktif", jumlah)

def login_page():
    st.subheader("Login ke Akun")
    st.button("Kembali", on_click=go_to, args=("Home",), type='primary')

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    colLogin, colPass = st.columns([4,16])
    with colLogin:
        if st.button("Login", key="login"):
            # koneksi database |users|
            with get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("""
                        SELECT role FROM users 
                        WHERE username=%s AND password=%s
                        """,(username, hash_password(password)))
                    result = c.fetchone()
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = result[0]
                        st.success("Login berhasil!")
                        time.sleep(3)
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Username/Password salah!")
    with colPass:
        if st.button("Lupa Password", key='lupa_password'):
            go_to("lupa_password")
            st.rerun()
        
def register_page():
    st.title("Form Registrasi")
    st.button("Kembali", on_click=go_to, args=("Home", ), type='primary')

    def register_check():
        # Fase 1 : validasi ke aturan dasar
        register_rules = [
            (any(char.isdigit() for char in nama),              "⚠️ Nama tidak boleh mengandung angka"),
            (not nama.istitle(),                                "⚠️ Nama harus menggunakan huruf besar di awal tiap kata"),
            (not nama,                                          "⚠️ nama tidak boleh kosong"),
            (not no_id,                                         "⚠️ Nomor Identitas tidak boleh kosong!"),
            (no_id and not no_id.isdigit(),                     "⚠️ Nomor ID harus berupa angka!"),
            (email and ("@" not in email or "." not in email),  "⚠️ Format email tidak valid!"),
            (email and "unimed.ac.id" not in email.lower(),     "❌ email harus menggunakan domain UNIMED!"),
            (password_a != password_b,                          "🔑 password tidak sama"),
            (role == 'mahasiswa' and len(no_id) != 10,          "❌ Nomor ID mahasiswa (NIM) harus 10 digit!"),
            (role == 'dosen' and len(no_id) != 18,              "❌ Nomor ID dosen (NIP) harus 18 digit!"),
            (len(password_a) < 8,                               "🔑 Password minimal 8 karakter!")
        ]

        for condition, message in register_rules:
            if condition:
                st.error(message)
                return False

        # Fase 2 : validasi ke database
        # koneksi database |users|
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute("""
                    SELECT 1 FROM users 
                    WHERE id=%s OR username=%s OR email=%s
                    LIMIT 1
                    """, (no_id, username, email))
                if c.fetchone():
                    st.error("❌ Nomor ID, Username, atau Email sudah terdaftar!")
                    return False
                else :
                # Jika proses check valid
                    c.execute("""
                        INSERT INTO users (id, email, username, password, role)
                        VALUES (%s, %s, %s, %s, %s)
                        """, (no_id, email, username, hash_password(password_b), role))
                    if role == "mahasiswa":
                        c.execute("""
                            INSERT INTO mahasiswa (Nama, username, NIM, email, Status)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (nama, username, no_id, email, role))
                    elif role == "dosen":
                        c.execute("""
                            INSERT INTO dosen (Nama, NIP, username, email, Status)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (nama, no_id, username, email, role))
                    conn.commit()
                    return True
        
    with st.form(key="register_form"):
        nama = st.text_input(label="Nama", placeholder='huruf awal harus kapital (contoh : Wira Triono)')
        no_id = st.text_input(label = "Nomor Identitas (NIM atau NIP)")
        email = st.text_input(label = "Email", placeholder = "Harus Email Unimed (contoh : xxx@mhs.unimed.ac.id)")
        username = st.text_input(label = "Username")
        password_a = st.text_input(label = "password baru", type = "password")
        password_b = st.text_input(label = "konfirmasi password ", type = "password")
        role = st.selectbox(label = "Mendaftar sebagai", options=["mahasiswa", "dosen"])

        submitted = st.form_submit_button("Register")
    
    if submitted:
        if register_check():
            st.balloons()
            st.success("✅ Akun berhasil dibuat! Silakan login.")
   
def lupa_password():
    st.button("Kembali", on_click=go_to, args=("Home",), type='primary')

    with st.form(key="lupa_password"):
        username = st.text_input(label="username anda")
        email = st.text_input(label="email anda")
        no_id = st.text_input(label="No.Identitas anda (NIM/NIP)")
        
        # Tombol submit untuk form
        konfirmasi_id = st.form_submit_button("konfirmasi")

    if konfirmasi_id:
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute("""
                    SELECT 1 FROM users 
                    WHERE id=%s AND username=%s AND email=%s
                    """,(no_id, username, email))
                identitas_valid = c.fetchone()
                if identitas_valid:
                    st.success("Identitas terkonfirmasi! Silakan ganti password.")
                    with st.form(key="form_reset_password"):
                        password_a = st.text_input("Password baru", type='password')
                        password_b = st.text_input("Konfirmasi password", type='password')
                        submit_reset = st.form_submit_button("Reset Password")

                        if submit_reset:
                            if password_a != password_b:
                                st.error("Password tidak sama!")
                            elif len(password_a) < 8:
                                st.error("Password kurang dari 8 karakter")
                            else:
                                c.execute("""
                                    UPDATE users
                                    SET password = %s
                                    WHERE username = %s
                                    """, (hash_password(password_b), username))
                                conn.commit()
                                st.success("Password berhasil diubah!")
                                st.session_state.page = 'Home'
                                st.rerun()
                else :
                    st.error("Identitas tidak valid. Silakan cek Kembali data Anda.")

# --- halaman login ---
def Dashboard():
    status = st.session_state.role
    # tombol logout
    if st.button("Logout", type='primary'):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = 'Home'
        st.rerun()

    st.title("Dashboard")
    st.subheader(f"Selamat datang, {st.session_state.username}! 🎉")
    st.write("👉 Ini adalah halaman profil anda")

    # koneksi database > |datasets|users|mahasiswa|dosen|
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as c:
            # ambil semua dataset yang pernah di upload user
            c.execute("""
                SELECT * FROM datasets
                WHERE user_id = %s
                """, (st.session_state.username,))
            datasets_all = c.fetchall()

            c.execute("""
                SELECT * FROM pertanyaan
                WHERE user_id = %s
                """, (st.session_state.username,))
            pertanyaan_all = c.fetchall()

            if status == "mahasiswa":
                tabel, columns = "mahasiswa", ["Nama", "username", "NIM", "email", "Kelas", "Status", "Prodi", "Stambuk"]
            else:
                tabel, columns = "dosen", ["NIP", "Nama", "username", "email", "Prodi", "Jabatan_fungsional",	"Status"]

            # ambil data dari tabel
            c.execute(f"""
                SELECT * FROM {tabel} 
                WHERE username = %s
                """, (st.session_state.username,))
            data = c.fetchone()
            profil = pd.DataFrame([data], columns=columns)

    # Ubah ke format vertikal
    profil_final = profil.melt(var_name="Keterangan", value_name="Isi").set_index("Keterangan")
    st.dataframe(profil_final, use_container_width=True)

    col1, col2 = st.columns([3,6])
    col1.info("update biodata disini")
    col2.write('')
    col2.button("Update", type='primary', on_click=go_to, args=('update_dashboard',))

    col1, col2 = st.columns([11,10])
    with col1:
        st.title("DATASETS")
        for dataset in datasets_all:
            with st.container(border=True):
                st.markdown(f"#### 📄 {dataset['nama_data']}")
                col3, col4, col5 = st.columns(3)
                col3.button("✏️ UPDATE", key=f"upd_{dataset['id']}",
                               on_click=go_to_dataset_update, 
                               args=(dataset,))
                col4.button("🗑️ DELETE", key=f"dlt_{dataset['id']}",
                            on_click=go_to_dataset_delete, 
                            args=(dataset,))
                col5.metric("jumlah unduhan",dataset['unduh'])

    with col2:
        st.title("PERTANYAAN")
        for pertanyaan in pertanyaan_all:
            with st.container(border=True):
                st.markdown(f"#### {pertanyaan['judul']}")
                col1, col2, col3 = st.columns([2,3,3])
                col1.button("🔎 VIEW", key=f"view_Q_{pertanyaan['id']}",
                    on_click=go_to_komentar, args=(pertanyaan['id'],pertanyaan['judul']))
                col3.metric("terjawab", pertanyaan['penjawab'])
                col2.button("🗑️ DELETE", key=f"dlt_Q_{pertanyaan['id']}",
                            on_click=go_to_pertanyaan_delete,
                            args=(pertanyaan,))

def Datasets():
    st.title("🎉 Datasets Para AnTik")
    st.write("""✨ Di sini kamu bisa menyimpan data apapun itu seperti hasil kuesioner yang dimanipulasi 😂. 
                Daripada data tugas berakhir dan data dibuang begitu saja, tidak terpakai, lebih baik disimpan di sini,
                siapa tahu nanti bisa berguna lagi untuk mahasiswa, dosen atau penelitian lain! 📊""")
    col1, col2 = st.columns([6,1])
    col1.markdown("#### Ingin berkontribusi seperti mereka? Unggah data anda disini!")
    with col2:
        st.write("")
        st.button(f"**Unggah Data**", type="primary", on_click=go_to, args=('dataset_upload',))

    with get_connection() as conn:
        with conn.cursor(dictionary=True) as c:
            c.execute("""
                SELECT d.*, u.Nama AS author
                FROM datasets d
                LEFT JOIN (
                    SELECT username, Nama FROM mahasiswa
                    UNION
                    SELECT username, Nama FROM dosen
                ) u ON d.user_id = u.username""")
            datasets_all = c.fetchall()

    total_data = len(datasets_all)
    PER_PAGE = 8
    total_pages = total_data // PER_PAGE
    if total_data % PER_PAGE != 0:
        total_pages += 1

    # Pastikan minimal 1 halaman
    if total_pages == 0:
        total_pages = 1
    page = st.number_input("Pilih halaman", min_value=1, max_value=total_pages, value=1, step=1)
    start_idx = (page - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_data = datasets_all[start_idx:end_idx]

    for dataset in page_data:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                col3, col4 = st.columns([5,1])
                _, ext = os.path.splitext(dataset['file_path'])
                col3.subheader(f"📄 {dataset['nama_data']} \t\t\t ({ext})")
                col3.info(dataset['tags'])
                with col4:
                    st.metric("Jumlah Like", dataset['vote'])
                    st.button("👍", on_click=toggle_like, 
                              args=(st.session_state.username, dataset["id"]),
                              key=f"like_{dataset['id']}")
                with st.expander("Klik untuk melihat deskripsi data"):
                    st.text(dataset["deskripsi"])
            with col2:
                # Menampilkan author dan tanggal dengan format yang lebih baik
                st.success(f"**Author:** {dataset['author'].split()[0]} **Diunggah:** {dataset['tanggal']}")
                st.button("klik untuk info selengkapnya", 
                            key=f"more_{dataset['id']}",
                            on_click=go_to_dataset_more,
                            args=(dataset['id'],))

def Diskusi():
    st.title("Halaman Diskusi Para AnTik 🎉")
    st.info(f"### tenang 🤗, kamu anonim disini 🕵️‍♂️🕵️‍♀️")
    col1, col2 = st.columns([8,2])
    col1.markdown("#### Ingin bertanya atau berdiskusi? tidak perlu malu...")
    with col2:
        st.write("")
        st.button(f"**klik disini**", on_click=go_to, args=('halaman_pertanyaan',), type="primary")

    with get_connection() as conn:
        with conn.cursor(dictionary=True) as c:
            c.execute("SELECT * FROM pertanyaan")
            pertanyaan_all = c.fetchall()

    for q in pertanyaan_all:
        with st.container(border=True):
            colQ,colDate = st.columns([3,1])
            colQ.header(f"**{q['judul']}**")
            colDate.success(f"**Diunggah pada** {q['created_at']}")
            colDate.metric("jawaban", q['penjawab'])
            colQ.button("Lihat jawaban/ingin menjawab?", key=f"btn_{q['id']}",
                           on_click=go_to_komentar, args=(q['id'],q['judul'],))

# --- halaman cabang dari 4 halaman utama ---
def update_dashboard():
    st.subheader("Update Profil")
    status = st.session_state.role
    st.button("Kembali", on_click=go_to, args=('Dashboard',), type='primary')

    def profil_check():
        profil_rules = [
            (any(char.isdigit() for char in nama),   "Nama tidak boleh mengandung angka"),
            (not prodi.isupper(),                    "prodi harus berupa huruf besar"),
            (not nama.istitle(),                     "Nama harus menggunakan huruf besar di awal tiap kata")
        ]

        for condition, message in profil_rules:
            if condition:
                st.error(message)
                return False
            
        if status == "mahasiswa":
            if not kelas or not stambuk:
                st.error("Data kelas/stambuk kosong")
                return False
            if kelas[-3:-1] != str(stambuk)[-2:]:
                st.error(f"Data kelas tidak valid dengan stambuk {stambuk}")
                return False
            if len(str(nim)) != 10:
                st.error("❌ NIM harus 10 digit!")
                return False 
        elif status == "dosen":
            if not jabatan:
                st.error("Jabatan tidak boleh kosong")
                return False
            if len(str(nip)) != 18:
                st.error("❌ NIP harus 18 digit!")
                return False
        
        return True

    with st.form(key="profil_form"):
        nama = st.text_input(label="Nama", placeholder='huruf awal harus kapital (contoh : Wira Triono)')
        prodi = st.text_input(label="Prodi (harus huruf kapital)", placeholder="STATISTIKA, MATEMATIKA, ILMU KOMPUTER, DLL")
        
        if status == 'mahasiswa':
            stambuk = st.number_input("Stambuk", min_value=2021, max_value=2030, step=1, format="%d")
            nim = st.number_input("NIM", min_value=0, max_value=9999999999, step=1, format="%d")
            kelas = st.text_input(label="kelas", placeholder="PSPM22A, PSS23B, PSIK24C, dll..")
        elif status == "dosen":
            nip = st.text_input("NIP")
            jabatan = st.text_input("Jabatan fungsional")
        
        submitted_profil= st.form_submit_button("Update")
    
    if submitted_profil:
        if profil_check():
            with st.spinner("memproses data..."):
                with get_connection() as conn:
                    with conn.cursor() as c:
                        if status == "mahasiswa":
                            c.execute("""
                                UPDATE mahasiswa
                                SET Nama=%s, NIM=%s, Kelas=%s, Prodi=%s, Stambuk=%s
                                WHERE username=%s
                            """, (nama, nim, kelas, prodi, stambuk, st.session_state.username))
                        elif status == "dosen":
                            c.execute("""
                                UPDATE dosen
                                SET Nama=%s, NIP=%s, Prodi=%s, Jabatan_fungsional=%s
                                WHERE username=%s
                            """, (nama, nip, prodi, jabatan, st.session_state.username))

                        conn.commit()

                        st.success("Data berhasil diperbarui")
                        time.sleep(1)
                        go_to("Dashboard")
                        st.rerun()

def dataset_upload():
    st.subheader("Unggah Dataset")
    st.button("Kembali", on_click=go_to, args=('Datasets',), type='primary')

    def submitted_check():
        # Fase 1 : validasi ke aturan dasar
        submit_rules = [
            (not nama_data,         "⚠️ Judul Tidak Boleh Kosong"),
            (len(nama_data) > 50,   " ❌ Judul Maksimal 50 karakter!"),
            (not deskripsi,         "⚠️ Deskripsi tidak boleh kosong."),
            (file_path is None,     "⚠️ Anda belum mengunggah file dataset."),
            (not tags,              "⚠️ tag harus dipilih minimal 1")
        ]

        for condition, message in submit_rules:
            if condition:
                st.error(message)
                return False
            
        filename = file_path.name.lower()
        if not filename.endswith((".csv", ".json", ".xlsx", ".xls")):
            st.error("❌ Format harus csv, json, xlsx atau xls")
            return False

        return True

    all_tags = ["Kesehatan", "Keuangan", "Pendidikan", "Teknologi", "Sains Data", "Demografi",
                "Klasifikasi", "Regresi", "Clustering", "Spatial", "Time Series", "Inferensia"]

    with st.form(key="upload_form"):
        nama_data = st.text_input(
            label="Judul Dataset",
            placeholder="Contoh: Data Penjualan Ritel Selama Pandemi (min. 50 karakter)"
        )
        deskripsi = st.text_area(
            label="Deskripsi",
            placeholder="Jelaskan secara detail tentang dataset Anda. Apa konteksnya? Apa saja isi kolomnya? Dari mana sumber datanya?",
            height=200
        )
        file_path = st.file_uploader(
            label="Unggah File Dataset Anda",
            type=["csv", "json", "xlsx", "xls"],
            accept_multiple_files=False
        )
        tags = st.multiselect(
            label="Pilih tags yang relevan",
            options=all_tags,
            max_selections=3,
            placeholder="maksimal 3 tag"
        )
        
        # Tombol submit untuk form
        submitted_dataset = st.form_submit_button("Unggah Dataset")

    # --- Logika setelah tombol submit ditekan ---
    if submitted_dataset:
        if submitted_check():
            with st.spinner("Mengunggah dan memproses data..."):
                file_id = upload_to_cloudinary(file_path)
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO datasets (user_id, nama_data, deskripsi, file_path, tags, vote)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """, (st.session_state.username, nama_data, deskripsi, file_id, ",".join(tags), 0))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Data berhasil disimpan ke database")
                
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memproses file: {e}")

def dataset_update():
    dataset = st.session_state.dataset_update
    st.button("Kembali", on_click=go_to, args=("Dashboard", ), type='primary')

    all_tags = ["Kesehatan", "Keuangan", "Pendidikan", "Teknologi", "Sains Data", "Demografi",
                "Klasifikasi", "Regresi", "Clustering", "Spatial", "Time Series", "Inferensia"]

    with st.form(key="update_form"):
        nama_data = st.text_input(
            label="Judul Dataset",
            value=dataset.get("nama_data", "")
        )
        deskripsi = st.text_area(
            label="Deskripsi",
            value=dataset.get("deskripsi", ""),
            height=200
        )
        tags = st.multiselect(
            label="Pilih tags yang relevan",
            options=all_tags,
            max_selections=3,
            placeholder="maksimal 3 tag"
        )
        update_data = st.form_submit_button("Perbarui Dataset")

    if update_data:
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute("""
                    UPDATE datasets 
                    SET nama_data=%s, deskripsi=%s, tags=%s
                    WHERE id=%s
                    """, (nama_data, deskripsi, ",".join(tags), dataset["id"]))
                conn.commit()
        
        st.success("Dataset berhasil diperbarui!")
        del st.session_state.dataset_update
        st.session_state.page = 'Dashboard'
        st.rerun()

def dataset_delete():
    dataset = st.session_state.dataset_delete

    with st.form(key=f"delete_form_{dataset['id']}"):
        choice = st.radio(f"Apakah kamu yakin ingin menghapus dataset {dataset['nama_data']}?",
                          ["Batal", "Iya, hapus"])
        submitted = st.form_submit_button("Konfirmasi")

    if submitted:
        if choice == "Iya, hapus":
            # Hapus database
            with get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("DELETE FROM datasets WHERE id=%s", (dataset["id"],))
                    conn.commit()
            st.success(f"Dataset {dataset['nama_data']} berhasil dihapus")

            # Hapus Cloudinary
            try:
                uploader.destroy(dataset["file_path"])
                st.success(f"File {dataset['file_path']} berhasil dihapus dari Cloudinary")
                time.sleep(3)
            except Exception as e:
                st.warning(f"Gagal hapus file di Cloudinary: {e}")
        else:
            st.info("Dataset batal dihapus")

        # Hapus flag dan Kembali ke Dashboard
        del st.session_state.dataset_delete
        st.session_state.page = 'Dashboard'
        st.rerun()

def dataset_more():
    dataset_id = st.session_state.get("selected_dataset_id")

    conn = get_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT user_id, nama_data, file_path FROM datasets WHERE id = %s",
              (dataset_id,))
    dataset = c.fetchone()
    conn.close()

    st.button("Kembali", on_click=go_to, args=("Datasets",), type='primary')
    st.title(f"Dataset {dataset['nama_data']}")
    st.warning("halaman ini masih tahap pengembangan, jadi jika ada error atau bug hubungi saya (wira triono)")

    @st.fragment
    def read_data(parse=','):
        _, ext = os.path.splitext(dataset['file_path'])
        if ext.lower().endswith('.json'):
            df = pd.read_json(dataset['file_path'])
        elif ext.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(dataset['file_path'])
        elif ext.lower().endswith('.csv'):
            df = pd.read_csv(dataset['file_path'], sep=parse)
        return df, ext

    col1, col2, col3 = st.columns(3)
    delimiter = col1.selectbox("Pilih delimiter", [",", ";", "\t"], index=0)

    try :
        df, file_ext = read_data(parse=delimiter)
        page = col2.number_input("Halaman (1 halaman ada 50 data)", 
                            min_value=1, max_value=(len(df) // 50) + 1, step=1)

        date_col = col3.selectbox("Ubah Ke Datatime (opsional)", ["(none)"]+list(df.columns))
        if date_col != "(none)":
            try :
                df[date_col] = pd.to_datetime(df[date_col].astype(str))
            except :
                st.warning("⚠️ Gagal parsing kolom tanggal dengan format yang dipilih.")
        
        # Menampilkan data per halaman
        start_row = (page - 1) * 50
        end_row = start_row + 50
        st.dataframe(df.iloc[start_row:end_row], use_container_width=True)

        data, mime = toggle_unduh(df, file_ext, dataset_id)
        with st.container(border=True):
            coltxt, coldown = st.columns([11,2])
            coltxt.markdown("### Suka dengan data ini? klik untuk mengunduh")
            coldown.download_button(
                label="📥 unduh",
                data=data,
                file_name=f"{dataset['nama_data']}{file_ext}",
                on_click=increment_unduh,
                args=(dataset_id,dataset['user_id']),
                mime=mime)

        var = st.selectbox("Pilih variabel", df.columns)
        # Cek tipe data
        if pd.api.types.is_numeric_dtype(df[var]):
            # Jika numerik → histogram
            @st.fragment
            def var_1_grafik_num():
                stat_num = df[var].describe()
                cols = st.columns(4)  # 4 kolom
                for i, (label, value) in enumerate(stat_num.items()):
                    col = cols[i % 4]  # pindah kolom tiap index % 4
                    col.metric(label=label, value=round(value, 3))

                fig = px.histogram(df, x=var, nbins=25)
                st.plotly_chart(fig, use_container_width=True)
            var_1_grafik_num()

        else:
            @st.fragment
            def var_1_grafik_cat():
                colCat = st.columns([10,2])
                with colCat[0]:
                    # Jika kategorik → bar plot
                    counts = df[var].value_counts().reset_index()
                    counts.columns = [var, 'Jumlah']

                    fig = px.bar(counts,
                                x=var,
                                y='Jumlah')
                    st.plotly_chart(fig, use_container_width=True)

                with colCat[1]:
                    stat_cols_1 = st.columns(1)
                    stat_cols_2 = st.columns(1)
                    stat_cols_3 = st.columns(1)
                    stat_cols_4 = st.columns(1)
                    stat_col = stat_cols_1 + stat_cols_2 + stat_cols_3 + stat_cols_4
                    cat_stats = pd.DataFrame({"total": [len(df[var])],
                                            "jumlah kategori": [df[var].nunique()],
                                            "top frekuensi": counts[var].iloc[0],
                                            "top kategori": counts['Jumlah'].iloc[0]})
                    for col_name, col_value in cat_stats.iloc[0].items():
                        col = stat_col.pop(0)
                        col.metric(label=col_name, value=col_value, delta=None)
            var_1_grafik_cat()
        
        @st.fragment
        def var_2_grafik():
            colA, colB = st.columns(2)
            x_axis = colA.selectbox("Pilih kolom X", df.columns)
            y_axis = colB.selectbox("Pilih kolom Y", df.columns)

            colGraf, colOpsi = st.columns([12,3])
            # Step 4: Pilih jenis grafik
            with colOpsi:
                with st.container(border=True):
                    st.write("")
                    chart_type = st.radio("Pilih jenis grafik 2 variabel", ["Line", "Scatter"])
                    color_col = st.selectbox("Pilih kolom untuk warna (opsional)", [None] + list(df.columns))

            with colGraf:
                fig = None
                if chart_type == "Line":
                    fig = px.line(df, x=x_axis, y=y_axis, color=color_col if color_col else None)
                elif chart_type == "Scatter":
                    fig = px.scatter(df, x=x_axis, y=y_axis, color=color_col if color_col else None)
                elif chart_type == "Histogram (sumbu x)":
                    fig = px.histogram(df, x=x_axis, nbins=32, color=color_col if color_col else None)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        var_2_grafik()
    except :
        st.error("silahkan pilih delimiter yang ada agar tidak error")

@st.fragment
def toggle_unduh(df, file_ext, dataset_id):
    if file_ext == '.csv':
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        data = buf.getvalue()
        mime = "text/csv"
    elif file_ext in ['.xls','.xlsx']:
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        buf.seek(0)
        data = buf
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_ext == '.json':
        buf = io.StringIO()
        df.to_json(buf, orient='records', lines=True)
        data = buf.getvalue()
        mime = "application/json"

    return data, mime

def increment_unduh(dataset_id, pemilik):
    if st.session_state.username != pemilik:
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute("UPDATE datasets SET unduh = unduh + 1 WHERE id=%s", (dataset_id,))
                conn.commit()
    else :
        st.info("Kamu Masih Bisa Unduh Tapi Jumlah Unduh Tidak Bertambah Karena Mengunduh Datamu Sendiri")

def toggle_like(user_id, dataset_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT liked FROM votes 
                WHERE username=%s AND dataset_id=%s
                """, (user_id, dataset_id))
            row = c.fetchone()
            if row is None:
                # belum ada → insert baru dengan like=True
                c.execute("INSERT INTO votes (username, dataset_id, liked) VALUES (%s, %s, %s)",
                        (user_id, dataset_id, True))
                c.execute("UPDATE datasets SET vote = vote + 1 WHERE id=%s", (dataset_id,))
            else:
                liked = row[0]
                if liked:  # kalau sudah like → batalkan
                    c.execute("UPDATE votes SET liked=FALSE WHERE username=%s AND dataset_id=%s", (user_id, dataset_id))
                    c.execute("UPDATE datasets SET vote = vote - 1 WHERE id=%s", (dataset_id,))
                else:      # kalau belum like → like
                    c.execute("UPDATE votes SET liked=TRUE WHERE username=%s AND dataset_id=%s", (user_id, dataset_id))
                    c.execute("UPDATE datasets SET vote = vote + 1 WHERE id=%s", (dataset_id,))
            conn.commit()

def halaman_pertanyaan():
    st.button("Kembali", on_click=go_to, args=('Diskusi',), type='primary')
    st.subheader("Apa Yang Anda Bingungkan ?")

    with st.form(key="pertanyaan_form", clear_on_submit=True):
        pertanyaan = st.text_area(
            label="Pertanyaan",
            placeholder="Contoh: Bagaimana cara belajar Python?",
            height=200
        )
        # Tombol submit untuk form
        submitted_pertanyaan = st.form_submit_button("Unggah pertanyaan")
    
    if submitted_pertanyaan:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO pertanyaan (user_id, judul, penjawab) VALUES (%s, %s, %s)", 
                (st.session_state.username, pertanyaan, 0))
        conn.commit()
        conn.close()
        st.success("✅ berhasil diunggah")
        time.sleep(2)
        go_to("Diskusi")
        st.rerun()

def komentar_pertanyaan():
    q_id = st.session_state.q_id
    q_judul = st.session_state.q_judul

    st.button('Kembali', on_click=go_to, args=('Diskusi',), type='primary')

    with get_connection() as conn:
        with conn.cursor(dictionary=True) as c:
            c.execute("SELECT * FROM komentar WHERE pertanyaan_id = %s",(q_id,))
            jawaban_all = c.fetchall()
    
            st.title(q_judul)
            for Ans in jawaban_all:
                with st.container(border=True):

                    edit_key = f"edit_mode_{Ans['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    colA, colDate = st.columns([8,3])
                    colDate.success(f"**Diunggah pada** {Ans['created_at']}")
                    if Ans['user_id'] == st.session_state.username :
                        colEdit, colDelete = colDate.columns([3,4])
                        if colEdit.button("✏️ Edit", key=f"edit_{Ans['id']}"):
                            st.session_state[edit_key] = True
                            st.session_state[f"text_{Ans['id']}"] = Ans['komentar']
                        if colDelete.button("🗑️ Delete", key=f'delete_{Ans["id"]}'):
                            c.execute("DELETE FROM komentar WHERE id=%s", (Ans['id'],))
                            c.execute("UPDATE pertanyaan SET penjawab = penjawab - 1 WHERE id=%s", (q_id,))
                            conn.commit()
                            st.success("✅ Jawaban berhasil dihapus")
                            st.rerun()

                    if st.session_state[edit_key]:
                        new_text = colA.text_area("Edit jawaban:", value=st.session_state[f"text_{Ans['id']}"],
                                                key=f"text_area_{Ans['id']}")
                        save_col, cancel_col = colA.columns(2)
                        if save_col.button("💾 Simpan", key=f"save_{Ans['id']}"):
                            if new_text.strip():
                                c.execute("UPDATE komentar SET komentar=%s WHERE id=%s", (new_text, Ans['id']))
                                conn.commit()
                                st.success("✅ Jawaban berhasil diperbarui")
                                st.session_state[edit_key] = False
                                st.rerun()
                            else:
                                st.warning("⚠️ Jawaban tidak boleh kosong.")
                        if cancel_col.button("❌ Batal", key=f"cancel_{Ans['id']}"):
                            st.session_state[edit_key] = False
                            st.rerun()
                    else :
                        colA.markdown(f"#### anonim-{hash_password(Ans['user_id'])[::-1][::3][:4]}")
                        colA.markdown(f"{Ans['komentar']}")
            
            with st.form(key="form_jawaban", clear_on_submit=True):
                jawaban = st.text_area("Tulis jawaban Anda")
                submit_jwb = st.form_submit_button("Kirim")

            if submit_jwb:
                if not jawaban.strip():  # kosong atau hanya spasi
                    st.error("❌ Jawaban tidak boleh kosong!")
                else:
                    c.execute("""INSERT INTO komentar (pertanyaan_id, user_id, komentar)
                            VALUES (%s, %s, %s)""",(q_id, st.session_state.username, jawaban))
                    c.execute("UPDATE pertanyaan SET penjawab = penjawab + 1 WHERE id=%s", (q_id,))
                    conn.commit()
                    # proses simpan jawaban
                    st.success("Jawaban berhasil dikirim!")
                    time.sleep(2)
                    st.rerun()

def pertanyaan_delete():
    pertanyaan = st.session_state.pertanyaan_delete

    with st.form(key=f"delete_form_{pertanyaan['id']}"):
        choice = st.radio(f"Apakah kamu yakin ingin menghapus pertanyaan {pertanyaan['judul']}?",
                          ["Batal", "Iya, hapus"])
        submitted = st.form_submit_button("Konfirmasi")

    if submitted:
        if choice == "Iya, hapus":
            # Hapus database
            with get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("DELETE FROM pertanyaan WHERE id=%s", (pertanyaan["id"],))
                    conn.commit()
            st.success(f"pertanyaan anda berhasil dihapus")
        else:
            st.info("pertanyaan batal dihapus")

        # Hapus flag dan Kembali ke Dashboard
        del st.session_state.pertanyaan_delete
        st.session_state.page = 'Dashboard'
        st.rerun()

# --- Streamlit app ---
def main():
    # Halaman login
    if st.session_state.logged_in:
        login_menu = ["Dashboard", "Datasets", "Diskusi"]

        if st.session_state.page in login_menu:
            with st.sidebar:
                st.header(f"Selamat Datang, {st.session_state.username}!")
                choice = st.sidebar.selectbox(
                    "Pilih Menu", 
                    login_menu, 
                    index=login_menu.index(st.session_state.page),
                    key="navigation_choice"
                )

                if choice != st.session_state.page:
                    go_to(choice)

        if st.session_state.page == "Dashboard":
            Dashboard()
        elif st.session_state.page == "Datasets":
            Datasets()
        elif st.session_state.page == "dataset_upload":
            dataset_upload()
        elif st.session_state.page == "dataset_update":
            dataset_update()
        elif st.session_state.page == "dataset_delete":
            dataset_delete()
        elif st.session_state.page == 'dataset_more':
            dataset_more()

        elif st.session_state.page == 'Diskusi':
            Diskusi()
        elif st.session_state.page == 'halaman_pertanyaan':
            halaman_pertanyaan()
        elif st.session_state.page == 'komentar_pertanyaan':
            komentar_pertanyaan()
        elif st.session_state.page == 'pertanyaan_delete':
            pertanyaan_delete()
        elif st.session_state.page == 'update_dashboard':
            update_dashboard()


    # halaman utama
    else:
        if st.session_state.page == 'Home':
            home_page()
        elif st.session_state.page == 'Login':
            login_page()
        elif st.session_state.page == 'Register':
            register_page()
        elif st.session_state.page == 'lupa_password':
            lupa_password()

if __name__ == "__main__":

    main()

