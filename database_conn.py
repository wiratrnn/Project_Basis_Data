import mysql.connector

# Koneksi ke Railway
connection = mysql.connector.connect(
    host="tramway.proxy.rlwy.net",
    user="root",
    password="RukrkWdGZrOQebAgpykbSNKNDVTehLus",
    database="railway",
    port=47812
)

cursor = connection.cursor()
cursor.execute("SHOW TABLES;")

tables = cursor.fetchall()
print(tables)

# # Baca seluruh isi file SQL
# with open(r"C:\Users\user\Downloads\project_db.sql", "r", encoding="utf-8") as f:
#     sql_script = f.read()

# # Eksekusi setiap statement satu per satu
# statements = sql_script.split(';')

# for statement in statements:
#     statement = statement.strip()
#     # Lewati baris kosong atau komentar
#     if statement and not statement.startswith('--') and not statement.startswith('/*'):
#         try:
#             cursor.execute(statement)
#         except mysql.connector.Error as e:
#             print(f"⚠️ Error di statement: {statement[:100]}...")
#             print(e)

# connection.commit()
# cursor.close()
# connection.close()

# print("✅ Database berhasil diupload ke Railway!")

