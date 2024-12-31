import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Configuración de la página
st.set_page_config(page_title="Sistema de Agenda de Citas", layout="wide")

# Inicialización del estado de la aplicación
if 'citas' not in st.session_state:
    st.session_state.citas = []

# Función para cargar citas desde archivo
def cargar_citas():
    try:
        if os.path.exists('citas.json'):
            with open('citas.json', 'r') as file:
                return json.load(file)
    except Exception as e:
        st.error(f"Error al cargar citas: {e}")
    return []

# Función para guardar citas en archivo
def guardar_citas(citas):
    try:
        with open('citas.json', 'w') as file:
            json.dump(citas, file)
    except Exception as e:
        st.error(f"Error al guardar citas: {e}")

# Función para validar disponibilidad
def verificar_disponibilidad(fecha, hora):
    for cita in st.session_state.citas:
        if cita['fecha'] == fecha and cita['hora'] == hora:
            return False
    return True

# Título principal
st.title("📅 Sistema de Agenda de Citas")

# Sidebar para agregar citas
with st.sidebar:
    st.header("Agendar Nueva Cita")
    
    # Formulario de nueva cita
    with st.form("nueva_cita"):
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico")
        telefono = st.text_input("Teléfono")
        
        # Selector de fecha (desde hoy hasta 30 días después)
        fecha_min = datetime.now().date()
        fecha_max = fecha_min + timedelta(days=30)
        fecha = st.date_input("Fecha", min_value=fecha_min, max_value=fecha_max)
        
        # Selector de hora (horario laboral)
        horas_disponibles = [f"{h:02d}:00" for h in range(9, 18)]
        hora = st.selectbox("Hora", horas_disponibles)
        
        # Descripción de la cita
        descripcion = st.text_area("Descripción de la cita")
        
        submitted = st.form_submit_button("Agendar Cita")
        
        if submitted:
            if not nombre or not email or not telefono:
                st.error("Por favor complete todos los campos obligatorios.")
            elif not verificar_disponibilidad(str(fecha), hora):
                st.error("Este horario ya está ocupado. Por favor seleccione otro.")
            else:
                nueva_cita = {
                    "nombre": nombre,
                    "email": email,
                    "telefono": telefono,
                    "fecha": str(fecha),
                    "hora": hora,
                    "descripcion": descripcion
                }
                st.session_state.citas.append(nueva_cita)
                guardar_citas(st.session_state.citas)
                st.success("¡Cita agendada con éxito!")

# Área principal: Visualización de citas
st.header("Citas Programadas")

# Cargar citas existentes
if not st.session_state.citas:
    st.session_state.citas = cargar_citas()

# Convertir citas a DataFrame para mejor visualización
if st.session_state.citas:
    df_citas = pd.DataFrame(st.session_state.citas)
    df_citas['fecha'] = pd.to_datetime(df_citas['fecha']).dt.date
    df_citas = df_citas.sort_values(['fecha', 'hora'])
    
    # Mostrar citas en una tabla
    st.dataframe(
        df_citas,
        column_config={
            "nombre": "Nombre",
            "email": "Correo",
            "telefono": "Teléfono",
            "fecha": "Fecha",
            "hora": "Hora",
            "descripcion": "Descripción"
        },
        hide_index=True
    )
else:
    st.info("No hay citas programadas.")

# Funcionalidad para eliminar citas
if st.session_state.citas:
    st.header("Eliminar Cita")
    citas_para_eliminar = [f"{cita['fecha']} {cita['hora']} - {cita['nombre']}" 
                          for cita in st.session_state.citas]
    
    cita_a_eliminar = st.selectbox("Seleccione la cita a eliminar:", citas_para_eliminar)
    
    if st.button("Eliminar Cita"):
        indice = citas_para_eliminar.index(cita_a_eliminar)
        st.session_state.citas.pop(indice)
        guardar_citas(st.session_state.citas)
        st.success("Cita eliminada con éxito")
        st.rerun()