import random
import numpy as np
from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt # Importar matplotlib
import os # Para manejo de rutas y carpetas
import datetime # Para nombres de archivo únicos

app = Flask(__name__)

# --- Configuración del Problema de Horarios ---

# Horario disponible: Lunes a Viernes, de 8:00 AM a 6:00 PM (18:00)
# Las horas se representarán como flotantes (ej. 8.0, 8.5, 9.0, ...)
DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
START_HOUR_DAY = 8.0
END_HOUR_DAY = 18.0 # 6:00 PM
SLOT_DURATION = 2.0 # Duración del bloque a encontrar (2 horas)
INCREMENT = 0.5 # Incrementos de media hora (0.5 horas)

# Generar todos los posibles tiempos de inicio para un bloque de 2 horas
POSSIBLE_START_TIMES = [t for t in np.arange(START_HOUR_DAY, END_HOUR_DAY - SLOT_DURATION + INCREMENT, INCREMENT)]
NUM_TIME_SLOTS = len(POSSIBLE_START_TIMES)
NUM_DAYS = len(DAYS_OF_WEEK)

# Horarios ocupados de los 4 profesores
# Formato: { "Profesor Nombre": [(Dia, Hora_Inicio_Ocupada, Hora_Fin_Ocupada), ...] }
# Las horas_inicio y horas_fin son inclusivas en el inicio y exclusivas en el fin
PROFESSOR_SCHEDULES = {
    "Profesor A": [
        ("Lunes", 9.0, 11.0), ("Lunes", 14.0, 16.0),
        ("Martes", 10.0, 12.0),
        ("Miércoles", 9.0, 10.0), ("Miércoles", 13.0, 15.0),
        ("Jueves", 8.0, 9.0), ("Jueves", 16.0, 18.0)
    ],
    "Profesor B": [
        ("Lunes", 10.0, 12.0),
        ("Martes", 9.0, 11.0), ("Martes", 14.0, 16.0),
        ("Miércoles", 8.0, 9.0), ("Miércoles", 15.0, 17.0),
        ("Jueves", 10.0, 12.0), ("Jueves", 15.0, 17.0)
    ],
    "Profesor C": [
        ("Lunes", 11.0, 13.0),
        ("Martes", 11.0, 13.0),
        ("Miércoles", 10.0, 12.0), ("Miércoles", 16.0, 17.0),
        ("Jueves", 13.0, 15.0),
        ("Viernes", 9.0, 11.0)
    ],
    "Profesor D": [
        ("Lunes", 8.0, 10.0), ("Lunes", 15.0, 17.0),
        ("Martes", 13.0, 15.0),
        ("Miércoles", 11.0, 13.0),
        ("Jueves", 9.0, 11.0), ("Jueves", 14.0, 16.0),
        ("Viernes", 10.0, 12.0)
    ]
}

# Carpeta para guardar las gráficas generadas
PLOTS_FOLDER = os.path.join(app.root_path, 'static', 'plots')
if not os.path.exists(PLOTS_FOLDER):
    os.makedirs(PLOTS_FOLDER)

# --- Funciones Auxiliares para el Problema ---

def is_slot_occupied(professor_schedule, day, start_hour, end_hour):
    """Verifica si un bloque de tiempo dado está ocupado para un profesor."""
    for occupied_day, occupied_start, occupied_end in professor_schedule:
        if day == occupied_day:
            if max(start_hour, occupied_start) < min(end_hour, occupied_end):
                return True
    return False

# --- Algoritmo Genético ---

def create_individual():
    """Crea un individuo (cromosoma) aleatorio: (day_index, start_time_index)"""
    day_idx = random.randrange(NUM_DAYS)
    time_idx = random.randrange(NUM_TIME_SLOTS)
    return (day_idx, time_idx)

def evaluate_fitness(individual):
    """Calcula el fitness de un individuo. Mayor fitness = mejor."""
    day_idx, time_idx = individual
    day_name = DAYS_OF_WEEK[day_idx]
    start_hour = POSSIBLE_START_TIMES[time_idx]
    end_hour = start_hour + SLOT_DURATION

    free_professors_count = 0
    for prof_name, schedule in PROFESSOR_SCHEDULES.items():
        if not is_slot_occupied(schedule, day_name, start_hour, end_hour):
            free_professors_count += 1
    
    return 1 if free_professors_count == len(PROFESSOR_SCHEDULES) else 0

def select_parents(population, fitnesses):
    """Selección por torneo."""
    fitnesses = np.array(fitnesses)
    
    if np.sum(fitnesses) == 0:
        probabilities = np.ones(len(fitnesses)) / len(fitnesses)
    else:
        probabilities = fitnesses / np.sum(fitnesses)
    
    parent1 = population[np.random.choice(len(population), p=probabilities)]
    parent2 = population[np.random.choice(len(population), p=probabilities)]
    
    return parent1, parent2

def crossover(parent1, parent2):
    """Cruce de un punto para (day_idx, time_idx)."""
    if random.random() < 0.5:
        child1 = (parent1[0], parent2[1])
        child2 = (parent2[0], parent1[1])
    else:
        child1 = (parent2[0], parent1[1])
        child2 = (parent1[0], parent2[1])
    return child1, child2

