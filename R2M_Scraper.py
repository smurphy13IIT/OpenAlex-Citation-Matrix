from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import base64
from functions import json_to_csv
import os
import pandas as pd

root_dir = "C:/Users/smurphy13/PycharmProjects/Marketing Citation Matrix/R2M Data"
jom_dir = root_dir + "/Articles"
images_dir = root_dir + "/Topic_Images"

paths = os.walk(jom_dir)

articles = []

csv_filename = root_dir + "/R2M_data"

df = pd.DataFrame()

"""Set up the browser driver."""
service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

"""Open a Chrome browser instance."""
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[0])

driver.get('https://www.r2mindex.com/score.html')
time.sleep(1)

for decade in os.listdir(jom_dir):
    decade_dir = jom_dir + "/" + decade
    for year in os.listdir(decade_dir):
        year_dir = decade_dir + "/" + year

        if int(year) >= 1982:
            for issue in os.listdir(year_dir):
                issue_dir = year_dir + "/" + issue
                for article in os.listdir(issue_dir):
                    article_path = issue_dir + "/" + article
                    article_data = {
                        'pub_year': year,
                        'issue': issue,
                        'article': article,
                        'R2M_score': '',
                        'percentile': '',
                        'image_path': ''
                    }

                    """Set up input data."""
                    pub_year = year
                    pdf_path = article_path

                    driver.get('https://www.r2mindex.com/score.html')

                    input_pub_year = driver.find_element("xpath", '/html/body/div[2]/div/form/div[1]/input')
                    input_article_pdf = driver.find_element("xpath", '/html/body/div[2]/div/form/div[2]/span/input')

                    input_pub_year.send_keys(pub_year)
                    input_article_pdf.send_keys(pdf_path)

                    btn_submit = driver.find_element("xpath", '/html/body/div[2]/div/form/div[3]/button')
                    btn_submit.click()
                    time.sleep(3)

                    btn_show_full_results = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[1]/button')
                    btn_show_full_results.click()
                    time.sleep(.2)

                    r2m_score_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[1]/h1[2]')
                    r2m_score = r2m_score_element.text
                    article_data['R2M_score'] = r2m_score

                    percent_score_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[1]/div[2]/p')
                    percent_score = percent_score_element.text[64:68]
                    article_data['percentile'] = percent_score

                    image_element = driver.find_element("xpath", '/html/body/div[2]/div/div/div[2]/div[1]/div/canvas')
                    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/jpg').substring(22);", image_element)
                    canvas_image_data = base64.b64decode(canvas_base64)
                    image_filename = f"topics_{pub_year}_{issue}_{os.path.splitext(article)[0]}.jpg"
                    image_path = root_dir + "/Topic_Images/" + image_filename
                    article_data['image_path'] = image_filename
                    with open(image_path, 'wb') as file:
                        file.write(canvas_image_data)

                    articles.append(article_data)

                    temp_df = pd.DataFrame([article_data])
                    df = pd.concat([df, temp_df], ignore_index=True)
                    df.to_csv(csv_filename + ".csv", index=False, mode='w')

                    print(article_data)

driver.quit()

json_to_csv(articles, csv_filename)