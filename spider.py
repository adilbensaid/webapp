import scrapy
from urllib.parse import urlparse
import pandas as pd
import os

class EnlacesSpider(scrapy.Spider):
    name = 'enlaces'  # Nombre del spider
    start_urls = []  # Lista de URLs de inicio, que se llenará con la URL proporcionada
    all_data = []  # Lista para almacenar los datos extraídos (origen, url, texto)

    # Constructor del spider, que recibe la URL de inicio y el directorio de salida
    def __init__(self, url, output_dir, *args, **kwargs):
        super(EnlacesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]  # Establecer la URL de inicio
        self.base_url = urlparse(url).netloc  # Extraer el dominio base de la URL
        self.output_dir = output_dir  # Guardar el directorio de salida para los datos

    # Método para procesar la respuesta de la URL de inicio
    def parse(self, response):
        # Recorremos todos los enlaces (etiquetas <a>) encontrados en la página
        for enlace in response.css('a'):
            url = enlace.css('::attr(href)').get()  # Obtener el enlace (atributo href)
            texto = enlace.css('::text').get()  # Obtener el texto del enlace
            if url and not url.startswith('http'):  # Si el enlace no es absoluto
                url = response.urljoin(url)  # Convertirlo en absoluto usando la URL base

            enlace_domain = urlparse(url).netloc  # Obtener el dominio del enlace
            if enlace_domain == self.base_url:  # Comprobar si el enlace es del mismo dominio
                # Añadir los datos (origen, url, texto) a la lista all_data
                self.all_data.append({
                    'origen': response.url,
                    'url': url,
                    'texto': texto.strip() if texto else ''  # Si hay texto, lo limpiamos (quitamos espacios)
                })
                # Si el enlace es un URL absoluto, seguimos el enlace y procesamos esa página
                if url and url.startswith('http'):
                    yield response.follow(url, self.parse_enlace)

    # Método para procesar las páginas a las que hemos seguido enlaces internos
    def parse_enlace(self, response):
        # Recorremos todos los enlaces (etiquetas <a>) encontrados en la página
        for enlace in response.css('a'):
            url = enlace.css('::attr(href)').get()  # Obtener el enlace (atributo href)
            texto = enlace.css('::text').get()  # Obtener el texto del enlace
            if url and not url.startswith('http'):  # Si el enlace no es absoluto
                url = response.urljoin(url)  # Convertirlo en absoluto usando la URL base

            enlace_domain = urlparse(url).netloc  # Obtener el dominio del enlace
            if enlace_domain == self.base_url:  # Comprobar si el enlace es del mismo dominio
                # Añadir los datos (origen, url, texto) a la lista all_data
                self.all_data.append({
                    'origen': response.url,
                    'url': url,
                    'texto': texto.strip() if texto else ''  # Si hay texto, lo limpiamos (quitamos espacios)
                })

    # Método que se ejecuta cuando el spider termina de procesar todas las páginas
    def closed(self, reason):
        # Convertimos la lista all_data en un DataFrame de Pandas
        df = pd.DataFrame(self.all_data)
        # Definimos la ruta y nombre del archivo Excel de salida
        output_file = os.path.join(self.output_dir, 'enlaces_extraidos.xlsx')
        # Guardamos los datos en un archivo Excel en la ubicación especificada
        df.to_excel(output_file, index=False, engine='openpyxl')
