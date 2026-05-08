import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración UCI Style
st.set_page_config(page_title="Simulador VM Total - VariedadesMx", layout="wide")
st.markdown("<style>.stApp {background-color: black; color: #39FF14;}</style>", unsafe_allow_html=True)

# --- BASE DE DATOS DE PATOLOGÍAS ---
patologias = {
    "SDRA": {"c": 15, "r": 5, "sh": 0.3, "desc": "Baja compliancia parenquimatosa"},
    "Asma": {"c": 50, "r": 45, "sh": 0.05, "desc": "Alta resistencia, riesgo de Auto-PEEP"},
    "Restrictivo (Obesidad)": {"c": 25, "r": 5, "sh": 0.1, "desc": "Restricción extrapulmonar"},
    "IAM Derecho": {"c": 45, "r": 5, "sh": 0.05, "desc": "Falla de precarga, sensible a PEEP"},
    "Falla Cardiaca Izq": {"c": 30, "r": 8, "sh": 0.2, "desc": "Edema cardiogénico, mejora con PEEP"}
}

# --- SIDEBAR: CONTROL DEL VENTILADOR ---
st.sidebar.title("🎮 Panel del Ventilador")
selected_pat = st.sidebar.selectbox("Seleccionar Escenario:", list(patologias.keys()))
vt = st.sidebar.slider("Volumen Corriente (mL)", 200, 800, 450)
fr = st.sidebar.slider("Frecuencia (bpm)", 8, 40, 16)
peep = st.sidebar.slider("PEEP (cmH2O)", 0, 25, 5)
fio2 = st.sidebar.slider("FiO2 (%)", 21, 100, 40) / 100

# --- CÁLCULOS FISIOLÓGICOS ---
p_data = patologias[selected_pat]
c_actual = p_data["c"]
r_actual = p_data["r"]

# Dinámica de presiones
p_plat = (vt / c_actual) + peep
p_pico = p_plat + (r_actual * 0.5)
dp = p_plat - peep # Driving Pressure

# Impacto Hemodinámico (Modelo de Interacción)
gc = 5.2 - (peep * 0.15) - (dp * 0.1) 
if selected_pat == "IAM Derecho": gc -= (peep * 0.3)
pam = 90 - (100 - (gc * 20))

# --- MONITOR PRINCIPAL ---
st.title(f"Paciente Virtual: {selected_pat}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("P. Pico", f"{round(p_pico)}", delta="ALTA" if p_pico > 35 else None, delta_color="inverse")
c2.metric("P. Meseta", f"{round(p_plat)}", delta="VILI" if p_plat > 30 else None, delta_color="inverse")
c3.metric("PAM", f"{round(pam)} mmHg", delta="Hipotensión" if pam < 65 else None, delta_color="inverse")
c4.metric("Driving P.", f"{round(dp)}", delta="Riesgo" if dp > 15 else None, delta_color="inverse")

# --- MANIOBRAS EN TIEMPO REAL ---
st.subheader("🛠 Maniobras Clínicas")
m1, m2, m3 = st.columns(3)
if m1.button("Reclutamiento (40x40)"):
    st.warning("⚠️ Ejecutando... PAM cayendo a 45 mmHg. Observe monitor.")
if m2.button("Pausa Espiratoria"):
    auto_p = (fr * 0.5) if selected_pat == "Asma" else 1.0
    st.write(f"Auto-PEEP detectada: {auto_p} cmH2O")
if m3.button("Gasometría (GSA)"):
    ph = 7.4 - (0.01 * (p_plat-20))
    st.success(f"Reporte: pH {round(ph,2)} | PaCO2 {round(40 + (p_plat/3))} | PaO2 {round(fio2*400)}")

# Gráfica de flujo (Simulada)
t = np.linspace(0, 10, 100)
flow = np.sin(t * fr/5)
fig, ax = plt.subplots(figsize=(12, 2))
ax.plot(t, flow, color="#39FF14")
ax.axhline(0, color="white", linewidth=0.5)
ax.set_facecolor('black')
fig.patch.set_facecolor('black')
st.pyplot(fig)