def mutate(individual, mutation_rate):
    """Muta un individuo (cambia día o tiempo)"""
    day_idx, time_idx = individual
    if random.random() < mutation_rate:
        day_idx = random.randrange(NUM_DAYS)
    if random.random() < mutation_rate:
        time_idx = random.randrange(NUM_TIME_SLOTS)
    return (day_idx, time_idx)

def genetic_algorithm(population_size, generations, mutation_rate):
    """Ejecuta el Algoritmo Genético."""
    
    population = [create_individual() for _ in range(population_size)]
    best_solution = None
    best_fitness = -1

    fitness_history = []
    avg_fitness_history = []

    for gen in range(generations):
        fitnesses = [evaluate_fitness(ind) for ind in population]

        current_best_fitness = max(fitnesses)
        current_avg_fitness = sum(fitnesses) / len(fitnesses)
        
        fitness_history.append(current_best_fitness)
        avg_fitness_history.append(current_avg_fitness)

        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = population[fitnesses.index(best_fitness)]
            
            if best_fitness == 1:
                break # Se encontró una solución donde todos los profesores coinciden

        new_population = []
        if best_solution:
             new_population.append(best_solution)

        while len(new_population) < population_size:
            parent1, parent2 = select_parents(population, fitnesses)
            child1, child2 = crossover(parent1, parent2)
            
            child1 = mutate(child1, mutation_rate)
            child2 = mutate(child2, mutation_rate)
            
            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)
        
        population = new_population

    if best_solution and best_fitness == 1:
        day_idx, time_idx = best_solution
        day_name = DAYS_OF_WEEK[day_idx]
        start_hour = POSSIBLE_START_TIMES[time_idx]
        end_hour = start_hour + SLOT_DURATION
        
        found_slot_display = {
            "day": day_name,
            "start_time": f"{int(start_hour):02d}:{int((start_hour % 1) * 60):02d}",
            "end_time": f"{int(end_hour):02d}:{int((end_hour % 1) * 60):02d}"
        }
    else:
        found_slot_display = None

    return {
        "found_slot": found_slot_display,
        "best_fitness_history": fitness_history,
        "avg_fitness_history": avg_fitness_history,
        "generations_ran": gen + 1
    }

def save_fitness_plot(best_fitness_history, avg_fitness_history, generations_ran):
    """Guarda la gráfica de evolución del fitness como una imagen PNG."""
    plt.figure(figsize=(10, 6))
    # Colores corregidos para Matplotlib (usando códigos hexadecimales)
    plt.plot(range(1, generations_ran + 1), best_fitness_history, label='Mejor Fitness por Generación', color='#4BC0C0')
    plt.plot(range(1, generations_ran + 1), avg_fitness_history, label='Fitness Promedio por Generación', color='#FF6384')
    plt.xlabel('Generación')
    plt.ylabel('Fitness (1 = Todos Libres)')
    plt.title('Evolución del Fitness del Algoritmo Genético')
    plt.ylim(0, 1.1) # Rango del fitness
    plt.legend()
    plt.grid(True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    plot_filename = f"fitness_evolution_{timestamp}.png"
    plot_filepath = os.path.join(PLOTS_FOLDER, plot_filename)
    
    plt.savefig(plot_filepath)
    plt.close() # Cierra la figura para liberar memoria

    return f"/static/plots/{plot_filename}" # Retorna la URL relativa para el frontend

# --- Rutas de Flask ---

@app.route('/')
def index():
    """Sirve la página HTML principal."""
    return render_template('index.html')

@app.route('/run_ga', methods=['POST'])
def run_ga():
    """Endpoint para ejecutar el algoritmo genético y devolver los resultados."""
    data = request.json
    population_size = int(data.get('population_size', 100))
    generations = int(data.get('generations', 500))
    mutation_rate = float(data.get('mutation_rate', 0.1))

    results = genetic_algorithm(population_size, generations, mutation_rate)
    
    # Generar y guardar la gráfica de fitness
    fitness_plot_url = save_fitness_plot(
        results["best_fitness_history"],
        results["avg_fitness_history"],
        results["generations_ran"]
    )
    results["fitness_plot_url"] = fitness_plot_url # Añadir la URL al resultado

    # Añadir los horarios ocupados de los profesores para la visualización en el frontend
    formatted_professor_schedules = {}
    for prof, schedule in PROFESSOR_SCHEDULES.items():
        formatted_schedule = []
        for day, start, end in schedule:
            formatted_schedule.append({
                "day": day,
                "start_hour": start,
                "end_hour": end
            })
        formatted_professor_schedules[prof] = formatted_schedule

    results["professor_schedules"] = formatted_professor_schedules
    results["days_of_week"] = DAYS_OF_WEEK
    results["possible_start_times"] = POSSIBLE_START_TIMES
    results["start_hour_day"] = START_HOUR_DAY
    results["end_hour_day"] = END_HOUR_DAY
    results["slot_duration"] = SLOT_DURATION
    results["increment_time"] = INCREMENT

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)