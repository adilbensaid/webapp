from flask import Flask, request, render_template, send_file
import subprocess
import os
import pandas as pd
from urllib.parse import urlparse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            # Ejecutar el spider con la URL dada
            os.environ['SCRAPY_URL'] = url  # Pasar URL como variable de entorno
            subprocess.run(['scrapy', 'crawl', 'enlaces'])

            # Verificar si el archivo Excel fue creado
            if os.path.exists('enlaces_extraidos.xlsx'):
                return send_file('enlaces_extraidos.xlsx', as_attachment=True)
        return 'Hubo un problema al ejecutar el spider.'
    return render_template('form.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT env variable or 5000 by default
    app.run(debug=True, host='0.0.0.0', port=port)
