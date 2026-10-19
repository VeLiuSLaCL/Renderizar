import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Ampliador INE al 200% (Cuadrante Superior Izquierdo)")
st.write("Sube el escáner de tu INE. El sistema tomará automáticamente la esquina superior izquierda (Cuadrante 1), eliminará el resto de la hoja y la ampliará al 200%.")

def procesar_cuadrante_1(imagen_pil, factor_zoom=2.0):
    """Divide la imagen en 4 cuadrantes, toma el superior izquierdo y lo amplía al 200%."""
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # 1. Definir los límites del Cuadrante 1 (mitad superior, mitad izquierda)
    mitad_ancho = ancho / 2
    mitad_alto = alto / 2

    # Coordenadas de recorte: (izquierda, arriba, derecha, abajo)
    box_cuadrante_1 = (0, 0, mitad_ancho, mitad_alto)
    cuadrante_1 = img.crop(box_cuadrante_1)

    # 2. Duplicar el tamaño del cuadrante recortado (200%)
    nuevo_ancho = int(cuadrante_1.width * factor_zoom)
    nuevo_alto = int(cuadrante_1.height * factor_zoom)

    # Reescalado con algoritmo LANCZOS para máxima calidad y nitidez
    return cuadrante_1.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

# Componente para subir archivo
uploaded_file = st.file_uploader("Selecciona el archivo de la INE", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Extrayendo Cuadrante 1 y ampliando al 200%...")

    # OPCIÓN 1: ARCHIVO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for page in doc:
            # Convertir página a imagen a 300 DPI para mantener alta nitidez
            pix = page.get_pixmap(dpi=300)
            img_original = Image.open(io.BytesIO(pix.tobytes("png")))

            # Extraer cuadrante 1 y ampliar
            img_ampliada = procesar_cuadrante_1(img_original, factor_zoom=2.0)

            # Convertir imagen procesada a bytes
            img_bytes = io.BytesIO()
            img_ampliada.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Insertar en nueva página en el PDF
            nueva_pagina = nuevo_doc.new_page(width=img_ampliada.width * 0.72, height=img_ampliada.height * 0.72)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success("¡PDF procesado con éxito!")
        st.download_button(
            label="📥 Descargar PDF (Cuadrante 1 al 200%)",
            data=output_buffer,
            file_name=f"ine_cuadrante1_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # OPCIÓN 2: IMAGEN (JPG / PNG)
    else:
        img_original = Image.open(io.BytesIO(file_bytes))
        img_ampliada = procesar_cuadrante_1(img_original, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        img_ampliada.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        # Mostrar la vista previa de la INE resultante
        st.image(img_ampliada, caption="Vista previa: Cuadrante 1 ampliado al 200%", use_column_width=True)

        st.success("¡Imagen procesada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen (Cuadrante 1 al 200%)",
            data=output_buffer,
            file_name=f"ine_cuadrante1_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
