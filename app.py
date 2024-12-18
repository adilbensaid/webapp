from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import sys
import os
from multiprocessing import Process
from scrapy.crawler import CrawlerProcess
from spider import EnlacesSpider  # Importamos el Spider desde spider.py
import tempfile
import shutil

# Función para comprobar e instalar paquetes
def check_and_install(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Verificar que dependencias necesarias están instaladas
check_and_install("scrapy")
check_and_install("pandas")
check_and_install("openpyxl")

# Crear la aplicación Flask
app = Flask(__name__)

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')  # Crear un archivo HTML básico para la interfaz

# Definir la función de scraping fuera de ejecutar_scrapy
def run_scrapy(url, output_dir):
    process = CrawlerProcess()
    # Modificar el spider para que guarde el archivo en output_dir
    process.crawl(EnlacesSpider, url=url, output_dir=output_dir)
    process.start()

# Ruta para ejecutar el scraping
@app.route('/scraping', methods=['POST'])
def ejecutar_scrapy():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'Por favor, ingresa una URL válida.'})

    # Asegurarnos de que el directorio de salida exista
    output_dir = os.path.join(os.getcwd(), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Usar multiprocessing para crear un nuevo proceso para el scraping
    p = Process(target=run_scrapy, args=(url, output_dir))
    p.start()
    p.join()  # Asegúrate de que el proceso termine antes de continuar

    # Ruta completa del archivo generado
    file_path = os.path.join(output_dir, 'enlaces_extraidos.xlsx')

    if not os.path.exists(file_path):
        return jsonify({'error': 'Hubo un error al generar el archivo.'})

    # Enviar el archivo al usuario para que lo descargue
    return send_file(file_path, as_attachment=True, download_name='enlaces_extraidos.xlsx')





if __name__ == '__main__':
    app.run(debug=True)
