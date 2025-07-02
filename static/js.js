document.addEventListener('DOMContentLoaded', () => {
    const runGAButton = document.getElementById('runGAButton');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const foundSlotDisplay = document.getElementById('foundSlotDisplay');
    const populationSizeInput = document.getElementById('populationSize');
    const generationsInput = document.getElementById('generations');
    const mutationRateInput = document.getElementById('mutationRate');
    const numProfessorsInput = document.getElementById('numProfessors'); // NUEVO: Input para cantidad de profesores
    const desiredSlotDurationInput = document.getElementById('desiredSlotDuration'); // NUEVO: Input para duración de slot libre
    const scheduleGridContainer = document.getElementById('scheduleGridContainer');
    const fitnessPlotContainer = document.getElementById('fitnessPlotContainer'); 

    runGAButton.addEventListener('click', async () => {
        // Validar entradas existentes
        const populationSize = parseInt(populationSizeInput.value);
        const generations = parseInt(generationsInput.value);
        const mutationRate = parseFloat(mutationRateInput.value);
        // Validar nuevas entradas
        const numProfessors = parseInt(numProfessorsInput.value);
        const desiredSlotDuration = parseFloat(desiredSlotDurationInput.value);

        if (isNaN(populationSize) || populationSize < 1 || populationSize > 1000) {
            alert("El tamaño de la población debe estar entre 1 y 1000.");
            return;
        }
        if (isNaN(generations) || generations < 5 || generations > 5000) {
            alert("El número de generaciones debe estar entre 5 y 5000.");
            return;
        }
        if (isNaN(mutationRate) || mutationRate < 0 || mutationRate > 1) {
            alert("La tasa de mutación debe estar entre 0.0 y 1.0.");
            return;
        }
        if (isNaN(numProfessors) || numProfessors < 1 || numProfessors > 15) { // Limita a 15 profesores por rendimiento visual/lógico
            alert("La cantidad de profesores debe estar entre 1 y 15.");
            return;
        }
        if (isNaN(desiredSlotDuration) || desiredSlotDuration <= 0 || desiredSlotDuration > 8) { // Ejemplo: slot de hasta 8h
            alert("La duración del slot libre debe ser un número positivo (ej. 0.5, 1.0, 2.0) y no exceder 8 horas.");
            return;
        }
        if (desiredSlotDuration % 0.5 !== 0) {
            alert("La duración del slot libre debe ser un múltiplo de 0.5 (ej. 1.0, 1.5, 2.0).");
            return;
        }


        // Mostrar spinner de carga
        loadingSpinner.style.display = 'flex';
        runGAButton.disabled = true;
        foundSlotDisplay.innerHTML = '<i class="fas fa-calendar-check"></i> Buscando horario...';
        
        // Limpiar visualizaciones anteriores
        scheduleGridContainer.innerHTML = ''; 
        fitnessPlotContainer.innerHTML = '<p style="text-align: center; color: #777;">Generando gráfica de evolución...</p>'; 

        try {
            const response = await fetch('http://127.0.0.1:5000/run_ga', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // ENVIAR NUEVOS PARÁMETROS AL BACKEND
                body: JSON.stringify({ 
                    population_size: populationSize, 
                    generations: generations, 
                    mutation_rate: mutationRate,
                    num_professors: numProfessors, // AÑADIDO
                    desired_slot_duration: desiredSlotDuration // AÑADIDO
                }),
            });

            if (!response.ok) {
                // Leer el mensaje de error del backend si está disponible
                const errorData = await response.json();
                throw new Error(errorData.error || `Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log(data);

            // Mostrar detalles del horario encontrado
            if (data.found_slot && data.found_slot.day) { 
                const numFree = data.found_slot.num_professors_free;
                const totalProfessors = data.found_slot.total_professors;
                const availableProfs = data.found_slot.professors_available_in_best_slot.join(', ');

                foundSlotDisplay.innerHTML = `
                    <i class="fas fa-calendar-check"></i> 
                    **Horario sugerido:** ${data.found_slot.day}, ${data.found_slot.start_time} - ${data.found_slot.end_time} (${data.slot_duration} horas)
                    <br>
                    <i class="fas fa-user-check"></i> 
                    **Profesores disponibles:** ${numFree} de ${totalProfessors} 
                    ${numFree > 0 ? `(${availableProfs})` : ''}
                `;
            } else {
                foundSlotDisplay.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i> 
                    No se encontró un horario común óptimo con los parámetros actuales. 
                    Intenta ajustar los parámetros o revisar los horarios de los profesores.
                `;
            }

            // Cargar Gráfica de Evolución del Fitness
            if (data.fitness_plot_url) {
                fitnessPlotContainer.innerHTML = ''; 
                const img = document.createElement('img');
                img.src = data.fitness_plot_url;
                img.alt = 'Gráfica de Evolución del Fitness';
                img.style.maxWidth = '100%'; 
                img.style.height = 'auto';
                img.style.display = 'block'; 
                img.style.margin = '0 auto'; 
                fitnessPlotContainer.appendChild(img);
            } else {
                fitnessPlotContainer.innerHTML = '<p style="text-align: center; color: #777;">No se pudo generar la gráfica de evolución del fitness.</p>';
            }
            
            // Visualización de Horarios
            drawProfessorSchedules(
                data.professor_schedules, 
                data.found_slot, 
                data.days_of_week, 
                data.possible_start_times, 
                data.start_hour_day,
                data.end_hour_day,
                data.slot_duration, // USAR LA DURACIÓN DINÁMICA
                data.increment_time
            );

        } catch (error) {
            console.error('Error al ejecutar el algoritmo genético:', error);
            foundSlotDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${error.message}. Verifica la consola del servidor.`;
            fitnessPlotContainer.innerHTML = '<p style="text-align: center; color: red;">Error al cargar la gráfica.</p>';
        } finally {
            // Ocultar spinner y habilitar botón
            loadingSpinner.style.display = 'none';
            runGAButton.disabled = false;
        }
    });

    function drawProfessorSchedules(professors, foundSlot, daysOfWeek, possibleStartTimes, startHourDay, endHourDay, slotDuration, incrementTime) {
        scheduleGridContainer.innerHTML = ''; 
        const totalHours = endHourDay - startHourDay;
        const numHourCells = Math.floor(totalHours / incrementTime); 

        for (const profName in professors) {
            const card = document.createElement('div');
            card.className = 'professor-schedule-card';
            card.innerHTML = `<h4>Horario de ${profName}</h4><canvas class="schedule-canvas"></canvas>`;
            scheduleGridContainer.appendChild(card);

            const canvas = card.querySelector('.schedule-canvas');
            const ctx = canvas.getContext('2d');

            const cellWidth = 90; 
            const cellHeight = 28; 
            const headerHeight = 35; 
            const timeColWidth = 65; 

            canvas.width = timeColWidth + (daysOfWeek.length * cellWidth);
            canvas.height = headerHeight + (numHourCells * cellHeight) + 5; 

            // Colores
            const occupiedColor = '#ffadad'; 
            const freeColor = '#d9ffda';     
            const commonSlotColor = '#8cff8c'; 

            // Dibujar fondo de libre
            ctx.fillStyle = freeColor;
            ctx.fillRect(timeColWidth, headerHeight, canvas.width - timeColWidth, canvas.height - headerHeight);

            // Dibujar grilla y etiquetas de días
            ctx.font = '12px Arial'; 
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#333';

            // Días
            for (let i = 0; i < daysOfWeek.length; i++) {
                ctx.fillText(daysOfWeek[i], timeColWidth + i * cellWidth + cellWidth / 2, headerHeight / 2);
                ctx.strokeRect(timeColWidth + i * cellWidth, 0, cellWidth, canvas.height); 
            }
            
            // Horas
            ctx.textAlign = 'right';
            ctx.textBaseline = 'top'; 
            ctx.font = '10px Arial'; 
            for (let i = 0; i <= numHourCells; i++) {
                const hour = startHourDay + (i * incrementTime);
                let displayHour = `${Math.floor(hour).toString().padStart(2, '0')}`;
                if (hour % 1 !== 0) { 
                    displayHour += ':30';
                } else {
                    displayHour += ':00';
                }
                ctx.fillText(displayHour, timeColWidth - 5, headerHeight + i * cellHeight + 2); 
                ctx.strokeRect(0, headerHeight + i * cellHeight, canvas.width, cellHeight); 
            }

            // Dibujar bloques ocupados del profesor
            ctx.fillStyle = occupiedColor;
            professors[profName].forEach(slot => {
                const dayIndex = daysOfWeek.indexOf(slot.day);
                if (dayIndex === -1) return;

                const startCell = (slot.start_hour - startHourDay) / incrementTime;
                const endCell = (slot.end_hour - startHourDay) / incrementTime;
                
                const x = timeColWidth + dayIndex * cellWidth;
                const y = headerHeight + startCell * cellHeight;
                const height = (endCell - startCell) * cellHeight;
                
                ctx.fillRect(x, y, cellWidth, height);
            });

            // Dibujar el horario común encontrado (si existe y este profesor está disponible)
            if (foundSlot && foundSlot.day && foundSlot.professors_available_in_best_slot.includes(profName)) {
                const commonDayIndex = daysOfWeek.indexOf(foundSlot.day);
                const commonStartHourParts = foundSlot.start_time.split(':').map(Number);
                const commonStartHour = commonStartHourParts[0] + (commonStartHourParts[1] / 60);
                
                // AHORA USA EL slotDuration DINÁMICO
                const commonEndHour = commonStartHour + slotDuration; 

                const startCell = (commonStartHour - startHourDay) / incrementTime;
                const endCell = (commonEndHour - startHourDay) / incrementTime;

                const x = timeColWidth + commonDayIndex * cellWidth;
                const y = headerHeight + startCell * cellHeight;
                const height = (endCell - startCell) * cellHeight;

                ctx.fillStyle = commonSlotColor;
                ctx.fillRect(x, y, cellWidth, height);

                ctx.strokeStyle = 'purple';
                ctx.lineWidth = 2;
                ctx.strokeRect(x, y, cellWidth, height);
                ctx.lineWidth = 1; 
                ctx.strokeStyle = '#ccc'; 
            }
        }
    }
});