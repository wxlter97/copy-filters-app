from flask import Flask, request, render_template_string
import json
import requests
import time

app = Flask(__name__)

# ------------------------------------------------
# Obtener filtro completo desde la cuenta origen
# ------------------------------------------------
def get_filter_by_id(origin_prefix, filter_id):
    url = f"https://{origin_prefix}.myvtex.com/_v/filters-plp/filter/{filter_id}"
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error obteniendo filtro {filter_id}: {response.text}")

    return response.json()


# ------------------------------------------------
# Subir filtro a la cuenta destino
# ------------------------------------------------
def upload_filter(domain_prefix, filter_name, filter_data):
    # limpiamos id para evitar conflictos
    filter_data.pop("id", None)

    url = f"https://{domain_prefix}.myvtex.com/_v/filters-plp/filter/"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.put(url, headers=headers, json=filter_data)

    if response.status_code not in [200, 204]:
        raise Exception(f"Error subiendo {filter_name}: {response.text}")

    return response


# ------------------------------------------------
# Flujo completo: obtener → subir
# ------------------------------------------------
def process_filters(origin_prefix, dest_prefix, filter_ids):
    log = []

    for index, filter_id in enumerate(filter_ids):
        # 1. Obtener desde origen
        filter_data = get_filter_by_id(origin_prefix, filter_id)
        filter_name = filter_data.get("name", f"(sin nombre) {filter_id}")

        # 2. Subir a destino
        upload_filter(dest_prefix, filter_name, filter_data)

        log.append(f"{index + 1}/{len(filter_ids)} - {filter_name} copiado correctamente")

        time.sleep(1)  # evitar rate-limit

    return "\n".join(log)


# ------------------------------------------------
# Interfaz HTML simple
# ------------------------------------------------
FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Copiar filtros VTEX</title>
</head>
<body>
    <h1>Copiar filtros entre cuentas VTEX</h1>

    <form method="POST" enctype="multipart/form-data">

        <label>Cuenta origen:</label><br>
        <input type="text" name="origen" placeholder="simannicor" required><br><br>

        <label>Cuenta destino:</label><br>
        <input type="text" name="destino" placeholder="simandestino" required><br><br>

        <label>Archivo JSON con IDs:</label><br>
        <input type="file" name="file" accept=".json" required><br><br>

        <button type="submit">Copiar filtros</button>
    </form>

    {% if log %}
        <h2>Resultado:</h2>
        <pre>{{ log }}</pre>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        origen = request.form.get("origen")
        destino = request.form.get("destino")
        file = request.files.get("file")

        if not file:
            return render_template_string(FORM_HTML, log="Error: Debes subir un archivo JSON.")

        try:
            data = json.load(file)
            filter_ids = data.get("filters", [])

            if not filter_ids:
                return render_template_string(FORM_HTML, log="El archivo JSON no contiene 'filters'.")

            log = process_filters(origen, destino, filter_ids)

            return render_template_string(FORM_HTML, log=log)

        except Exception as e:
            return render_template_string(FORM_HTML, log=f"Error: {str(e)}")

    return render_template_string(FORM_HTML)


if __name__ == "__main__":
    app.run(debug=True)
