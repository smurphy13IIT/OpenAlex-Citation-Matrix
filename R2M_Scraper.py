from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import base64
import pandas as pd

"""Set up the browser driver."""
service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

"""Set up input data."""
pub_year = 2010
pdf_path = "C:/Users/Sean IIT/PycharmProjects/OpenAlex-Marketing/Park-BrandAttachmentBrand-2010.pdf"

"""Open a Chrome browser instance."""
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])

driver.get('https://www.r2mindex.com/score.html')
time.sleep(1)

input_pub_year = driver.find_element("xpath", '/html/body/div[2]/div/form/div[1]/input')
input_article_pdf = driver.find_element("xpath", '/html/body/div[2]/div/form/div[2]/span/input')

input_pub_year.send_keys(pub_year)
input_article_pdf.send_keys(pdf_path)

btn_submit = driver.find_element("xpath", '/html/body/div[2]/div/form/div[3]/button')
btn_submit.click()
time.sleep(1)

btn_show_full_results = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[1]/button')
btn_show_full_results.click()
time.sleep(.5)

r2m_score_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[1]/h1[2]')
r2m_score = r2m_score_element.text
print(r2m_score)

percent_score_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[2]/p')
percent_score = percent_score_element.text[64:68]
print(percent_score)

image_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[2]/div[1]/div/canvas')
canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/jpg').substring(22);", image_element)
canvas_image_data = base64.b64decode(canvas_base64)

with open('image.jpg', 'wb') as file:
    file.write(canvas_image_data)

time.sleep(1)

driver.close()
driver.quit()