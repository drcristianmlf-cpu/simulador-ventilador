import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="VariedadesMx - Simulador Pro 2026", layout="wide")

# Estilo visual de monitor médico
st.markdown("""
    <style>
    .stApp { background-color: #0d0d0d; color: #39FF14; }
    .stMetric { background-color: #1a1a1a; padding: 10px; border-radius: 5px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE FISIOPATOLOGÍA DINÁMICA ---
def generar_curvas(pat, vt, fr, peep, fio2, maniobra_reclutamiento=False):
    # Parámetros base según patología
    params = {
        "Normal": {"c": 50, "r": 5, "base_gc": 5.0, "pvc": 5},
        "SDRA (Falla Restrictiva)": {"c": 15, "r": 8, "base_gc": 4.5, "pvc": 10},
        "Asma/EPOC (Obstructiva)": {"c": 55, "r": 40, "base_gc": 4.8, "pvc": 8},
        "IAM Derecho (Falla VD)": {"c": 45, "r": 5, "base_gc": 3.5, "pvc": 18},
        "Edema Pulmonar (ICA)": {"c": 25, "r": 12, "base_gc": 3.8, "pvc": 12}
    }
    
    p = params[pat]
    c, r = p["c"], p["r"]
    
    # Efecto de la maniobra de reclutamiento
    if maniobra_reclutamiento:
        c = c * 1.2 # Mejora temporal de compliancia
    
    # Cálculos de presiones
    p_plat = (vt / c) + peep
    p_pico = p_plat + (r * (vt/1000) * 2) # Basado en flujo
    p_mean = (p_plat + peep) / 2
    
    # Interacción Hemodinámica Real
    # En IAM Derecho, el Gasto Cardíaco cae drásticamente con la PEEP
    if pat == "IAM Derecho (Falla VD)":
        gc = p["base_gc"] - (peep * 0.25) - (p_mean * 0.1)
    else:
        gc = p["base_gc"] - (peep * 0.05) 
    
    pam = 60 + (gc * 6)
    pvc = p["pvc"] + (peep * 0.4)
    
    # Gasometría y Oximetría
    spo2 = min(100, 80 + (fio2 * 15) + (peep * 0.5) - (10 if pat=="SDRA (Falla Restrictiva)" else 0))
    paco2 = 40 + (p_plat / 4) if pat != "Normal" else 40
    
    return p_pico, p_plat, gc, pam, pvc, spo2, paco2, c, r

# --- INTERFAZ ---
st.title("📟 Simulador de Ventilación Mecánica Avanzada (VariedadesMx)")

with st.sidebar:
    st.header("🏥 Perfil del Paciente")
    escenario = st.selectbox("Patología:", ["Normal", "SDRA (Falla Restrictiva)", "Asma/EPOC (Obstructiva)", "IAM Derecho (Falla VD)", "Edema Pulmonar (ICA)"])
    
    st.header("🎛 Panel de Control")
    v_t = st.slider("Volumen Corriente (mL)", 200, 800, 450)
    f_r = st.slider("Frecuencia (bpm)", 8, 40, 16)
    peep_val = st.slider("PEEP (cmH2O)", 0, 25, 5)
    fi_o2 = st.slider("FiO2 (%)", 21, 100, 40) / 100
    
    st.header("🛠 Maniobras")
    reclut = st.checkbox("Maniobra de Reclutamiento")
    fuga = st.checkbox("Test de Fuga de Cuff")

# Ejecutar motor
pico, plat, gc, pam, pvc, spo2, co2, comp, res = generar_curvas(escenario, v_t, f_r, peep_val, fi_o2, reclut)

# --- MONITOR DE PARÁMETROS (TIEMPO REAL) ---
st.subheader("📊 Monitor Multiparamétrico")
c1, c2, c3, c4 = st.columns(4)
c1.metric("P. PICO", f"{round(pico)} cmH2O", delta="¡ALTA!" if pico > 35 else None, delta_color="inverse")
c2.metric("P. MESETA", f"{round(plat)} cmH2O", delta="RIESGO" if plat > 30 else None, delta_color="inverse")
c3.metric("PAM", f"{round(pam)} mmHg", delta="Choque" if pam < 65 else None, delta_color="inverse")
c4.metric("SpO2", f"{round(spo2)}%", delta="Hipoxia" if spo2 < 90 else None, delta_color="inverse")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Gasto Cardíaco", f"{round(gc, 2)} L/min")
c6.metric("PVC", f"{round(pvc)} mmHg")
c7.metric("Compliancia", f"{round(comp)} mL/cmH2O")
c8.metric("EtCO2", f"{round(co2)} mmHg")

# --- GRÁFICAS DINÁMICAS ---
st.subheader("📈 Curvas de Ventilación")
t = np.linspace(0, 4, 200)
# Simular onda de presión real con rampa y meseta
y = np.piecewise(t, [t < 1, (t >= 1) & (t < 1.3), t >= 1.3], 
                [lambda x: peep_val + (pico-peep_val)*x, plat, lambda x: peep_val + (plat-peep_val)*np.exp(-5*(x-1.3))])

fig, ax = plt.subplots(figsize=(12, 3))
ax.plot(t, y, color='#39FF14', linewidth=3)
ax.set_facecolor('black')
fig.patch.set_facecolor('black')
ax.set_ylabel("Presión")
ax.grid(color='#333', linestyle='--')
st.pyplot(fig)

# --- REPORTE SISTÉMICO ---
st.subheader("🩺 Evaluación Extrapulmonar")
with st.expander("Ver detalle de Perfusión Orgánica"):
    col_a, col_b = st.columns(2)
    col_a.write(f"🧠 **Perfusión Cerebral:** {'Comprometida' if (pam - co2/2) < 50 else 'Estable'}")
    col_a.write(f"💧 **Perfusión Renal:** {'Riesgo de falla prerenal' if gc < 3.0 else 'Flujo adecuado'}")
    col_b.write(f"❤️ **Carga del VD:** {'Sobrecarga crítica' if pvc > 15 else 'Normal'}")
    col_b.write(f"📋 **Índice Tobin (RSBI):** {round(f_r / (v_t/1000), 1)}")

if fuga:
    st.warning("⚠️ Test de Fuga: Volumen exhalado 150mL menor al inspirado. Riesgo de edema laríngeo bajo.")
