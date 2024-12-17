import scrapy
from urllib.parse import urlparse
import pandas as pd
import os

class EnlacesSpider(scrapy.Spider):
    name = 'enlaces'
    start_urls = []
    seen_links = set()
    all_data = []

    def __init__(self, url, output_dir, *args, **kwargs):
        super(EnlacesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        self.base_url = urlparse(url).netloc
        self.output_dir = output_dir  # Guardamos el directorio de salida

    def parse(self, response):
        for enlace in response.css('a'):
            url = enlace.css('::attr(href)').get()
            texto = enlace.css('::text').get()
            if url and not url.startswith('http'):
                url = response.urljoin(url)

            enlace_domain = urlparse(url).netloc
            if enlace_domain == self.base_url:
                unique_key = (response.url, url)
                if unique_key not in self.seen_links:
                    self.seen_links.add(unique_key)
                    self.all_data.append({
                        'origen': response.url,
                        'url': url,
                        'texto': texto.strip() if texto else ''
                    })
                if url and url.startswith('http'):
                    yield response.follow(url, self.parse_enlace)

    def parse_enlace(self, response):
        for enlace in response.css('a'):
            url = enlace.css('::attr(href)').get()
            texto = enlace.css('::text').get()
            if url and not url.startswith('http'):
                url = response.urljoin(url)

            enlace_domain = urlparse(url).netloc
            if enlace_domain == self.base_url:
                unique_key = (response.url, url)
                if unique_key not in self.seen_links:
                    self.seen_links.add(unique_key)
                    self.all_data.append({
                        'origen': response.url,
                        'url': url,
                        'texto': texto.strip() if texto else ''
                    })

    def closed(self, reason):
        # Guardamos el archivo Excel en el directorio de salida
        df = pd.DataFrame(self.all_data)
        output_file = os.path.join(self.output_dir, 'enlaces_extraidos.xlsx')
        df.to_excel(output_file, index=False, engine='openpyxl')
