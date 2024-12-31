import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# Configuración de la página
st.set_page_config(page_title="Sistema de Agenda de Citas", layout="wide")

# Configuración de credenciales de Google Sheets
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1J2h1Gjw_N6x_i_8LXSWYrvuvZYR75qJFVec_S0DWa4U'
SHEET_NAME = 'Hoja 1'

# Función para conectar con Google Sheets
@st.cache_resource
def get_google_sheets_service():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service

# Función para leer citas desde Google Sheets
def leer_citas():
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:F'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return []
            
        citas = []
        for row in values:
            if len(row) == 6:  # Asegurarse de que la fila tiene todos los campos
                cita = {
                    "nombre": row[0],
                    "email": row[1],
                    "telefono": row[2],
                    "fecha": row[3],
                    "hora": row[4],
                    "descripcion": row[5]
                }
                citas.append(cita)
        return citas
    except Exception as e:
        st.error(f"Error al leer citas: {e}")
        return []

# Función para guardar cita en Google Sheets
def guardar_cita(cita):
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        values = [[
            cita['nombre'],
            cita['email'],
            cita['telefono'],
            cita['fecha'],
            cita['hora'],
            cita['descripcion']
        ]]
        
        body = {
            'values': values
        }
        
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:F',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error al guardar cita: {e}")
        return False

# Función para eliminar cita de Google Sheets
def eliminar_cita(indice):
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # Obtener todas las citas
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:F'
        ).execute()
        
        values = result.get('values', [])
        if indice < len(values):
            # Eliminar la fila específica
            request = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,  # ID de la hoja (generalmente 0 para la primera hoja)
                                "dimension": "ROWS",
                                "startIndex": indice + 1,  # +1 porque la primera fila es el encabezado
                                "endIndex": indice + 2
                            }
                        }
                    }
                ]
            }
            
            sheet.batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=request
            ).execute()
            
            return True
    except Exception as e:
        st.error(f"Error al eliminar cita: {e}")
        return False

# Función para verificar disponibilidad
def verificar_disponibilidad(fecha, hora):
    citas = leer_citas()
    for cita in citas:
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
        
        # Selector de fecha
        fecha_min = datetime.now().date()
        fecha_max = fecha_min + timedelta(days=30)
        fecha = st.date_input("Fecha", min_value=fecha_min, max_value=fecha_max)
        
        # Selector de hora
        horas_disponibles = [f"{h:02d}:00" for h in range(9, 18)]
        hora = st.selectbox("Hora", horas_disponibles)
        
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
                if guardar_cita(nueva_cita):
                    st.success("¡Cita agendada con éxito!")
                    st.rerun()

# Área principal: Visualización de citas
st.header("Citas Programadas")

# Cargar y mostrar citas existentes
citas = leer_citas()
if citas:
    df_citas = pd.DataFrame(citas)
    df_citas['fecha'] = pd.to_datetime(df_citas['fecha']).dt.date
    df_citas = df_citas.sort_values(['fecha', 'hora'])
    
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
if citas:
    st.header("Eliminar Cita")
    citas_para_eliminar = [f"{cita['fecha']} {cita['hora']} - {cita['nombre']}" 
                          for cita in citas]
    
    cita_a_eliminar = st.selectbox("Seleccione la cita a eliminar:", citas_para_eliminar)
    
    if st.button("Eliminar Cita"):
        indice = citas_para_eliminar.index(cita_a_eliminar)
        if eliminar_cita(indice):
            st.success("Cita eliminada con éxito")
            st.rerun()
