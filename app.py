import random
import numpy as np
from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import os
import datetime

app = Flask(__name__)

# --- Configuración del Problema de Horarios ---

# Horario disponible: Lunes a Viernes, de 8:00 AM a 6:00 PM (18:00)
DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
START_HOUR_DAY = 8.0
END_HOUR_DAY = 18.0 # 6:00 PM
INCREMENT = 0.5 # Incrementos de media hora (0.5 horas)

# La duración del slot a encontrar (SLOT_DURATION) y los horarios de los profesores
# (PROFESSOR_SCHEDULES) ahora serán dinámicos, basados en la entrada del usuario.

# Carpeta para guardar las gráficas generadas
PLOTS_FOLDER = os.path.join(app.root_path, 'static', 'plots')
if not os.path.exists(PLOTS_FOLDER):
    os.makedirs(PLOTS_FOLDER)

# --- Funciones Auxiliares para el Problema ---

def generate_random_professor_schedules(num_professors, start_hour_day, end_hour_day, days_of_week, increment):
    """
    Genera horarios ocupados aleatorios para un número dado de profesores.
    Cada profesor tendrá entre 10 y 15 bloques ocupados, de 1 a 3 horas de duración.
    (Ajustado para tener más horas ocupadas)
    """
    prof_schedules = {}
    for i in range(num_professors):
        prof_name = f"Profesor {chr(65 + i)}" # A, B, C, ...
        schedule = []
        
        # AUMENTADO: Número aleatorio de bloques ocupados por profesor.
        # Esto hace que haya menos horas disponibles.
        num_occupied_slots = random.randint(10, 15) # Antes: 5 a 10
        
        for _ in range(num_occupied_slots):
            day = random.choice(days_of_week)
            
            # Generar una hora de inicio aleatoria en incrementos de 0.5
            possible_starts = np.arange(start_hour_day, end_hour_day - increment, increment)
            start_time = random.choice(possible_starts)

            # Duración aleatoria del bloque ocupado (1 a 3 horas, en incrementos de 0.5)
            occupied_duration = random.choice([1.0, 1.5, 2.0, 2.5, 3.0])
            end_time = start_time + occupied_duration
            
            # Asegurarse de que el end_time no exceda END_HOUR_DAY
            if end_time > end_hour_day:
                end_time = end_hour_day
                if end_time - start_time < increment: # Asegurar una duración mínima
                    continue

            schedule.append((day, start_time, end_time))
        prof_schedules[prof_name] = schedule
    return prof_schedules

def is_slot_occupied(professor_schedule, day, start_hour, slot_duration):
    """Verifica si un bloque de tiempo dado está ocupado para un profesor."""
    end_hour_proposed = start_hour + slot_duration
    for occupied_day, occupied_start, occupied_end in professor_schedule:
        if day == occupied_day:
            # Revisa si hay solapamiento
            # Un slot ocupado es [occupied_start, occupied_end), lo mismo para el slot propuesto.
            # Hay solapamiento si (start_hour_proposed < occupied_end) AND (end_hour_proposed > occupied_start)
            if max(start_hour, occupied_start) < min(end_hour_proposed, occupied_end):
                return True
    return False

# --- Algoritmo Genético ---

def create_individual(num_days, num_time_slots):
    """Crea un individuo (cromosoma) aleatorio: (day_index, start_time_index)"""
    day_idx = random.randrange(num_days)
    time_idx = random.randrange(num_time_slots)
    return (day_idx, time_idx)

def evaluate_fitness(individual, professor_schedules, days_of_week, possible_start_times, slot_duration):
    """
    Calcula el fitness de un individuo. Mayor fitness = mejor.
    El fitness es el NÚMERO DE PROFESORES LIBRES en ese slot.
    """
    day_idx, time_idx = individual
    day_name = days_of_week[day_idx]
    start_hour = possible_start_times[time_idx]

    free_professors_count = 0
    for prof_name, schedule in professor_schedules.items():
        if not is_slot_occupied(schedule, day_name, start_hour, slot_duration):
            free_professors_count += 1
    
    return free_professors_count

def select_parents(population, fitnesses):
    """Selección por torneo. Asegura que incluso con fitness=0 se pueda seleccionar."""
    fitnesses = np.array(fitnesses)
    
    if np.sum(fitnesses) == 0:
        probabilities = np.ones(len(fitnesses)) / len(fitnesses)
    else:
        probabilities = fitnesses / np.sum(fitnesses)
    
    idx1, idx2 = np.random.choice(len(population), size=2, p=probabilities, replace=True)
    parent1 = population[idx1]
    parent2 = population[idx2]
    
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

def mutate(individual, mutation_rate, num_days, num_time_slots):
    """Muta un individuo (cambia día o tiempo)"""
    day_idx, time_idx = individual
    if random.random() < mutation_rate:
        day_idx = random.randrange(num_days)
    if random.random() < mutation_rate:
        time_idx = random.randrange(num_time_slots)
    return (day_idx, time_idx)

