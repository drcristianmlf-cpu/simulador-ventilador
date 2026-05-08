import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Ventilador Pro VariedadesMx", layout="wide")
st.markdown("<style>.stApp {background-color: #050505; color: #00FF41;}</style>", unsafe_allow_html=True)

# --- FUNCIONES DE CÁLCULO ANTROPOMÉTRICO ---
def calcular_peso_ideal(talla, sexo):
    if sexo == "Masculino":
        return 50 + 0.91 * (talla - 152.4)
    else:
        return 45.5 + 0.91 * (talla - 152.4)

# --- MOTOR DE VENTILACIÓN ---
def simular_ventilacion(modo, pat, vt, fr, peep, fio2, pres_insp, ps, ie_ratio, peso_id):
    # Parámetros de patología
    params = {
        "Normal": {"c": 50, "r": 5, "base_gc": 5.0},
        "SDRA": {"c": 18, "r": 8, "base_gc": 4.5},
        "Asma": {"c": 55, "r": 45, "base_gc": 4.8},
        "IAM Derecho": {"c": 45, "r": 5, "base_gc": 3.2}
    }
    p = params[pat]
    c, r = p["c"], p["r"]
    
    # Lógica según Modo Ventilatorio
    if modo == "AC-Volumen":
        p_plat = (vt / c) + peep
        p_pico = p_plat + (r * 0.5)
        vt_real = vt
    elif modo == "AC-Presión":
        p_pico = pres_insp + peep
        p_plat = p_pico - 2 # Simplificado
        vt_real = (p_pico - peep) * c
    else: # PSV (Espontáneo)
        p_pico = ps + peep
        p_plat = p_pico - 1
        vt_real = (ps) * c
        fr = fr + 4 # Simular esfuerzo del paciente

    # Hemodinamia e Interacción
    p_mean = (p_plat + peep) / 2
    gc = p["base_gc"] - (peep * 0.1) - (p_mean * 0.05)
    if pat == "IAM Derecho": gc -= (peep * 0.3)
    
    # Gasometría Dinámica
    ve = (vt_real * fr) / 1000 # Volumen Minuto
    paco2 = 40 * (8 / ve) # Relación inversa flujo/CO2
    ph = 7.4 - (0.008 * (paco2 - 40))
    pao2 = (fio2 * (760 - 47)) - (paco2 / 0.8)
    spo2 = min(100, 85 + (pao2 / 10))

    return p_pico, p_plat, vt_real, round(gc,2), round(ph,2), round(paco2), round(spo2), round(ve,1)

# --- INTERFAZ DE USUARIO ---
st.title("📟 Estación de Ventilación Mecánica Avanzada")

# Sidebar: Datos del Paciente
with st.sidebar:
    st.header("👤 Datos Antropométricos")
    sexo = st.radio("Sexo:", ["Masculino", "Femenino"])
    talla = st.number_input("Talla (cm):", 140, 210, 170)
    edad = st.number_input("Edad:", 18, 99, 45)
    pi = calcular_peso_ideal(talla, sexo)
    st.info(f"Peso Ideal: {round(pi, 1)} kg")
    
    st.header("⚙️ Modo y Patología")
    modo_v = st.selectbox("Modo Ventilatorio:", ["AC-Volumen", "AC-Presión", "PSV (Espontáneo)"])
    pat_v = st.selectbox("Situación Clínica:", ["Normal", "SDRA", "Asma", "IAM Derecho"])

# Panel Central: Parámetros del Ventilador
c1, c2, c3, c4 = st.columns(4)
with c1:
    peep = st.slider("PEEP", 0, 25, 5)
    fio2 = st.slider("FiO2 (%)", 21, 100, 40) / 100
with c2:
    if modo_v == "AC-Volumen":
        vt = st.slider("Vol. Corriente (mL)", 200, 800, 420)
        fr = st.slider("Frecuencia (bpm)", 8, 40, 14)
        pres_insp = 0; ps = 0
    elif modo_v == "AC-Presión":
        pres_insp = st.slider("Presión Insp. (cmH2O)", 5, 40, 15)
        fr = st.slider("Frecuencia (bpm)", 8, 40, 14)
        vt = 0; ps = 0
    else: # PSV
        ps = st.slider("Presión Soporte (PS)", 5, 30, 10)
        fr = 12 # Basal
        vt = 0; pres_insp = 0
with c3:
    ie = st.select_slider("Relación I:E", options=["1:1", "1:2", "1:3", "1:4"], value="1:2")

# --- EJECUCIÓN ---
pico, plat, vtr, gc, ph, co2, spo2, ve = simular_ventilacion(modo_v, pat_v, vt, fr, peep, fio2, pres_insp, ps, ie, pi)

# --- MONITOR UCIN ---
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("P. PICO", f"{round(pico)}")
m2.metric("P. MESETA", f"{round(plat)}")
m3.metric("Vt Real", f"{round(vtr)} mL", f"{round(vtr/pi, 1)} mL/kg PI")
m4.metric("Vol. Minuto", f"{ve} L/min")

# --- LABORATORIO DE GASES (RESULTADOS) ---
st.subheader("🩸 Resultados de Gasometría Arterial")
g1, g2, g3, g4 = st.columns(4)
g1.metric("pH", ph)
g2.metric("pCO2", f"{co2} mmHg")
g3.metric("SpO2", f"{spo2}%")
g4.metric("Gasto Cardíaco", f"{gc} L/min")

# --- GRÁFICAS ---
st.subheader("📈 Curvas en Tiempo Real")
t = np.linspace(0, 4, 100)
y = np.piecewise(t, [t < 1, (t >= 1) & (t < 1.4), t >= 1.4], 
                [lambda x: peep + (pico-peep)*x, plat, lambda x: peep + (plat-peep)*np.exp(-4*(x-1.4))])
fig, ax = plt.subplots(figsize=(10, 2))
ax.plot(t, y, color='#00FF41', linewidth=2.5)
ax.set_facecolor('black')
fig.patch.set_facecolor('black')
st.pyplot(fig)
