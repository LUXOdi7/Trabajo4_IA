document.addEventListener('DOMContentLoaded', () => {
    const runGAButton = document.getElementById('runGAButton');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const foundSlotDisplay = document.getElementById('foundSlotDisplay');
    const populationSizeInput = document.getElementById('populationSize');
    const generationsInput = document.getElementById('generations');
    const mutationRateInput = document.getElementById('mutationRate');
    const scheduleGridContainer = document.getElementById('scheduleGridContainer');
    const fitnessPlotContainer = document.getElementById('fitnessPlotContainer'); 

    runGAButton.addEventListener('click', async () => {
        // Validar entradas
        const populationSize = parseInt(populationSizeInput.value);
        const generations = parseInt(generationsInput.value);
        const mutationRate = parseFloat(mutationRateInput.value);

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
                body: JSON.stringify({ population_size: populationSize, generations: generations, mutation_rate: mutationRate }),
            });

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log(data);

            // Actualizar display del horario encontrado
            if (data.found_slot) {
                foundSlotDisplay.innerHTML = `
                    <i class="fas fa-calendar-check"></i> 
                    ${data.found_slot.day}, ${data.found_slot.start_time} - ${data.found_slot.end_time}
                `;
            } else {
                foundSlotDisplay.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i> 
                    No se encontró un horario común de 2 horas con los parámetros actuales.
                `;
            }

            // --- Cargar Gráfica de Evolución del Fitness (imagen estática) ---
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
            
            // --- Visualización de Horarios ---
            drawProfessorSchedules(
                data.professor_schedules, 
                data.found_slot, 
                data.days_of_week, 
                data.possible_start_times, 
                data.start_hour_day,
                data.end_hour_day,
                data.slot_duration,
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

            // Ajustes para dar más espacio a los horarios
            const cellWidth = 90; // Ancho de celda aumentado
            const cellHeight = 28; // Alto de celda aumentado
            const headerHeight = 35; // Altura del encabezado de días
            const timeColWidth = 65; // Ancho de la columna de tiempo

            canvas.width = timeColWidth + (daysOfWeek.length * cellWidth);
            canvas.height = headerHeight + (numHourCells * cellHeight) + 5; // Un poco de padding extra al final

            // Colores
            const occupiedColor = '#ffadad'; 
            const freeColor = '#d9ffda';     
            const commonSlotColor = '#8cff8c'; 

            // Dibujar fondo de libre
            ctx.fillStyle = freeColor;
            ctx.fillRect(timeColWidth, headerHeight, canvas.width - timeColWidth, canvas.height - headerHeight);

            // Dibujar grilla y etiquetas de días
            ctx.font = '12px Arial'; // Fuente ligeramente más grande
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
            ctx.textBaseline = 'top'; // Alinea texto a la parte superior de la celda
            ctx.font = '10px Arial'; // Fuente más pequeña para las horas
            for (let i = 0; i <= numHourCells; i++) {
                const hour = startHourDay + (i * incrementTime);
                let displayHour = `${Math.floor(hour).toString().padStart(2, '0')}`;
                if (hour % 1 !== 0) { 
                    displayHour += ':30';
                } else {
                    displayHour += ':00';
                }
                ctx.fillText(displayHour, timeColWidth - 5, headerHeight + i * cellHeight + 2); // Ajuste vertical
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

            // Dibujar el horario común encontrado (si existe)
            if (foundSlot) {
                const commonDayIndex = daysOfWeek.indexOf(foundSlot.day);
                const commonStartHour = parseFloat(foundSlot.start_time.split(':')[0]) + (parseFloat(foundSlot.start_time.split(':')[1]) / 60);
                const commonEndHour = parseFloat(foundSlot.end_time.split(':')[0]) + (parseFloat(foundSlot.end_time.split(':')[1]) / 60);

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