#!/usr/bin/python3

from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

logging.basicConfig(filename='app.log', filemode='w', level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger().addHandler(logging.StreamHandler())


def get_additional_info(p_url: str):
    email = ''
    phone = ''
    site = ''
    a_url = p_url
    if not p_url.startswith('https://www.apsei.org.pt/'):
        a_url = 'https://www.apsei.org.pt/' + p_url
    if a_url != 'https://www.apsei.org.pt/associados/associados-empresas/':
        with requests.Session() as request:
            req_sub_link = request.get(a_url)
            if req_sub_link.status_code == 200:
                soup_sub_link = BeautifulSoup(req_sub_link.content, "html.parser")
                div_sub_link = soup_sub_link.find('div', {'class': 'associadoDetalheBox'})
                div_detail = div_sub_link.find('div', {"class": "right"})
                if div_sub_link is not None and div_detail is not None:
                    email = div_detail.find("a", href=re.compile(r"^mailto:"))['href']
                    if email is not None:
                        email = email.replace('mailto:', '')
                    site = div_detail.find("a", href=re.compile(r"^http"))['href']
                    if site == 'http://':
                        site = ''
                    phone = re.search(r"Tel: (.*?)<br />", req_sub_link.text)
                    if phone is not None:
                        phone = phone.group(0).replace('Tel: ', '').replace('<br />', '')
                    else:
                        phone = ''
    return email, phone, site


def process_empresas(p_url: str, p_filename: str):
    list_company_names = []
    list_cities = []
    list_emails = []
    list_phones = []
    list_sites = []

    with requests.Session() as request:
        req = request.get(p_url)
        if req.status_code == 200:
            soup = BeautifulSoup(req.content, "html.parser")
            div = soup.find('div', {"class": "list"})
            if div is not None:
                divs = div.find_all('div', {"class": "associadoBox"})
                for item in divs:
                    box = item.find('div', {"class": "associadoBoxRight"})
                    links = box.find_all('a', href=True)
                    list_company_names.append(links[0].text)
                    list_cities.append(links[1].text)
                    email, phone, site = get_additional_info(links[0]['href'])
                    list_emails.append(email)
                    list_phones.append(phone)
                    list_sites.append(site)
    df = pd.DataFrame(
        {
            'Name': list_company_names,
            'City': list_cities,
            'E-mail': list_emails,
            'Phone': list_phones,
            'Site': list_sites
        }
    )
    df.sort_values("Name", inplace=True)
    df.to_csv('output/{file_name}.csv'.format(file_name=p_filename), index=False, encoding='utf-8')
    with pd.ExcelWriter('output/{filename}.xlsx'.format(filename=p_filename)) as writer:
        df.to_excel(
            writer,
            engine='xlsxwriter',
            encoding='utf-8',
            index=False
        )


def process_observadores(p_url: str, p_filename: str):
    list_company_names = []
    list_emails = []
    list_phones = []
    list_sites = []

    with requests.Session() as request:
        req = request.get(p_url)
        if req.status_code == 200:
            soup = BeautifulSoup(req.content, "html.parser")
            div = soup.find('div', {"class": "whiteContent"})
            if div is not None:
                ul = div.find('ul')
                lis = ul.find_all('li')
                for item in lis:
                    links = item.find_all('a', href=True)
                    list_company_names.append(links[0].text)
                    email, phone, site = get_additional_info(links[0]['href'])
                    list_emails.append(email)
                    list_phones.append(phone)
                    list_sites.append(site)
    df = pd.DataFrame(
        {
            'Name': list_company_names,
            'E-mail': list_emails,
            'Phone': list_phones,
            'Site': list_sites
        }
    )
    df.sort_values("Name", inplace=True)
    df.to_csv('output/{file_name}.csv'.format(file_name=p_filename), index=False, encoding='utf-8')
    with pd.ExcelWriter('output/{filename}.xlsx'.format(filename=p_filename)) as writer:
        df.to_excel(
            writer,
            engine='xlsxwriter',
            encoding='utf-8',
            index=False
        )


if __name__ == '__main__':
    logging.info("Starting process...")

    start_time = datetime.now()
    try:
        process_empresas(p_url="https://www.apsei.org.pt/associados/associados-empresas/",
                         p_filename='apsei-empresas')
        process_observadores(p_url="https://www.apsei.org.pt/associados/associados-observadores/",
                             p_filename='apsei-observadores')

        logging.info('...done')
    except Exception as e:
        logging.error('An error has occurred. \n {}'.format(e))
    finally:
        logging.info('...ending process. Time slapsed {}.'.format((datetime.now() - start_time)))
