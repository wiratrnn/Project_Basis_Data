import streamlit as st
import cloudinary
import cloudinary.uploader

def configure_cloudinary():
    cloudinary.config(
        cloud_name = st.secrets.cloudinary.cloud_name, 
        api_key = st.secrets.cloudinary.api_key, 
        api_secret = st.secrets.cloudinary.api_secret,
        secure = True
    )
    return True

def upload_to_cloudinary(uploaded_file):
    if not configure_cloudinary():
        return None

    upload_result = cloudinary.uploader.upload(
        uploaded_file.getbuffer(),
        resource_type="raw",
        public_id=uploaded_file.name 
    )
    
    secure_url = upload_result.get('secure_url')
    return secure_url

