import csv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time

speciality = "généraliste"
zipcode = "75001"
num_doctors = 5

service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service)
driver.get("https://www.doctolib.fr")
wait = WebDriverWait(driver, 10)

try:
    reject_btn = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-disagree-button")))
    reject_btn.click()
except:
    pass

query_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")))
query_input.clear()
query_input.send_keys(speciality)

place_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))
place_input.clear()
place_input.send_keys(zipcode)
time.sleep(1)
place_input.send_keys(Keys.ARROW_DOWN)
place_input.send_keys(Keys.ENTER)

query_input.send_keys(Keys.ENTER)

time.sleep(5)

# Liste pour stocker les résultats
doctors_data = []

for i in range(1, 1 + num_doctors):
    try:
        name_selector = f"div.dl-card-variant-default:nth-child({i}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a:nth-child(1) > h2:nth-child(1)"
        sector_selector = f"div.dl-card:nth-child({i+2}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(2) > p:nth-child(1)"
        address_selector = f"div.dl-card:nth-child({i+2}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > p:nth-child(1)"
        city_postal_selector = f"div.dl-card:nth-child({i+2}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > p:nth-child(2)"
        
        name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name_selector)))
        sector_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sector_selector)))
        address_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, address_selector)))
        city_postal_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, city_postal_selector)))
        
        # Séparer code postal et ville
        city_postal = city_postal_elem.text.strip().split(' ', 1)
        postal_code = city_postal[0]
        city = city_postal[1] if len(city_postal) > 1 else ""
        
        doctors_data.append({
            "Nom complet": name_elem.text,
            "Secteur d'assurance": sector_elem.text,
            "Adresse": address_elem.text,
            "Ville": city,
            "Code postal": postal_code
        })
    except Exception as e:
        print(f"Médecin #{i} : données non trouvées ou hors page")

driver.quit()

# Écriture dans le fichier CSV
with open('docteurs.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Nom complet", "Secteur d'assurance", "Adresse", "Ville", "Code postal"])
    writer.writeheader()
    for doctor in doctors_data:
        writer.writerow(doctor)

print("Données exportées dans docteurs.csv")
