"""
Script - using a gene name of a protein (uniprot.org), find its abundance (pax-db.org)
"""

import csv
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re


# Set parameters

start = 0  # Protein start number
end = 1  # Protein end number
timeout = 10  # Web timeout
output_file = 'output10ss7.csv' # File that will collect the data
max_retries = 10 # How many retries if failing
retry_delay = 1 # How time between retries


names_list_full = []
names_list = []
genes_list = []
abund_list = []
data_list = []

# Retrieve all protein names from the csv

with open('protein_names.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        name = row[0]
        names_list_full.append(name)

# As specified, the specific number of proteins will be selected.

names_list = names_list_full[start:end]

# Open a new web driver with Chrome. Open uniprot.org

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, timeout)
driver.get("https://uniprot.org")

first_iteration = True  # In the first iteration, the search box is different

previous = None

for name_to_search in names_list:


    if (previous is not None) and (name_to_search == previous):
            print ('Loading previous value..')
            pass
    else:

            previous = name_to_search

            # Find the search box

            if first_iteration:
                search_box = '//*[@id="root"]/div[1]/div/main/div/div[1]/div/section/form/div[2]/input'
                first_iteration = False
            else:
                search_box = '//*[@id="root"]/div[1]/header/div/div[3]/section/form/div[2]/input'
            search_input = driver.find_element(By.XPATH, search_box)

            # Input the name into the search field

            search_input.clear()
            search_input.send_keys(name_to_search)
            search_input.send_keys(Keys.RETURN)
            wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div/div/main/ul/li[2]/div/div[2]/strong')))

            # Collect the name of the protein

            gene = driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/main/ul/li[2]/div/div[2]/strong')
            gene_name = gene.text

    print(name_to_search, '-', gene_name)
    genes_list.append(gene_name)

# Next, we will connect to pax-db.org

first_iteration = True

driver.get("https://pax-db.org/")

for name_to_search in genes_list:

    #Testing
    print (name_to_search)

    # Select homo sapien option

    if first_iteration == True:
        homo_box = driver.find_element(By.XPATH, '//*[@id="search_container"]/div[1]/div/div/div/span/input[2]')
        homo_box.click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="search_container"]/div[1]/div/div/div/span/div/div/div[1]')))
        sapien = driver.find_element(By.XPATH, '//*[@id="search_container"]/div[1]/div/div/div/span/div/div/div[1]')
        sapien.click()

    if first_iteration:

        previous = None
        first_iteration = False

    if (previous is not None) and (name_to_search == previous):
                    print ('Loading previous value..')
                    pass
    else:

        # Type gene name in search box

        wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="search_container"]/div[2]/div/label/div/div[1]/div[2]')))
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_container"]/div[2]/div/label/div/div[1]/div[2]')))

        div_box = driver.find_element(By.XPATH, '//*[@id="search_container"]/div[2]/div/label/div/div[1]/div[2]')
        div_box.click()
        search_box = driver.find_element(By.XPATH,
                                        '/html/body/div[1]/div/header/div[2]/div[2]/div/label/div/div[1]/div[2]/textarea')
        for i in range(10):
            search_box.send_keys(Keys.BACKSPACE)
        search_box.send_keys(name_to_search)

        # Click search

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="search_container"]/div[2]/div/label/div/div[1]/div[3]/i')))
        search_button = driver.find_element(By.XPATH, '//*[@id="search_container"]/div[2]/div/label/div/div[1]/div[3]/i')
        search_button.click()
        time.sleep(2)

        # Not repeating for previous values



        # Doing max retries number of times to find the data

        for _ in range (max_retries):
            try:


                

                    # Check if search options has been loaded (i.e. not exact match)

                    search_res = driver.find_elements(By.XPATH, '/html/body/div[1]/div/div/main/div/div/div[1]/h3')
                    if search_res:
                        first_option = driver.find_element(By.XPATH, '//*[@id="q-app"]/div/div/main/div/div/div[2]/div/div/div[1]/h4/a')
                        first_option.click()

                    # Find 'whole organism'

                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="q-app"]/div/div/main/div/div[2]/div/div[1]/table/tbody/tr[1]/td[3]')))
                    whole = driver.find_element(By.XPATH, '//*[@id="q-app"]/div/div/main/div/div[2]/div/div[1]/table/tbody/tr[1]/td[2]')

                    # Collect abundance values

                    #if whole.text == 'whole organism':
                    abund = driver.find_element(By.XPATH,
                                                '//*[@id="q-app"]/div/div/main/div/div[2]/div/div[1]/table/tbody/tr[1]/td[3]')
                    pattern = r'(\d+(\.\d+)? ppm)'
                    match = re.search(pattern, abund.text)
                    abund_score = match.group()

                    # Collect Dataset score

                    dataset = driver.find_element(By.XPATH,
                                                    '//*[@id="q-app"]/div/div/main/div/div[2]/div/div[1]/table/tbody/tr[1]/td[4]')
                    dataset_score = dataset.text

            
            except Exception as e:
                print ('Error. Retrying!')
                #time.sleep (retry_delay)
            else:
                break
        else:
            print ('Could not retrieve data!', name_to_search)

    previous = name_to_search
    print(abund_score, ', ', dataset_score)
    abund_list.append(abund_score)
    data_list.append(dataset_score)

driver.close()

# Move all the collected data into a csv file.

column_headers = ['mapped_accession', 'Gene_Name', 'Abundance', 'Dataset Score']
csv_file = output_file

#print (len(names_list), len(genes_list), len(abund_list), len(data_list))

with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(column_headers)
    for row in zip(names_list, genes_list, abund_list, data_list):
        writer.writerow(row)

print(f'Info Collected, CSV file generated')
