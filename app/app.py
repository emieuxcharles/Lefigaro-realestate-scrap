from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
import random
import pandas as pd
import json
import urllib.parse as urlparse

class Realestate():
    def __init__(self):
        self.announce_id = None
        self.script = None
        self.price = None
        self.name = None
        self.type = None
        self.link = None
        self.m2 = None
        self.postal_code = None
        self.address = None

def page_not_found(e):
    return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', **locals())


@app.route('/selenium-proxy-scrap/', methods=["GET", "POST"])
def seleniumProxyScrap():
    return render_template('selenium-proxy-scrap.html')

@app.route("/selenium-proxy-scrap/launch/", methods=['POST'])
def selogerScrapLaunch():
    URL = request.form['inputUrlSeLoger']
    PROXY = getProxy()
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--proxy-server=%s' % PROXY)

    driver = webdriver.Remote(
        command_executor='http://chrome:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME,
        options=options
    )

    driver.get(URL)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    return render_template('selenium-proxy-scrap.html', result=soup, proxy=PROXY);

@app.route('/proxy/', methods=["GET", "POST"])
def getProxy():
    reponse = requests.get('https://free-proxy-list.net/')
    proxy_list = pd.read_html(reponse.text)[0]
    proxy_list["url"] = "http://" + proxy_list['IP Address'] + ":" + proxy_list["Port"].astype(str)
    https_proxies = proxy_list[proxy_list["Https"] == "yes"]
    proxy_choice = random.choice(range(1,https_proxies['url'].count()))
    proxyvalue = proxy_list['url'][proxy_choice]
    # return render_template('proxy.html', proxyvalue=proxyvalue)
    return proxyvalue

@app.route('/simple-scrap/', methods=["GET", "POST"])
def simpleScrap():
    return render_template('simple-scrap.html')


@app.route("/simple-scrap/launch/", methods=['POST'])
def simpleScrapLaunch():
    realestates = []
    url = "https://immobilier.lefigaro.fr/annonces/immobilier-location-parking-france.html"
    # url = request.form['inputUrlSimple']
    realestate_type = request.form['realestate_type']
    page = requests.get(url)
    pagination = BeautifulSoup(page.content, "html.parser").select('.pagination-list>ol>li:last-of-type>a')[0]['href']
    parsed = urlparse.urlparse(pagination)
    nbpage = int(urlparse.parse_qs(parsed.query)['page'][0])
    for i in range(1, nbpage):
    # for i in range(1, 2):
        url = f"https://immobilier.lefigaro.fr/annonces/immobilier-location-parking-france.html?page={i}"
        # url = f"{url}page={i}"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser").select('.cartouche-liste')
        for realestate in soup:
            r = {}
            script = realestate.find('script').contents
            price = realestate.find_all("span", {"class": "price"})

            if len(script) > 0:
                json_script = json.loads(script[0]);

            r['announce_id'] = realestate.get('id').replace('list-item-', '')
            r['name'] = json_script['name'];
            r['link'] = json_script['url'];
            r['m2'] = json_script['floorSize']['value'];
            r['type'] = realestate_type;
            r['postal_code'] = json_script['address']['postalCode'].replace('F-', '')
            r['address'] = json_script['address']['addressLocality']
            r['price'] = price[0].contents[0].replace(' €', '');
            realestates.append(r)
    with open(f'output-{realestate_type}.json', 'w') as outfile:
        json.dump(realestates, outfile)
    realestates_number = len(realestates)
    return render_template('simple-scrap.html', realestates=realestates, realestates_number=realestates_number)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
