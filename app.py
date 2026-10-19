import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image, ImageChops

# Configuración de la página
st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Recorte y Ampliación de INE al 200%")
st.write("Sube el escáner de tu INE. El sistema detectará la credencial, eliminará los márgenes vacíos de la hoja y amplió el contenido al 200%.")

def recortar_y_ampliar(imagen_pil, factor_zoom=2.0):
    """Detecta el contenido útil de la imagen, elimina bordes vacíos y la amplía."""
    # Convertir a RGB por si viene en escala de grises o RGBA
    img = imagen_pil.convert("RGB")

    # Detectar fondo blanco o transparente para recortar los márgenes sobrantes
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()

    # Si se detecta el contenido de la INE dentro de la hoja, se recorta
    if bbox:
        img_recortada = img.crop(bbox)
    else:
        img_recortada = img  # Si no detecta bordes, usa la imagen completa

    # Calcular el nuevo tamaño al 200% solo del contenido de la INE
    nuevo_ancho = int(img_recortada.width * factor_zoom)
    nuevo_alto = int(img_recortada.height * factor_zoom)

    # Reescalar con algoritmo LANCZOS para máxima calidad y nitidez
    return img_recortada.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

# Componente para subir archivo
uploaded_file = st.file_uploader("Selecciona el archivo de la INE", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Detectando contenido y ampliando la INE al 200%...")

    # OPCIÓN 1: ARCHIVO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for page in doc:
            # Convertir la página del PDF a imagen en alta resolución (300 DPI)
            pix = page.get_pixmap(dpi=300)
            img_original = Image.open(io.BytesIO(pix.tobytes("png")))

            # Recortar márgenes y ampliar INE
            img_ampliada = recortar_y_ampliar(img_original, factor_zoom=2.0)

            # Guardar la imagen en una nueva página del PDF con el tamaño exacto ampliado
            img_bytes = io.BytesIO()
            img_ampliada.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Crear página con las dimensiones exactas de la INE ampliada
            nueva_pagina = nuevo_doc.new_page(width=img_ampliada.width * 0.72, height=img_ampliada.height * 0.72)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success("¡INE recortada y ampliada al 200%!")
        st.download_button(
            label="📥 Descargar PDF Ampliado al 200%",
            data=output_buffer,
            file_name=f"ine_ampliada_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # OPCIÓN 2: IMAGEN (JPG / PNG)
    else:
        img_original = Image.open(io.BytesIO(file_bytes))
        img_ampliada = recortar_y_ampliar(img_original, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        img_ampliada.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        # Mostrar vista previa de la INE recortada y ampliada
        st.image(img_ampliada, caption="Vista previa: INE enfocada y ampliada al 200%", use_column_width=True)

        st.success("¡Imagen recortada y ampliada al 200%!")
        st.download_button(
            label="📥 Descargar Imagen Ampliada al 200%",
            data=output_buffer,
            file_name=f"ine_ampliada_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
