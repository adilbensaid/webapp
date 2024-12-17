import scrapy
import pandas as pd
from urllib.parse import urlparse
import subprocess
import sys
import os


# Función para comprobar si un paquete está instalado
def check_and_install(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Comprobar e instalar pandas y openpyxl
check_and_install("scrapy")
check_and_install("pandas")
check_and_install("openpyxl")

class EnlacesSpider(scrapy.Spider):
    name = 'enlaces'
    self.start_urls = [os.environ.get('SCRAPY_URL', 'https://dentin.mktmedianet.es')]
    seen_links = set()  # Usamos un set para hacer un seguimiento de los enlaces procesados
    all_data = []  # Lista para almacenar todos los datos extraídos

    # Extraemos la raíz del dominio (sin tener en cuenta rutas o parámetros)
    def __init__(self, *args, **kwargs):
        super(EnlacesSpider, self).__init__(*args, **kwargs)
        self.base_url = urlparse(self.start_urls[0]).netloc  # Extraemos solo el dominio

    def parse(self, response):
        # Extraemos todos los enlaces <a> y sus atributos 'href' (enlace) y su contenido de texto
        for enlace in response.css('a'):
            # Extraemos el enlace (href)
            url = enlace.css('::attr(href)').get()

            # Extraemos el texto dentro de la etiqueta <a>
            texto = enlace.css('::text').get()

            # Si el enlace es relativo, lo convertimos en absoluto
            if url and not url.startswith('http'):
                url = response.urljoin(url)

            # Filtramos para asegurarnos que el enlace pertenece al mismo dominio que el origen
            enlace_domain = urlparse(url).netloc
            if enlace_domain == self.base_url:
                # Crear una clave única para cada combinación de origen y enlace
                unique_key = (response.url, url)

                # Si ya hemos procesado este enlace (origen + URL), no lo procesamos de nuevo
                if unique_key not in self.seen_links:
                    self.seen_links.add(unique_key)  # Añadirlo al conjunto de enlaces procesados
                    self.all_data.append({
                        'origen': response.url,
                        'url': url,
                        'texto': texto.strip() if texto else ''
                    })

                # Si el enlace es un URL absoluto dentro del mismo dominio, también seguimos ese enlace
                if url and url.startswith('http'):
                    yield response.follow(url, self.parse_enlace)

    def parse_enlace(self, response):
        # Extraemos los enlaces de la página de destino
        for enlace in response.css('a'):
            url = enlace.css('::attr(href)').get()
            texto = enlace.css('::text').get()

            # Si el enlace es relativo, lo convertimos en absoluto
            if url and not url.startswith('http'):
                url = response.urljoin(url)

            # Filtramos para asegurarnos que el enlace pertenece al mismo dominio que el origen
            enlace_domain = urlparse(url).netloc
            if enlace_domain == self.base_url:
                # Crear una clave única para cada combinación de origen y enlace
                unique_key = (response.url, url)

                # Si ya hemos procesado este enlace (origen + URL), no lo procesamos de nuevo
                if unique_key not in self.seen_links:
                    self.seen_links.add(unique_key)  # Añadirlo al conjunto de enlaces procesados
                    self.all_data.append({
                        'origen': response.url,
                        'url': url,
                        'texto': texto.strip() if texto else ''
                    })

    def closed(self, reason):
        # Al finalizar el spider, guardamos los datos en un archivo Excel
        df = pd.DataFrame(self.all_data)
        df.to_excel('enlaces_extraidos.xlsx', index=False, engine='openpyxl')
