import json
import os
import uuid
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "prestamos-familiares-secret-key")

DATA_FILE = os.environ.get("DATA_FILE", "/data/prestamos.json")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"familiares": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"familiares": []}


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calcular_balance_familiar(familiar):
    balance = 0.0
    me_deben = 0.0
    me_pagaron = 0.0
    for p in familiar.get("prestamos", []):
        if p["tipo"] == "yo_preste":
            me_deben += p["monto"]
        else:
            me_pagaron += p["monto"]
    balance = me_deben - me_pagaron
    return {"me_deben": me_deben, "yo_debo": me_pagaron, "balance": balance}


def calcular_totales(data):
    me_deben = 0.0
    yo_debo = 0.0
    for f in data["familiares"]:
        b = calcular_balance_familiar(f)
        me_deben += b["me_deben"]
        yo_debo += b["yo_debo"]
    return {
        "me_deben": me_deben,
        "yo_debo": yo_debo,
        "balance": me_deben - yo_debo,
        "total_familiares": len(data["familiares"]),
    }


@app.route("/")
def index():
    data = load_data()
    totales = calcular_totales(data)
    familiares = []
    for f in data["familiares"]:
        b = calcular_balance_familiar(f)
        familiares.append(
            {
                "id": f["id"],
                "nombre": f["nombre"],
                "num_prestamos": len(f.get("prestamos", [])),
                "balance": b["balance"],
                "me_deben": b["me_deben"],
                "yo_debo": b["yo_debo"],
            }
        )
    return render_template("index.html", totales=totales, familiares=familiares)


@app.route("/agregar-familiar", methods=["POST"])
def agregar_familiar():
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        flash("El nombre es obligatorio", "error")
        return redirect(url_for("index"))
    data = load_data()
    data["familiares"].append(
        {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "prestamos": [],
        }
    )
    save_data(data)
    flash(f"Familiar '{nombre}' agregado", "success")
    return redirect(url_for("index"))


@app.route("/familiar/<familiar_id>")
def ver_familiar(familiar_id):
    data = load_data()
    familiar = next((f for f in data["familiares"] if f["id"] == familiar_id), None)
    if not familiar:
        flash("Familiar no encontrado", "error")
        return redirect(url_for("index"))
    balance = calcular_balance_familiar(familiar)
    # Compute running totals for each entry
    prestamos = []
    acumulado = 0.0
    for p in familiar.get("prestamos", []):
        if p["tipo"] == "yo_preste":
            acumulado += p["monto"]
        else:
            acumulado -= p["monto"]
        prestamos.append({**p, "acumulado": acumulado})
    return render_template(
        "familiar.html",
        familiar=familiar,
        balance=balance,
        prestamos=prestamos,
        now=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/familiar/<familiar_id>/agregar-prestamo", methods=["POST"])
def agregar_prestamo(familiar_id):
    data = load_data()
    familiar = next((f for f in data["familiares"] if f["id"] == familiar_id), None)
    if not familiar:
        flash("Familiar no encontrado", "error")
        return redirect(url_for("index"))

    descripcion = request.form.get("descripcion", "").strip()
    try:
        monto = round(float(request.form.get("monto", 0)), 2)
    except ValueError:
        monto = 0.0
    tipo = request.form.get("tipo", "yo_preste")
    fecha = request.form.get("fecha", datetime.now().strftime("%Y-%m-%d"))

    if monto <= 0:
        flash("La cantidad debe ser mayor a 0", "error")
        return redirect(url_for("ver_familiar", familiar_id=familiar_id))

    familiar.setdefault("prestamos", []).append(
        {
            "id": str(uuid.uuid4()),
            "tipo": tipo,
            "descripcion": descripcion,
            "monto": monto,
            "fecha": fecha,
        }
    )
    save_data(data)
    flash("Préstamo agregado", "success")
    return redirect(url_for("ver_familiar", familiar_id=familiar_id))


@app.route("/familiar/<familiar_id>/prestamo/<prestamo_id>/editar", methods=["POST"])
def editar_prestamo(familiar_id, prestamo_id):
    data = load_data()
    familiar = next((f for f in data["familiares"] if f["id"] == familiar_id), None)
    if not familiar:
        flash("Familiar no encontrado", "error")
        return redirect(url_for("index"))

    prestamo = next(
        (p for p in familiar.get("prestamos", []) if p["id"] == prestamo_id), None
    )
    if not prestamo:
        flash("Préstamo no encontrado", "error")
        return redirect(url_for("ver_familiar", familiar_id=familiar_id))

    descripcion = request.form.get("descripcion", "").strip()
    try:
        monto = round(float(request.form.get("monto", 0)), 2)
    except ValueError:
        monto = 0.0
    tipo = request.form.get("tipo", prestamo["tipo"])
    fecha = request.form.get("fecha", prestamo["fecha"])

    if monto <= 0:
        flash("La cantidad debe ser mayor a 0", "error")
        return redirect(url_for("ver_familiar", familiar_id=familiar_id))

    prestamo["tipo"] = tipo
    prestamo["descripcion"] = descripcion
    prestamo["monto"] = monto
    prestamo["fecha"] = fecha
    save_data(data)
    flash("Entrada actualizada", "success")
    return redirect(url_for("ver_familiar", familiar_id=familiar_id))


@app.route("/familiar/<familiar_id>/prestamo/<prestamo_id>/eliminar", methods=["POST"])
def eliminar_prestamo(familiar_id, prestamo_id):
    data = load_data()
    familiar = next((f for f in data["familiares"] if f["id"] == familiar_id), None)
    if not familiar:
        flash("Familiar no encontrado", "error")
        return redirect(url_for("index"))

    familiar["prestamos"] = [
        p for p in familiar.get("prestamos", []) if p["id"] != prestamo_id
    ]
    save_data(data)
    flash("Préstamo eliminado", "success")
    return redirect(url_for("ver_familiar", familiar_id=familiar_id))


@app.route("/familiar/<familiar_id>/eliminar", methods=["POST"])
def eliminar_familiar(familiar_id):
    data = load_data()
    data["familiares"] = [f for f in data["familiares"] if f["id"] != familiar_id]
    save_data(data)
    flash("Familiar eliminado", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
