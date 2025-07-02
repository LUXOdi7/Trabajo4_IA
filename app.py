from flask import Flask, render_template, request, jsonify
import random, os, json
import matplotlib.pyplot as plt

app = Flask(__name__)

HORARIOS_PROFESORES = {
    "prof1": [9, 10, 14],
    "prof2": [8, 12, 15],
    "prof3": [10, 11, 16],
    "prof4": [13, 14, 15]
}

RANGO_HORARIO = list(range(8, 16))

def evaluar(hora):
    libres = 0
    for ocupados in HORARIOS_PROFESORES.values():
        if hora not in ocupados and hora+1 not in ocupados:
            libres += 1
    return libres

def mutar(hora):
    return random.choice(RANGO_HORARIO)

def generar_grafico(historial):
    mejores_por_gen = [max([ind[1] for ind in gen]) for gen in historial]
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(mejores_por_gen)+1), mejores_por_gen, marker='o', color='blue')
    plt.title("Mejor fitness por generación")
    plt.xlabel("Generación")
    plt.ylabel("Cantidad de profesores disponibles")
    plt.ylim(0, 4)
    plt.grid(True)
    os.makedirs("visualizaciones", exist_ok=True)
    plt.savefig("visualizaciones/grafico_fitness.png")
    plt.close()

def algoritmo_genetico(generaciones, tamano, mutacion):
    historial = []
    mejor = None
    mejor_fitness = -1

    for gen in range(generaciones):
        poblacion = [random.choice(RANGO_HORARIO) for _ in range(tamano)]
        evaluados = [(h, evaluar(h)) for h in poblacion]
        historial.append(evaluados)

        evaluados.sort(key=lambda x: x[1], reverse=True)
        if evaluados[0][1] > mejor_fitness:
            mejor = evaluados[0][0]
            mejor_fitness = evaluados[0][1]

        if mejor_fitness == 4:
            break

        seleccionados = [x[0] for x in evaluados[:tamano//2]]
        nueva_pob = []
        while len(nueva_pob) < tamano:
            padre = random.choice(seleccionados)
            if random.random() < float(mutacion):
                hijo = mutar(padre)
            else:
                hijo = padre
            nueva_pob.append(hijo)

    os.makedirs("visualizaciones", exist_ok=True)
    with open("visualizaciones/poblacion_generaciones.json", "w") as f:
        json.dump(historial, f, indent=2)
    with open("visualizaciones/mejor_horario.txt", "w") as f:
        f.write(f"Mejor horario: {mejor}h a {mejor+2}h - Profesores disponibles: {mejor_fitness}/4")
    with open("visualizaciones/resumen.txt", "w") as f:
        f.write("Algoritmo Genético aplicado para hallar horario común\n")
        f.write(f"Generaciones: {gen+1}, Mejor horario: {mejor}-{mejor+2}, Profesores: {mejor_fitness}\n")

    generar_grafico(historial)

    return mejor, gen+1, historial

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ejecutar")
def ejecutar():
    generaciones = int(request.args.get("gen"))
    tamano = int(request.args.get("tam"))
    mutacion = float(request.args.get("mut"))

    mejor, gen_final, historial = algoritmo_genetico(generaciones, tamano, mutacion)

    historial_formato = [[(h, f) for h, f in gen] for gen in historial]

    return jsonify({
        "mejor_horario": f"{mejor}:00 - {mejor+2}:00",
        "generaciones": gen_final,
        "historial": historial_formato
    })

if __name__ == "__main__":
    app.run(debug=True)
