import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Ampliador de INE / Documentos al 200%")
st.write("Sube el escáner de tu INE en formato **PDF**, **JPG** o **PNG** para aumentarlo al 200% de su tamaño sin perder calidad.")

# Componente para subir archivo
uploaded_file = st.file_uploader("Selecciona el archivo de la INE", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Procesando archivo al 200%...")

    # OPCIÓN 1: ARCHIVO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for page in doc:
            zoom = 2.0  # 200%
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            rect = page.rect
            nueva_pagina = nuevo_doc.new_page(width=rect.width * zoom, height=rect.height * zoom)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=pix.tobytes("png"))

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success("¡PDF ampliado con éxito!")
        st.download_button(
            label="📥 Descargar PDF al 200%",
            data=output_buffer,
            file_name=f"ampliado_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # OPCIÓN 2: IMAGEN (JPG / PNG)
    else:
        img = Image.open(io.BytesIO(file_bytes))
        nuevo_ancho = img.width * 2
        nuevo_alto = img.height * 2

        # Reescalado con algoritmo LANCZOS para máxima nitidez
        img_resized = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        img_resized.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        # Mostrar vista previa de la imagen reescalada
        st.image(img_resized, caption="Vista previa ampliada al 200%", use_column_width=True)

        st.success("¡Imagen ampliada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen al 200%",
            data=output_buffer,
            file_name=f"ampliado_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
