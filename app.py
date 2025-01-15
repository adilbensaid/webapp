# app.py
import os
import re
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import pandas as pd
from urllib.parse import urlparse
import scrapy
from scrapy.crawler import CrawlerProcess

app = Flask(__name__)

# Carpetas para subir y guardar archivos
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Ruta de la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar el formulario del primer script
@app.route('/process', methods=['POST'])
def process():
    try:
        # Obtener archivos subidos
        screaming_file = request.files['screaming_file']
        sistrix_file = request.files['sistrix_file']
        url_base = request.form['url_base']
        slug_productos = request.form['slug_productos']
        taxonomias = [tax.strip() for tax in request.form['taxonomias'].split(',') if tax.strip()]

        # Guardar archivos subidos
        screaming_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(screaming_file.filename))
        sistrix_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(sistrix_file.filename))

        screaming_file.save(screaming_path)
        sistrix_file.save(sistrix_path)

        # Procesar archivos
        result_path = fusionar_y_analizar(screaming_path, sistrix_path, url_base, slug_productos, taxonomias)

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        return f"Ocurrió un error: {str(e)}"

# Función para fusionar y analizar archivos
def fusionar_y_analizar(screaming_path, sistrix_path, url_base, slug_productos, taxonomias):
    df_screaming = pd.read_excel(screaming_path, engine='openpyxl')
    df_sistrix = pd.read_csv(sistrix_path, sep=';', encoding='utf-8-sig')

    # Fusionar archivos
    df_merged = pd.merge(df_screaming, df_sistrix, left_on="Dirección", right_on="URL", how="left")

    # Filtrar contenido no deseado
    columnas_requeridas = ['Dirección', 'Tipo de contenido', 'Código de respuesta', 'Indexabilidad', 
                           'Título 1', 'Meta description 1', 'H1-1', 'GA4 Sessions', 'GA4 Views', 
                           'Palabra clave principal', 'Top-10', 'Top-100', 'Cuota de visibilidad', 'Clics', 'Impresiones']
    columnas_existentes = [col for col in columnas_requeridas if col in df_merged.columns]
    df_merged = df_merged[columnas_existentes]

    recursos = df_merged[df_merged['Tipo de contenido'].isin(['text/css', 'text/javascript', 'font/opentype', 
                                                             'application/x-font-woff2', 'application/javascript'])]
    df_merged.drop(recursos.index, inplace=True)

    imagenes = df_merged[df_merged['Tipo de contenido'].isin(['image/jpeg', 'image/png', 'application/pdf', 
                                                             'image/svg+xml', 'image/webp']) | 
                          df_merged['Dirección'].str.contains(r'\.png|\.jpg|\.svg|\.webp|\.jpeg', na=False)]
    df_merged.drop(imagenes.index, inplace=True)

    parametros = df_merged[df_merged['Dirección'].str.contains(r'[?=]', na=False)]
    df_merged.drop(parametros.index, inplace=True)

    http = df_merged[df_merged['Dirección'].str.startswith("http://", na=False)]
    df_merged.drop(http.index, inplace=True)

    productos = df_merged[df_merged['Dirección'].str.startswith(url_base) & df_merged['Dirección'].str.contains(slug_productos, na=False)]
    df_merged.drop(productos.index, inplace=True)

    tax_todas = pd.DataFrame()
    taxonomias_filtradas = {}
    for taxonomia in taxonomias:
        tax = df_merged[df_merged['Dirección'].str.startswith(url_base) & df_merged['Dirección'].str.contains(taxonomia, na=False)]
        taxonomias_filtradas[taxonomia] = tax
        tax_todas = pd.concat([tax_todas, tax], ignore_index=True)
        df_merged.drop(tax.index, inplace=True)

    # Guardar resultados
    result_path = os.path.join(app.config['RESULT_FOLDER'], 'resultado.xlsx')
    with pd.ExcelWriter(result_path) as writer:
        df_merged.to_excel(writer, sheet_name='General', index=False)
        productos.to_excel(writer, sheet_name='Productos', index=False)
        http.to_excel(writer, sheet_name='Http', index=False)
        parametros.to_excel(writer, sheet_name='Parametros', index=False)
        imagenes.to_excel(writer, sheet_name='Imagenes', index=False)
        recursos.to_excel(writer, sheet_name='Recursos', index=False)

        for taxonomia, data in taxonomias_filtradas.items():
            sheet_name = re.sub(r'[\/:*?"<>|]', '_', taxonomia)
            data.to_excel(writer, sheet_name=sheet_name, index=False)

    return result_path

# Ruta para manejar el formulario del segundo script
@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        url = request.form['url']
        if not url:
            return "Por favor, proporciona una URL válida."

        # Ejecutar el scraper
        result_path = run_scraper(url)

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        return f"Ocurrió un error: {str(e)}"

# Función para ejecutar el scraper
def run_scraper(url):
    class EnlacesSpider(scrapy.Spider):
        name = 'enlaces'
        start_urls = [url]
        all_data = []

        def parse(self, response):
            for enlace in response.css('a'):
                href = enlace.css('::attr(href)').get()
                texto = enlace.css('::text').get()
                if href and not href.startswith('http'):
                    href = response.urljoin(href)
                self.all_data.append({'origen': response.url, 'url': href, 'texto': texto.strip() if texto else ''})

        def closed(self, reason):
            df = pd.DataFrame(self.all_data)
            result_path = os.path.join(RESULT_FOLDER, 'enlaces_extraidos.xlsx')
            df.to_excel(result_path, index=False, engine='openpyxl')

    process = CrawlerProcess()
    process.crawl(EnlacesSpider)
    process.start()

    return os.path.join(RESULT_FOLDER, 'enlaces_extraidos.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
