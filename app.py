from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

HORAS_POSIBLES = list(range(8, 17))

profesores = {
    "profesor1": [(8, 10), (14, 16)],
    "profesor2": [(9, 11), (13, 15)],
    "profesor3": [(11, 13), (15, 17)],
    "profesor4": [(10, 12), (16, 18)]
}

def fitness(gen, profesores):
    start = gen
    end = gen + 2
    disponibles = 0
    for bloques in profesores.values():
        ocupado = False
        for bloque in bloques:
            if not (end <= bloque[0] or start >= bloque[1]):
                ocupado = True
                break
        if not ocupado:
            disponibles += 1
    return disponibles

def algoritmo_genetico(generaciones, tamano, tasa_mutacion):
    poblacion = random.sample(HORAS_POSIBLES, tamano)
    historial = []

    for generacion in range(generaciones):
        fitnesses = [(gen, fitness(gen, profesores)) for gen in poblacion]
        historial.append(fitnesses)

        for gen, fit in fitnesses:
            if fit == 4:
                return gen, historial

        fitnesses.sort(key=lambda x: x[1], reverse=True)
        mejores = [f[0] for f in fitnesses[:2]]
        nueva_poblacion = mejores.copy()

        while len(nueva_poblacion) < tamano:
            padre = random.choice(mejores)
            if random.random() < tasa_mutacion:
                hijo = random.choice(HORAS_POSIBLES)
            else:
                hijo = padre + random.choice([-1, 1])
                if hijo not in HORAS_POSIBLES:
                    hijo = random.choice(HORAS_POSIBLES)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    mejor_gen = max(poblacion, key=lambda g: fitness(g, profesores))
    return mejor_gen, historial

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ejecutar')
def ejecutar():
    gen = int(request.args.get('gen', 50))
    tam = int(request.args.get('tam', 5))
    mut = float(request.args.get('mut', 0.1))

    resultado, historial = algoritmo_genetico(gen, tam, mut)
    return jsonify({
        'mejor_horario': f"{resultado}:00 - {resultado+2}:00",
        'generaciones': len(historial),
        'historial': historial
    })

if __name__ == '__main__':
    app.run(debug=True)
