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
        deuceRule: "oro", // "oro" o "ventaja"
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
                app.goToSetup(); // Usamos la función optimizada
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
                app.beeper(587, 200, 'sawtooth'); 
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
        app.setDeuceRule('oro');
        
        // Resetear el asistente visual para que siempre empiece en el Paso 1
        const step1 = document.getElementById('setup-step-1');
        const step2 = document.getElementById('setup-step-2');
        if (step1 && step2) {
            step1.classList.remove('hidden');
            step2.classList.add('hidden');
        }
    },

    // --- 🧙‍♂️ ASISTENTE GUIADO DE CONFIGURACIÓN ---
    seleccionarPaso1: (regla) => {
        app.setDeuceRule(regla);
        
        // Transición visual fluida al Paso 2
        document.getElementById('setup-step-1').classList.add('hidden');
        document.getElementById('setup-step-2').classList.remove('hidden');
        app.beeper(600, 100, 'sine');
    },

    volverAPaso1: () => {
        // Transición visual de regreso al Paso 1
        document.getElementById('setup-step-2').classList.add('hidden');
        document.getElementById('setup-step-1').classList.remove('hidden');
        app.beeper(400, 100, 'sine');
    },

    // --- 🎛️ SELECTOR DE FORMATOS DE PADEL TOH ---
    setFormat: (formato) => {
        app.datos.formatoSelected = formato;
        
        const formatosIds = {
            '3_SETS_6_G': 'btn-f1',
            '3_SHORT_4_G': 'btn-f2',
            '1_SET_6_G': 'btn-f3',
            '1_SHORT_4_G': 'btn-f4'
        };
        
        Object.values(formatosIds).forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.remove('active');
        });
        
        if (formato === '3_SETS_6_G') { app.datos.setsParaGanar = 2; app.datos.gamesParaGanarSet = 6; }
        else if (formato === '3_SHORT_4_G') { app.datos.setsParaGanar = 2; app.datos.gamesParaGanarSet = 4; }
        else if (formato === '1_SET_6_G') { app.datos.setsParaGanar = 1; app.datos.gamesParaGanarSet = 6; }
        else if (formato === '1_SHORT_4_G') { app.datos.setsParaGanar = 1; app.datos.gamesParaGanarSet = 4; }
        
        const btnActivo = document.getElementById(formatosIds[formato]);
        if (btnActivo) btnActivo.classList.add('active');
        
        console.log(`⚙️ [TOH ARBITRO] Formato cargado: ${formato} | Sets: ${app.datos.setsParaGanar} | Games: ${app.datos.gamesParaGanarSet}`);
    },

    // --- 🛡️ SELECTOR DE REGLA EN EMPATE 40-40 ---
    setDeuceRule: (regla) => {
        app.datos.deuceRule = regla;
        
        const btnOro = document.getElementById('btn-deuce-oro');
        const btnVentaja = document.getElementById('btn-deuce-ventaja');
        
        if (btnOro) btnOro.classList.toggle('active', regla === 'oro');
        if (btnVentaja) btnVentaja.classList.toggle('active', regla === 'ventaja');
        
        console.log(`⚙️ [TOH ARBITRO] Regla de empate configurada: ${regla.toUpperCase()}`);
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
            // B. LÓGICA DE JUEGO NORMAL (0, 15, 30, 40, ADV, ORO)
            const p_actual = jugador === 1 ? app.datos.puntos1 : app.datos.puntos2;
            const p_rival = jugador === 1 ? app.datos.puntos2 : app.datos.puntos1;

            if (p_actual === 0) {
                if (jugador === 1) app.datos.puntos1 = 15; else app.datos.puntos2 = 15;
            } else if (p_actual === 15) {
                if (jugador === 1) app.datos.puntos1 = 30; else app.datos.puntos2 = 30;
            } else if (p_actual === 30) {
                if (jugador === 1) app.datos.puntos1 = 40; else app.datos.puntos2 = 40;
                
                // Si llegamos a 40-40, activamos la alarma
                if (p_rival === 40) {
                    if (app.datos.deuceRule === 'oro') {
                        app.beeper(220, 500, 'sawtooth'); // Alarma dorada
                        console.log("⚔️ [PUNTO DE ORO] ¡Punto de oro activado en la Arena!");
                    } else {
                        app.beeper(440, 200, 'sine'); // Aviso de deuce normal
                        console.log("↔️ [DEUCE] Iguales. Sistema de Ventajas activado.");
                    }
                }
            } else if (p_actual === 40) {
                // Caso 1: Punto de Oro (Gana de inmediato)
                if (app.datos.deuceRule === 'oro') {
                    app.ganarJuego(jugador);
                    return;
                }
                
                // Caso 2: Sistema de Ventajas tradicional
                if (p_rival === 40) {
                    // Estaban iguales (40-40), el jugador gana la ventaja (ADV)
                    if (jugador === 1) {
                        app.datos.puntos1 = "ADV";
                        app.datos.puntos2 = "40";
                    } else {
                        app.datos.puntos2 = "ADV";
                        app.datos.puntos1 = "40";
                    }
                    app.beeper(700, 100, 'sine');
                } else if (p_rival === "ADV") {
                    // El rival tenía ventaja, volvemos a Iguales (40-40)
                    app.datos.puntos1 = 40;
                    app.datos.puntos2 = 40;
                    app.beeper(440, 300, 'sine');
                } else {
                    // Tenías ventaja o el rival tenía menos de 40 -> Ganas el juego!
                    app.ganarJuego(jugador);
                    return;
                }
            } else if (p_actual === "ADV") {
                // El jugador tenía ventaja y hace el punto -> Gana el juego!
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

        // Caso 1: Tie-break (llegaron al límite)
        if (g1 === limite && g2 === limite) {
            app.datos.tieBreakActivo = true;
            app.beeper(523, 400, 'sine');
            console.log("🔥 [TIE-BREAK] ¡Muerte súbita activada!");
            return;
        }

        // Caso 2: Ganó el set por diferencia de 2
        if ((g1 >= limite || g2 >= limite) && Math.abs(g1 - g2) >= 2) {
            const ganadorSet = g1 > g2 ? 1 : 2;
            app.datos.historialSets.push(`${g1}-${g2}`);
            
            if (ganadorSet === 1) app.datos.sets1++; else app.datos.sets2++;
            
            app.datos.games1 = 0;
            app.datos.games2 = 0;

            if (app.datos.sets1 === app.datos.setsParaGanar || app.datos.sets2 === app.datos.setsParaGanar) {
                app.terminarPartido();
            } else {
                setTimeout(() => app.startTimer(120), 500); // Descanso fin de set
            }
            return;
        }

        // Caso 3: Cambio de lado en games impares
        const gamesSumados = g1 + g2;
        if (gamesSumados % 2 !== 0) {
            setTimeout(() => app.startTimer(90), 500); // Descanso cambio de lado
        }
    },

    verificarTieBreak: () => {
        const p1 = app.datos.puntos1;
        const p2 = app.datos.puntos2;
        
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
        
        if (app.datos.puntos1 === 40 && app.datos.puntos2 === 40 && app.datos.deuceRule === 'oro') {
            document.getElementById('score-p1').innerHTML = `<span style="color: var(--neon-gold); text-shadow: 0 0 15px rgba(255,204,0,0.5);">ORO</span>`;
            document.getElementById('score-p2').innerHTML = `<span style="color: var(--neon-gold); text-shadow: 0 0 15px rgba(255,204,0,0.5);">ORO</span>`;
        } else {
            document.getElementById('score-p1').innerText = app.datos.puntos1 === 0 ? "00" : app.datos.puntos1;
            document.getElementById('score-p2').innerText = app.datos.puntos2 === 0 ? "00" : app.datos.puntos2;
        }

        document.getElementById('sets-p1').innerText = app.datos.games1;
        document.getElementById('sets-p2').innerText = app.datos.games2;
    },

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