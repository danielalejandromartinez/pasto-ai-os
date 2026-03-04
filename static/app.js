const app = {
    datos: {
        matchId: null, 
        clubId: 1, // Por defecto al Club 1
        categoria: "General", 
        nombre1: "JUGADOR A", 
        nombre2: "JUGADOR B", 
        puntos1: 0, 
        puntos2: 0,
        sets1: 0, 
        sets2: 0, 
        setsParaGanar: 3, 
        historialSets: [], 
        historialPuntos: [],
        enviando: false,
        // 🔐 LLAVE DE COMANDO MAESTRA
        passcode: "2026"
    },

    // 📡 CONEXIÓN AL BACKEND DE PYTHON (PASTO.AI OS)
    apiUrl: "/api/match/finish",
    timerInterval: null,

    init: () => {
        console.log("🚀 [SISTEMA] Inicializando Interfaz de Referí 2030...");
        console.log("🔐 [SEGURIDAD] Sincronizando Capas de Protección...");
        
        // 1. OBSERVAR: Capturamos datos de la URL (Misión encomendada por el Orquestador)
        const params = new URLSearchParams(window.location.search);
        if (params.has('matchId')) {
            app.datos.matchId = params.get('matchId');
            app.datos.categoria = params.get('cat') || "General";
            
            // 2. INTERPRETAR: Ponemos los nombres en los cuadros de texto (en silencio detrás del bloqueo)
            document.getElementById('input-p1').value = params.get('p1');
            document.getElementById('input-p2').value = params.get('p2');
            
            console.log(`✅ [SISTEMA] Duelo Sincronizado: ID ${app.datos.matchId} | ${params.get('p1')} vs ${params.get('p2')}`);
            console.log("⚠️ [ESTADO] Terminal bloqueada. Esperando autorización de Árbitro...");
        }
    },

    // 🔐 FUNCIÓN DE DESBLOQUEO (EL CERROJO DEL BÚNKER)
    unlock: () => {
        const inputPin = document.getElementById('ref-passcode').value;
        const errorMsg = document.getElementById('lock-error');

        if (inputPin === app.datos.passcode) {
            // ÉXITO: Liberar el sistema
            app.beeper(880, 150, 'sine'); // Sonido de acceso concedido
            document.getElementById('screen-lock').classList.remove('active');
            
            // Si venimos de un reto confirmado en la web, vamos directo a Configuración
            if (app.datos.matchId) {
                app.mostrarPantalla('screen-setup');
                console.log("🔓 [SEGURIDAD] Llave aceptada. Sincronizando con la Arena...");
            } else {
                app.mostrarPantalla('screen-home');
                console.log("🔓 [SEGURIDAD] Llave aceptada. Sistema en modo espera.");
            }
        } else {
            // FALLO: Bloqueo de intruso
            app.beeper(110, 500, 'sawtooth'); // Sonido de alerta grave
            errorMsg.style.display = 'block';
            document.getElementById('ref-passcode').value = ""; // Limpiar campo
            console.error("⚠️ [ALERTA] Intento de acceso no autorizado detectado en la terminal.");
            
            // Ocultar error después de unos segundos
            setTimeout(() => {
                errorMsg.style.display = 'none';
            }, 3000);
        }
    },

    // --- 🔊 MOTOR DE AUDIO SINTETIZADO ---
    beeper: (freq, duration, type = 'square') => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = type; osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            osc.start(); setTimeout(() => osc.stop(), duration);
        } catch(e) { console.log("Audio no disponible"); }
    },

    // --- ⏱️ GESTIÓN DEL TIEMPO (REST MODE) ---
    startTimer: () => {
        app.mostrarPantalla('screen-timer');
        app.beeper(400, 600);
        let timeLeft = 90;
        const display = document.getElementById('timer-display');
        display.classList.remove('timer-urgent');

        app.timerInterval = setInterval(() => {
            timeLeft--;
            let mins = Math.floor(timeLeft / 60);
            let secs = timeLeft % 60;
            display.innerText = `${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`;

            if (timeLeft === 15) {
                app.beeper(600, 200);
                display.classList.add('timer-urgent');
            }

            if (timeLeft <= 0) app.skipTimer();
        }, 1000);
    },

    skipTimer: () => {
        clearInterval(app.timerInterval);
        app.beeper(300, 800);
        app.mostrarPantalla('screen-match');
        app.actualizarPantalla();
    },

    // --- LÓGICA DE CONTROL ---
    mostrarPantalla: (id) => {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    },

    // Función de apoyo para que el botón de inicio funcione
    goToSetup: () => {
        app.mostrarPantalla('screen-setup');
    },

    setFormat: (cantidad) => {
        app.datos.setsParaGanar = cantidad;
        document.getElementById('btn-m3').classList.toggle('active', cantidad === 2);
        document.getElementById('btn-m5').classList.toggle('active', cantidad === 3);
        console.log(`⚙️ [SISTEMA] Formato ajustado: Al mejor de ${cantidad === 2 ? '3' : '5'}`);
    },
    
    startMatch: () => {
        app.datos.nombre1 = document.getElementById('input-p1').value.toUpperCase() || "A";
        app.datos.nombre2 = document.getElementById('input-p2').value.toUpperCase() || "B";
        app.datos.puntos1 = 0; app.datos.puntos2 = 0; app.datos.sets1 = 0; app.datos.sets2 = 0;
        app.datos.historialSets = []; app.datos.historialPuntos = [];
        app.datos.enviando = false;
        
        app.actualizarPantalla();
        app.mostrarPantalla('screen-match');
        app.beeper(500, 200, 'sine');
        console.log("⚔️ [SISTEMA] Motor de combate inicializado.");
    },

    addPoint: (jugador) => {
        app.datos.historialPuntos.push(JSON.stringify({p1: app.datos.puntos1, p2: app.datos.puntos2, s1: app.datos.sets1, s2: app.datos.sets2}));
        if (jugador === 1) app.datos.puntos1++; else app.datos.puntos2++;
        app.beeper(800, 50, 'sine');
        app.verificarSet(); 
        app.actualizarPantalla();
    },

    verificarSet: () => {
        const p1 = app.datos.puntos1; const p2 = app.datos.puntos2;
        if ((p1 >= 11 || p2 >= 11) && Math.abs(p1 - p2) >= 2) {
            const ganadorSet = p1 > p2 ? 1 : 2;
            app.datos.historialSets.push(`${p1}-${p2}`);
            if (ganadorSet === 1) app.datos.sets1++; else app.datos.sets2++;
            app.datos.puntos1 = 0; app.datos.puntos2 = 0;
            app.datos.historialPuntos = [];

            if (app.datos.sets1 === app.datos.setsParaGanar || app.datos.sets2 === app.datos.setsParaGanar) {
                app.terminarPartido();
            } else {
                setTimeout(() => app.startTimer(), 500);
            }
        }
    },

    terminarPartido: () => {
        const ganador = app.datos.sets1 > app.datos.sets2 ? app.datos.nombre1 : app.datos.nombre2;
        document.getElementById('winner-name').innerText = ganador;
        document.getElementById('final-sets').innerText = `${app.datos.sets1} - ${app.datos.sets2}`;
        app.mostrarPantalla('screen-result');
        app.beeper(880, 1000, 'sawtooth');
        console.log(`🏁 [SISTEMA] Ciclo finalizado. Dominador: ${ganador}`);
    },

    actualizarPantalla: () => {
        document.getElementById('name-p1').innerText = app.datos.nombre1;
        document.getElementById('name-p2').innerText = app.datos.nombre2;
        document.getElementById('score-p1').innerText = app.datos.puntos1.toString().padStart(2, '0');
        document.getElementById('score-p2').innerText = app.datos.puntos2.toString().padStart(2, '0');
        document.getElementById('sets-p1').innerText = app.datos.sets1;
        document.getElementById('sets-p2').innerText = app.datos.sets2;
    },

    // 🚀 REPORTE AL HUB: Envía la señal a Python
    reset: async () => { 
        if (app.datos.enviando) return;
        
        // Si no hay un ganador definido, es porque cancelaron la misión
        if (app.datos.sets1 < app.datos.setsParaGanar && app.datos.sets2 < app.datos.setsParaGanar) {
            console.log("⚠️ [SISTEMA] Misión abortada por el usuario.");
            window.location.href = "/club/1";
            return;
        }

        app.datos.enviando = true;
        const ganador = app.datos.sets1 > app.datos.sets2 ? app.datos.nombre1 : app.datos.nombre2;
        
        console.log(`📡 [SISTEMA] Reportando resultado al Hub de Pasto.AI...`);

        try {
            const response = await fetch(app.apiUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    matchId: app.datos.matchId,
                    cat: app.datos.categoria,
                    res: `${app.datos.sets1}-${app.datos.sets2}`,
                    ganador: ganador,
                    parciales: app.datos.historialSets
                })
            });

            if (response.ok) {
                console.log("✅ [SISTEMA] Transmisión exitosa. Ranking actualizado.");
                window.location.href = "/club/1"; 
            } else {
                const errData = await response.json();
                alert(`Error en el Hub: ${errData.mensaje || 'Desconocido'}`);
                app.datos.enviando = false;
            }
        } catch (error) {
            console.error("❌ [ERROR] Fallo crítico de comunicación:", error);
            alert("No se pudo conectar con el Hub. Verifica que el servidor esté encendido.");
            app.datos.enviando = false;
        }
    },

    undo: () => { 
        if (app.datos.historialPuntos.length > 0) {
            const f = JSON.parse(app.datos.historialPuntos.pop());
            app.datos.puntos1 = f.p1; app.datos.puntos2 = f.p2;
            app.datos.sets1 = f.s1; app.datos.sets2 = f.s2;
            app.actualizarPantalla();
            app.beeper(200, 100);
            console.log("↩️ [SISTEMA] Movimiento corregido.");
        }
    }
};

window.onload = app.init;