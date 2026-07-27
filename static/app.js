const app = {
    datos: {
        matchId: null, 
        clubId: 1, 
        categoria: "General", 
        nombre1: "PAREJA A", 
        nombre2: "PAREJA B", 
        puntos1: 0, // Puntos de Game: 0, 15, 30, 40
        puntos2: 0,
        games1: 0,  // Games ganados en el set actual
        games2: 0,
        sets1: 0,   // Sets ganados en el partido
        sets2: 0, 
        
        // Configuración dinámica por formato de Padel
        formatoSelected: "3_SETS_6_G",
        setsParaGanar: 2, 
        gamesParaGanarSet: 6,
        tieBreakActivo: false,

        historialSets: [], 
        historialPuntos: [],
        enviando: false,
        passcode: "2026"
    },

    apiUrl: "/api/match/finish",
    timerInterval: null,

    init: () => {
        console.log("🚀 [TOH ARBITRO] Inicializando Consola de Padel 2050...");
        
        const params = new URLSearchParams(window.location.search);
        if (params.has('matchId')) {
            app.datos.matchId = params.get('matchId');
            app.datos.categoria = params.get('cat') || "General";
            
            document.getElementById('input-p1').value = params.get('p1');
            document.getElementById('input-p2').value = params.get('p2');
            
            console.log(`✅ [TOH ARBITRO] Duelo Sincronizado: ID ${app.datos.matchId} | ${params.get('p1')} vs ${params.get('p2')}`);
        }
    },

    unlock: () => {
        const inputPin = document.getElementById('ref-passcode').value;
        const errorMsg = document.getElementById('lock-error');

        if (inputPin === app.datos.passcode) {
            app.beeper(880, 150, 'sine');
            document.getElementById('screen-lock').classList.remove('active');
            
            if (app.datos.matchId) {
                app.mostrarPantalla('screen-setup');
                app.setFormat('3_SETS_6_G'); // Formato por defecto al iniciar
            } else {
                app.mostrarPantalla('screen-home');
            }
        } else {
            app.beeper(110, 500, 'sawtooth');
            errorMsg.style.display = 'block';
            document.getElementById('ref-passcode').value = "";
            setTimeout(() => { errorMsg.style.display = 'none'; }, 3000);
        }
    },

    beeper: (freq, duration, type = 'square') => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = type; osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.05, ctx.currentTime);
            osc.start(); setTimeout(() => osc.stop(), duration);
        } catch(e) {}
    },

    startTimer: (segundos) => {
        app.mostrarPantalla('screen-timer');
        app.beeper(440, 400, 'sine');
        let timeLeft = segundos;
        const display = document.getElementById('timer-display');
        display.classList.remove('timer-urgent');

        app.timerInterval = setInterval(() => {
            timeLeft--;
            let mins = Math.floor(timeLeft / 60);
            let secs = timeLeft % 60;
            display.innerText = `${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`;

            if (timeLeft === 15) {
                app.beeper(587, 200, 'sawtooth'); // Aviso sonoro sutil de 15s
                display.classList.add('timer-urgent');
            }

            if (timeLeft <= 0) app.skipTimer();
        }, 1000);
    },

    skipTimer: () => {
        clearInterval(app.timerInterval);
        app.beeper(880, 200, 'sine');
        app.mostrarPantalla('screen-match');
        app.actualizarPantalla();
    },

    mostrarPantalla: (id) => {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    },

    goToSetup: () => {
        app.mostrarPantalla('screen-setup');
        app.setFormat('3_SETS_6_G');
    },

    // --- 🎛️ SELECTOR DE FORMATOS DE PADEL TOH ---
    setFormat: (formato) => {
        app.datos.formatoSelected = formato;
        
        // Quitamos la iluminación de neón a todos los botones
        document.querySelectorAll('.btn-mode').forEach(btn => btn.classList.remove('active'));
        
        let btnId = '';
        if (formato === '3_SETS_6_G') { btnId = 'btn-f1'; app.datos.setsParaGanar = 2; app.datos.gamesParaGanarSet = 6; }
        else if (formato === '3_SHORT_4_G') { btnId = 'btn-f2'; app.datos.setsParaGanar = 2; app.datos.gamesParaGanarSet = 4; }
        else if (formato === '1_SET_6_G') { btnId = 'btn-f3'; app.datos.setsParaGanar = 1; app.datos.gamesParaGanarSet = 6; }
        else if (formato === '1_SHORT_4_G') { btnId = 'btn-f4'; app.datos.setsParaGanar = 1; app.datos.gamesParaGanarSet = 4; }
        
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.add('active');
        
        console.log(`⚙️ [TOH ARBITRO] Formato cargado: ${formato} | Sets: ${app.datos.setsParaGanar} | Games: ${app.datos.gamesParaGanarSet}`);
    },
    
    startMatch: () => {
        app.datos.nombre1 = document.getElementById('input-p1').value.toUpperCase() || "PAREJA A";
        app.datos.nombre2 = document.getElementById('input-p2').value.toUpperCase() || "PAREJA B";
        app.datos.puntos1 = 0; app.datos.puntos2 = 0;
        app.datos.games1 = 0; app.datos.games2 = 0;
        app.datos.sets1 = 0; app.datos.sets2 = 0;
        app.datos.tieBreakActivo = false;
        app.datos.historialSets = []; app.datos.historialPuntos = [];
        app.datos.enviando = false;
        
        app.actualizarPantalla();
        app.mostrarPantalla('screen-match');
        app.beeper(659, 300, 'sine');
        console.log("⚔️ [TOH ARBITRO] Motor de Padel Inicializado. ¡A jugar!");
    },

    // --- 🎾 MOTOR DE PUNTOS OFICIAL FIP (PADEL ENGINE) ---
    addPoint: (jugador) => {
        // Guardamos historial para la función deshacer (Undo)
        app.datos.historialPuntos.push(JSON.stringify({
            p1: app.datos.puntos1, p2: app.datos.puntos2,
            g1: app.datos.games1, g2: app.datos.games2,
            s1: app.datos.sets1, s2: app.datos.sets2,
            tb: app.datos.tieBreakActivo
        }));

        if (app.datos.tieBreakActivo) {
            // A. LÓGICA DE TIE-BREAK (Puntos numéricos: 1, 2, 3...)
            if (jugador === 1) app.datos.puntos1++; else app.datos.puntos2++;
            app.beeper(880, 80, 'sine');
            app.verificarTieBreak();
        } else {
            // B. LÓGICA DE JUEGO NORMAL (0, 15, 30, 40, ORO)
            const p_actual = jugador === 1 ? app.datos.puntos1 : app.datos.puntos2;
            const p_rival = jugador === 1 ? app.datos.puntos2 : app.datos.puntos1;

            if (p_actual === 0) {
                if (jugador === 1) app.datos.puntos1 = 15; else app.datos.puntos2 = 15;
            } else if (p_actual === 15) {
                if (jugador === 1) app.datos.puntos1 = 30; else app.datos.puntos2 = 30;
            } else if (p_actual === 30) {
                if (jugador === 1) app.datos.puntos1 = 40; else app.datos.puntos2 = 40;
                
                // Si llegamos a 40-40, activamos el "Punto de Oro"
                if (p_rival === 40) {
                    app.beeper(220, 500, 'sawtooth'); // Alarma dramática
                    console.log("⚔️ [PUNTO DE ORO] ¡Punto de oro activado en la Arena!");
                }
            } else if (p_actual === 40) {
                // Ganó el game!
                app.ganarJuego(jugador);
                return;
            }
            app.beeper(600, 50, 'sine');
        }
        app.actualizarPantalla();
    },

    ganarJuego: (ganador) => {
        app.beeper(987, 250, 'sine');
        if (ganador === 1) app.datos.games1++; else app.datos.games2++;
        
        // Reset de puntos del game
        app.datos.puntos1 = 0;
        app.datos.puntos2 = 0;
        app.datos.tieBreakActivo = false;
        
        app.verificarSet();
        app.actualizarPantalla();
    },

    verificarSet: () => {
        const g1 = app.datos.games1;
        const g2 = app.datos.games2;
        const limite = app.datos.gamesParaGanarSet;

        // Caso 1: Tie-break (llegaron a 6-6 o 4-4 en short set)
        if (g1 === limite && g2 === limite) {
            app.datos.tieBreakActivo = true;
            app.beeper(523, 400, 'sine');
            console.log("🔥 [TIE-BREAK] ¡Muerte súbita activada!");
            return;
        }

        // Caso 2: Ganó el set por diferencia de 2 games (ej: 6-4, 4-2)
        if ((g1 >= limite || g2 >= limite) && Math.abs(g1 - g2) >= 2) {
            const ganadorSet = g1 > g2 ? 1 : 2;
            app.datos.historialSets.push(`${g1}-${g2}`);
            
            if (ganadorSet === 1) app.datos.sets1++; else app.datos.sets2++;
            
            app.datos.games1 = 0;
            app.datos.games2 = 0;

            if (app.datos.sets1 === app.datos.setsParaGanar || app.datos.sets2 === app.datos.setsParaGanar) {
                app.terminarPartido();
            } else {
                // Descanso Fin de Set: 2 minutos (120s)
                setTimeout(() => app.startTimer(120), 500);
            }
            return;
        }

        // Caso 3: Cambio de lado (Games impares sumados: 1-0, 2-1, 3-2...)
        const gamesSumados = g1 + g2;
        if (gamesSumados % 2 !== 0) {
            // Descanso Cambio de Lado: 90 segundos
            setTimeout(() => app.startTimer(90), 500);
        }
    },

    verificarTieBreak: () => {
        const p1 = app.datos.puntos1;
        const p2 = app.datos.puntos2;
        
        // El primero que llegue a 7 con diferencia de 2 gana el tie break
        if ((p1 >= 7 || p2 >= 7) && Math.abs(p1 - p2) >= 2) {
            const ganadorSet = p1 > p2 ? 1 : 2;
            
            if (ganadorSet === 1) app.datos.games1++; else app.datos.games2++;
            app.datos.historialSets.push(`${app.datos.games1}-${app.datos.games2}`);
            
            if (ganadorSet === 1) app.datos.sets1++; else app.datos.sets2++;
            
            app.datos.puntos1 = 0; app.datos.puntos2 = 0;
            app.datos.games1 = 0; app.datos.games2 = 0;
            app.datos.tieBreakActivo = false;

            if (app.datos.sets1 === app.datos.setsParaGanar || app.datos.sets2 === app.datos.setsParaGanar) {
                app.terminarPartido();
            } else {
                setTimeout(() => app.startTimer(120), 500);
            }
        }
    },

    terminarPartido: () => {
        const ganador = app.datos.sets1 > app.datos.sets2 ? app.datos.nombre1 : app.datos.nombre2;
        document.getElementById('winner-name').innerText = ganador;
        document.getElementById('final-sets').innerText = `${app.datos.sets1} - ${app.datos.sets2} (${app.datos.historialSets.join(', ')})`;
        app.mostrarPantalla('screen-result');
        app.beeper(880, 1000, 'sawtooth');
        console.log(`🏁 [TOH ARBITRO] Ciclo finalizado. Ganador: ${ganador}`);
    },

    actualizarPantalla: () => {
        document.getElementById('name-p1').innerText = app.datos.nombre1;
        document.getElementById('name-p2').innerText = app.datos.nombre2;
        
        // Si hay deuce 40-40, mostramos la palabra "ORO" (Punto de Oro) en neón dorado
        if (app.datos.puntos1 === 40 && app.datos.puntos2 === 40) {
            document.getElementById('score-p1').innerHTML = `<span style="color: var(--neon-gold); text-shadow: 0 0 15px rgba(255,204,0,0.5);">ORO</span>`;
            document.getElementById('score-p2').innerHTML = `<span style="color: var(--neon-gold); text-shadow: 0 0 15px rgba(255,204,0,0.5);">ORO</span>`;
        } else {
            document.getElementById('score-p1').innerText = app.datos.puntos1.toString().padStart(2, '0');
            document.getElementById('score-p2').innerText = app.datos.puntos2.toString().padStart(2, '0');
        }

        // El score principal muestra los juegos (games) ganados en el set actual
        document.getElementById('sets-p1').innerText = app.datos.games1;
        document.getElementById('sets-p2').innerText = app.datos.games2;
    },

    // --- 📡 REPORTE PERSISTENTE AL HUB EN RENDER ---
    reset: async () => { 
        if (app.datos.enviando) return;
        
        if (app.datos.sets1 < app.datos.setsParaGanar && app.datos.sets2 < app.datos.setsParaGanar) {
            console.log("⚠️ [TOH ARBITRO] Partido cancelado por el referí.");
            window.location.href = "/club/1";
            return;
        }

        app.datos.enviando = true;
        const ganador = app.datos.sets1 > app.datos.sets2 ? app.datos.nombre1 : app.datos.nombre2;
        
        console.log(`📡 [TOH ARBITRO] Transmitiendo resultado al Muro de la Fama...`);

        try {
            const response = await fetch(app.apiUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    matchId: app.datos.matchId,
                    cat: app.datos.categoria,
                    res: `${app.datos.sets1}-${app.datos.sets2}`,
                    ganador: ganador,
                    parciales: app.datos.historialSets.join(', ')
                })
            });

            if (response.ok) {
                console.log("✅ [TOH ARBITRO] Sincronización de puntos exitosa.");
                window.location.href = "/club/1"; 
            } else {
                const errData = await response.json();
                alert(`Error en el servidor: ${errData.mensaje || 'Desconocido'}`);
                app.datos.enviando = false;
            }
        } catch (error) {
            console.error("❌ [ERROR CRÍTICO] Fallo de transmisión:", error);
            alert("Fallo de red. Verifica la conexión.");
            app.datos.enviando = false;
        }
    },

    undo: () => { 
        if (app.datos.historialPuntos.length > 0) {
            const f = JSON.parse(app.datos.historialPuntos.pop());
            app.datos.puntos1 = f.p1; app.datos.puntos2 = f.p2;
            app.datos.games1 = f.g1; app.datos.games2 = f.g2;
            app.datos.sets1 = f.s1; app.datos.sets2 = f.s2;
            app.datos.tieBreakActivo = f.tb;
            app.actualizarPantalla();
            app.beeper(200, 100);
            console.log("↩️ [SISTEMA] Movimiento corregido.");
        }
    }
};

window.onload = app.init;