def genetic_algorithm(population_size, generations, mutation_rate, 
                      professor_schedules, days_of_week, possible_start_times, slot_duration):
    """Ejecuta el Algoritmo Genético."""
    
    num_days = len(days_of_week)
    num_time_slots = len(possible_start_times)
    total_professors = len(professor_schedules)

    population = [create_individual(num_days, num_time_slots) for _ in range(population_size)]
    best_solution = None
    best_fitness = -1 # Ahora busca el mayor número de profesores libres

    fitness_history = []
    avg_fitness_history = []

    for gen in range(generations):
        fitnesses = [evaluate_fitness(ind, professor_schedules, days_of_week, possible_start_times, slot_duration) for ind in population]

        current_best_fitness = max(fitnesses)
        current_avg_fitness = sum(fitnesses) / len(fitnesses)
        
        fitness_history.append(current_best_fitness)
        avg_fitness_history.append(current_avg_fitness)

        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = population[fitnesses.index(best_fitness)]
            
            if best_fitness == total_professors: # Si todos están libres, perfecto
                break 

        new_population = []
        if best_solution:
            new_population.append(best_solution)

        while len(new_population) < population_size:
            parent1, parent2 = select_parents(population, fitnesses)
            child1, child2 = crossover(parent1, parent2)
            
            child1 = mutate(child1, mutation_rate, num_days, num_time_slots)
            child2 = mutate(child2, mutation_rate, num_days, num_time_slots)
            
            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)
        
        population = new_population

    # Formatea la solución encontrada para devolver al frontend
    found_slot_display = None
    professors_available_in_best_slot = []
    num_professors_free = 0

    if best_solution:
        day_idx, time_idx = best_solution
        day_name = days_of_week[day_idx]
        start_hour = possible_start_times[time_idx]
        end_hour = start_hour + slot_duration

        for prof_name, schedule in professor_schedules.items():
            if not is_slot_occupied(schedule, day_name, start_hour, slot_duration):
                professors_available_in_best_slot.append(prof_name)
        num_professors_free = len(professors_available_in_best_slot)
        
        found_slot_display = {
            "day": day_name,
            "start_time": f"{int(start_hour):02d}:{int((start_hour % 1) * 60):02d}",
            "end_time": f"{int(end_hour):02d}:{int((end_hour % 1) * 60):02d}",
            "num_professors_free": num_professors_free,
            "professors_available_in_best_slot": professors_available_in_best_slot,
            "total_professors": total_professors
        }
    else:
        found_slot_display = {
            "day": None,
            "start_time": None,
            "end_time": None,
            "num_professors_free": 0,
            "professors_available_in_best_slot": [],
            "total_professors": total_professors # Incluso si no se encuentra un slot, el total es relevante
        }

    return {
        "found_slot": found_slot_display,
        "best_fitness_history": fitness_history,
        "avg_fitness_history": avg_fitness_history,
        "generations_ran": gen + 1
    }

def save_fitness_plot(best_fitness_history, avg_fitness_history, generations_ran, total_professors):
    """Guarda la gráfica de evolución del fitness como una imagen PNG."""
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, generations_ran + 1), best_fitness_history, label='Mejor Fitness por Generación', color='#4BC0C0')
    plt.plot(range(1, generations_ran + 1), avg_fitness_history, label='Fitness Promedio por Generación', color='#FF6384')
    plt.xlabel('Generación')
    plt.ylabel('Fitness (Número de Profesores Libres)')
    plt.title('Evolución del Fitness del Algoritmo Genético')
    plt.ylim(0, total_professors + 0.5)
    plt.yticks(range(0, total_professors + 1))
    plt.legend()
    plt.grid(True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    plot_filename = f"fitness_evolution_{timestamp}.png"
    plot_filepath = os.path.join(PLOTS_FOLDER, plot_filename)
    
    plt.savefig(plot_filepath)
    plt.close()

    return f"/static/plots/{plot_filename}"

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
    num_professors = int(data.get('num_professors', 4)) # Nuevo: cantidad de profesores
    desired_slot_duration = float(data.get('desired_slot_duration', 2.0)) # Nuevo: duración del slot

    # Recalcular possible_start_times basado en la nueva duración del slot
    possible_start_times = [t for t in np.arange(START_HOUR_DAY, END_HOUR_DAY - desired_slot_duration + INCREMENT, INCREMENT)]
    if not possible_start_times: # Asegurarse de que no esté vacío si la duración es muy grande
        return jsonify({"error": "La duración del slot deseada es demasiado grande para el horario disponible."}), 400

    # Generar horarios aleatorios para la cantidad especificada de profesores
    professor_schedules = generate_random_professor_schedules(num_professors, START_HOUR_DAY, END_HOUR_DAY, DAYS_OF_WEEK, INCREMENT)

    results = genetic_algorithm(population_size, generations, mutation_rate, 
                                 professor_schedules, DAYS_OF_WEEK, possible_start_times, desired_slot_duration)
    
    # Generar y guardar la gráfica de fitness
    fitness_plot_url = save_fitness_plot(
        results["best_fitness_history"],
        results["avg_fitness_history"],
        results["generations_ran"],
        num_professors # Pasa el total de profesores para el rango del gráfico
    )
    results["fitness_plot_url"] = fitness_plot_url

    # Formatear los horarios de los profesores para el frontend
    formatted_professor_schedules = {}
    for prof, schedule in professor_schedules.items():
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
    results["possible_start_times"] = possible_start_times
    results["start_hour_day"] = START_HOUR_DAY
    results["end_hour_day"] = END_HOUR_DAY
    results["slot_duration"] = desired_slot_duration # Usar la duración deseada
    results["increment_time"] = INCREMENT
    results["total_professors"] = num_professors # Enviar el total de profesores al frontend

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)