import csv
import time
import argparse
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

parser = argparse.ArgumentParser(description="Recherche personnalisée sur Doctolib")

parser.add_argument("--speciality", type=str, required=True, help="Spécialité médicale (ex: généraliste)")
parser.add_argument("--zipcode", type=str, required=True, help="Code postal (ex: 75001)")
parser.add_argument("--max_results", type=int, default=5, help="Nombre maximum de médecins")
parser.add_argument("--start_date", type=str, help="Date de début (format JJ/MM/AAAA)")
parser.add_argument("--end_date", type=str, help="Date de fin (format JJ/MM/AAAA)")
parser.add_argument("--assurance", type=str, choices=["secteur 1", "secteur 2", "non conventionné"], help="Type d’assurance à filtrer")
parser.add_argument("--address_filter", type=str, help="Mot-clé pour filtrer l’adresse")
parser.add_argument("--exclude_address", action="store_true", help="Exclure les adresses contenant le mot-clé")

args = parser.parse_args()

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
query_input.send_keys(args.speciality)

place_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))
place_input.clear()
place_input.send_keys(args.zipcode)
time.sleep(1)
place_input.send_keys(Keys.ARROW_DOWN)
place_input.send_keys(Keys.ENTER)

query_input.send_keys(Keys.ENTER)
time.sleep(5)

doctor_data = []

for i in range(1, 1 + args.max_results):
    try:
        name_selector = f"div.dl-card-variant-default:nth-child({i}) h2"
        sector_selector = f"div.dl-card:nth-child({i+2}) div:nth-child(3) div:nth-child(2) > p:nth-child(1)"
        address_selector = f"div.dl-card:nth-child({i+2}) div:nth-child(2) div:nth-child(2) > p:nth-child(1)"
        city_postal_selector = f"div.dl-card:nth-child({i+2}) div:nth-child(2) div:nth-child(2) > p:nth-child(2)"
        rdv_selector = f"div.dl-card:nth-child({i+2}) span[class*='availabilities-slot'], div.dl-card:nth-child({i+2}) span[id^='slot']"

        name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name_selector)))
        sector_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sector_selector)))
        address_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, address_selector)))
        city_postal_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, city_postal_selector)))
        
        try:
            rdv_elem = driver.find_element(By.CSS_SELECTOR, rdv_selector)
            rdv_text = rdv_elem.text.strip()
        except:
            rdv_text = "Non disponible"

        city_postal = city_postal_elem.text.strip().split(' ', 1)
        postal_code = city_postal[0]
        city = city_postal[1] if len(city_postal) > 1 else ""

        if args.assurance and args.assurance.lower() not in sector_elem.text.lower():
            continue

        if args.address_filter:
            if args.exclude_address and args.address_filter.lower() in address_elem.text.lower():
                continue
            elif not args.exclude_address and args.address_filter.lower() not in address_elem.text.lower():
                continue

        if args.start_date and rdv_text != "Non disponible":
            try:
                rdv_date = datetime.strptime(rdv_text, "%a %d %b")
                rdv_date = rdv_date.replace(year=datetime.now().year)
                start = datetime.strptime(args.start_date, "%d/%m/%Y")
                if rdv_date < start:
                    continue
                if args.end_date:
                    end = datetime.strptime(args.end_date, "%d/%m/%Y")
                    if rdv_date > end:
                        continue
            except:
                pass

        doctor_data.append({
            "Nom complet": name_elem.text,
            "Secteur d'assurance": sector_elem.text,
            "Adresse": address_elem.text,
            "Ville": city,
            "Code postal": postal_code,
            "Date de RDV": rdv_text
        })
    except Exception as e:
        print(f"Médecin #{i} : données non trouvées ou hors page")

driver.quit()

with open('docteurs.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Nom complet", "Secteur d'assurance", "Adresse", "Ville", "Code postal", "Date de RDV"])
    writer.writeheader()
    for doctor in doctor_data:
        writer.writerow(doctor)

print("Données exportées dans docteurs.csv")
