"""
Script - Extracts the mutation characteristics of a protein from marks.hms.harvard.edu/evmutation
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
import os

# Set parameters

start = 0  # Protein start number
end = 1  # Protein end number
timeout = 10 # Web timeout
output_file = 'output_s2_7.csv' # File that will collect the data
max_retries = 10 # How many retries if failing
retry_delay = 0.5 # How much time between retries
download_time = 3 # 2 # How much time to download csv file
search_load_time_all = 3 # 0.75 # How much time to retrieve data after search
download_path = 'C://Users//timothy//Downloads' # The path where the csv will get downloaded
mapped_accession = 'protein_pos_list.csv' # Input csv

names_list_full = []
names_list = []

# Retrieve all accession and phoshosite from the csv

with open(mapped_accession, 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        name = row[0]
        pos = row[1]
        names_list_full.append((name, pos))

# Open the output file

with open(output_file, 'a',newline='') as new_file:
    csv_writer = csv.writer(new_file)
    new_row = ['mapped_accession','mapped_phosphosite','mutant','pos','wt','subs','prediction_epistatic','prediction_independent','frequency','column_conservation']
    csv_writer.writerow(new_row)

# In case the accession is not available on the site, add a blank entry to the output

def blank_entry(output_file = output_file):
    with open(output_file, 'a',newline='') as new_file:
        csv_writer = csv.writer(new_file)
        new_row = [name_to_search, pos]
        csv_writer.writerow(new_row)

# As specified, the specific number of proteins will be selected.

names_list = names_list_full[start:end]

# Open a new web driver with Chrome. Open marks.hms.harvard.edu/evmutation/human_proteins.html

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, timeout)
driver.get("https://marks.hms.harvard.edu/evmutation/human_proteins.html")

# Retrieval is a bit slower in first iteration

first_iteration = True

for name_to_search, pos in names_list:

    if (first_iteration is True):
        first_iteration = False
        search_load_time = 5
    else:
        search_load_time = search_load_time_all
    # Divide the phosphosite into letter and number

    pattern = r'([A-Za-z]+)(\d+)'
    match = re.match(pattern, pos)
    if match:
        letter = match.group(1)
        number = match.group(2)
    print (name_to_search, pos)

    # We will try 'max_retries' no. of times to fetch the data.

    for _ in range (max_retries):
        try:

            # Enter the phosphosite into the search box

            search_box = driver.find_element(By.XPATH, '//*[@id="proteins_filter"]/label/input')
            search_box.clear()
            search_box.send_keys(name_to_search)

            # Wait for the results to load

            time.sleep (search_load_time)

            # Detect if there is no records

            no_match = driver.find_elements(By.XPATH, '//*[@id="proteins"]/tbody/tr/td')
            if ((no_match[0].text == "No data available in table") or (no_match[0].text == "No matching records found")):
                print ("No Match")
                blank_entry()

            else:

                # Find the total number of matching records retrieved
                
                tot_range = driver.find_element(By.XPATH, '//*[@id="proteins_info"]')
                tot_range = tot_range.text
                match = re.search('(\d+)\s+entries', tot_range)
                if match:
                    nos_entries = int(match.group(1))
                print ("Nos entries",nos_entries)

                found_file = False

                # Check each entry

                for i in range (1, nos_entries+1):

                    # Retrieve the range of values in that entry

                    next_range_path = '//*[@id="proteins"]/tbody/tr['+str(i)+']/td[3]'
                    sec_range = driver.find_element(By.XPATH,next_range_path)
                    sec_range = sec_range.text
                    min_range, max_range = map(int, sec_range.split('-'))

                    # Check if phosphosite range is within the entry range

                    if min_range > int(number) or int(number) > max_range:
                        print ('Not in range')
                    else:

                        print ('Match')
                        found_file = True

                        # Click the 'Mutations' link to download the csv.

                        mutat = '//*[@id="proteins"]/tbody/tr['+str(i)+']/td[10]/a[2]'                      
                        link = driver.find_element(By.XPATH, mutat)
                        csv_file_url = link.get_attribute('href')
                        csv_file_name = os.path.basename(csv_file_url)
                        link.click()

                        # Wait for the csv to download

                        time.sleep(download_time)

                        # Open the csv file to search for the phosphosite

                        download_dir = download_path 
                        csv_file_path = os.path.join(download_dir, csv_file_name)


                        with open(csv_file_path, 'r') as file:
                            csv_reader = csv.reader(file, delimiter=';')
                            next(csv_reader, None) # Skip header

                            # Seach each row for the phosphosite

                            found_row = False

                            for row in csv_reader:
                                if row[1] == number and row[2] == letter and row[3] == letter:

                                    # If found, copy the data to the output file

                                    found_row = True
                                    
                                    with open(output_file, 'a',newline='') as new_file:
                                        csv_writer = csv.writer(new_file)
                                        new_row = [name_to_search, pos] + row
                                        csv_writer.writerow(new_row)

                                    break

                            if not found_row:   #found_row = False
                                print("No matching row found.")
                                found_file = False
                            else:   # found_row = True
                                break
                                
                if not found_file:
                    print ("No file")
                    blank_entry()
                    break # Searched all the files, no more retries required

        except Exception as e:
            print ('Error. Retrying!', e)
            time.sleep (retry_delay)

        else:
            break # Search completed with no errors, no more retries required
    else:
        print ('Could not retrieve data!', name_to_search)

driver.close()

print ("Info collected, CSV Generated")
