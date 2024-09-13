import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import os
from datetime import datetime
import requests
from PyPDF2 import PdfReader
import io
import boto3
from urllib.parse import urljoin, urlparse


def scrape_website(website):
    st.write("Launching chrome browser...")

    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(website)
        st.write("Page loaded...")
        html = driver.page_source
        time.sleep(10)

        return html
    finally:
        driver.quit()


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def extract_pdf_text(pdf_url):
    if not pdf_url.startswith(('http://', 'https://')):
        pdf_url = 'http://' + pdf_url
    response = requests.get(pdf_url)
    with io.BytesIO(response.content) as f:
        try:
            reader = PdfReader(f, strict=False)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""


def save_to_s3(content, website, bucket_name):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Scrape {today} - {website.replace('https://', '').replace('http://', '').replace('/', '_')}.txt"

    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=filename, Body=content)

    st.write(f"Content saved to S3 bucket '{bucket_name}' with key '{filename}'")


def list_s3_buckets():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    return buckets


def validate_url(url, base_url=None):
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        if base_url:
            url = urljoin(base_url, url)
        else:
            url = 'http://' + url
    return url


# Streamlit app
st.title("Web Scraper")

website = st.text_input("Enter the website URL to scrape:")
buckets = list_s3_buckets()
bucket_name = st.selectbox("Select the S3 bucket to save the content:", buckets)

if st.button("Scrape"):
    if website and bucket_name:
        website = validate_url(website)
        if website.endswith('.pdf'):
            st.write("PDF detected. Extracting text from PDF...")
            pdf_text = extract_pdf_text(website)
            save_to_s3(pdf_text, website, bucket_name)
            st.write("PDF scraping completed!")
        else:
            html_content = scrape_website(website)
            st.write("HTML content length:", len(html_content))  # Debug statement
            body_content = extract_body_content(html_content)
            st.write("Body content length:", len(body_content))  # Debug statement
            cleaned_content = clean_body_content(body_content)
            st.write("Cleaned content length:", len(cleaned_content))  # Debug statement

            # Check for PDF links and extract text if found
            soup = BeautifulSoup(html_content, "html.parser")
            pdf_links = [validate_url(a['href'], website) for a in soup.find_all('a', href=True) if
                         a['href'].endswith('.pdf')]
            for pdf_link in pdf_links:
                pdf_text = extract_pdf_text(pdf_link)
                cleaned_content += f"\n\nPDF Content from {pdf_link}:\n{pdf_text}"
                st.write(f"Extracted PDF text length from {pdf_link}:", len(pdf_text))  # Debug statement

            save_to_s3(cleaned_content, website, bucket_name)
            st.write("Scraping completed!")
    else:
        st.write("Please enter a valid URL and select an S3 bucket.")
