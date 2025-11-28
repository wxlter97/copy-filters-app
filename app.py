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
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error obteniendo filtro {filter_id}: {response.text}")

    return response.json()


# ------------------------------------------------
# Subir filtro a la cuenta destino
# ------------------------------------------------
def upload_filter(domain_prefix, filter_name, filter_data):
    filter_data.pop("id", None)

    url = f"https://{domain_prefix}.myvtex.com/_v/filters-plp/filter/"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.put(url, headers=headers, json=filter_data)

    if response.status_code not in [200, 204]:
        raise Exception(f"Error subiendo {filter_name}: {response.text}")

    return response


# ------------------------------------------------
# Flujo completo
# ------------------------------------------------
def process_filters(origin_prefix, dest_prefix, filter_ids):
    log = []
    for index, filter_id in enumerate(filter_ids):
        filter_data = get_filter_by_id(origin_prefix, filter_id)
        filter_name = filter_data.get("name", f"(sin nombre) {filter_id}")
        upload_filter(dest_prefix, filter_name, filter_data)
        log.append(f"{index+1}/{len(filter_ids)} - {filter_name} copiado correctamente")
        time.sleep(1)
    return "\n".join(log)


# ------------------------------------------------
# Interfaz moderna
# ------------------------------------------------
FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Copiar filtros VTEX</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
    <div class="bg-white shadow-xl rounded-xl p-8 w-full max-w-xl border border-gray-200">

        <h1 class="text-2xl font-bold text-gray-800 mb-6 text-center">
            Copiar filtros entre cuentas VTEX
        </h1>

        <form method="POST" enctype="multipart/form-data" class="space-y-5">

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Cuenta origen</label>
                <input type="text" name="origen" placeholder="siman" required
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-300 focus:outline-none">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Cuenta destino</label>
                <input type="text" name="destino" placeholder="simanguatemala" required
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-300 focus:outline-none">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Archivo JSON con IDs</label>
                <input type="file" name="file" accept=".json" required
                    class="w-full px-4 py-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-300 focus:outline-none">
            </div>

            <button type="submit"
                class="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
                Copiar filtros
            </button>

        </form>

        {% if log %}
            <div class="mt-8">
                <h2 class="text-lg font-semibold text-gray-700 mb-2">Resultado:</h2>
                <pre class="bg-gray-900 text-green-300 p-4 rounded-lg text-sm overflow-auto max-h-64">{{ log }}</pre>
            </div>
        {% endif %}

    </div>
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
    app.run(host="0.0.0.0", port=10000)
