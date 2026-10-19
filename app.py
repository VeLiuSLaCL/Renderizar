import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Ampliador de Primer Cuadrante al 200%")
st.write("Sube tu documento. El programa tomará la **esquina superior izquierda (Cuadrante 1)** de cada hoja, la ampliará al **200%** y la colocará ocupando la nueva **hoja tamaño Carta**.")

def ampliar_primer_cuadrante(imagen_pil, factor_zoom=2.0):
    """Recorta la esquina superior izquierda (Cuadrante 1) y la amplía al 200% sobre una hoja carta."""
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # 1. Recortar estrictamente el primer cuadrante (mitad superior izquierda)
    cuadrante_1 = img.crop((0, 0, ancho / 2, alto / 2))

    # 2. Multiplicar dimensiones al 200%
    nuevo_ancho = int(cuadrante_1.width * factor_zoom)
    nuevo_alto = int(cuadrante_1.height * factor_zoom)

    # Escalado LANCZOS para mantener la máxima nitidez en letras y fotos
    cuadrante_ampliado = cuadrante_1.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    # 3. Crear el lienzo en blanco para Hoja Carta (2550 x 3300 px a 300 DPI)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # Ajustar si el ancho ampliado excede ligeramente los márgenes de la carta
    if cuadrante_ampliado.width > ANCHO_CARTA:
        escala = ANCHO_CARTA / cuadrante_ampliado.width
        cuadrante_ampliado = cuadrante_ampliado.resize(
            (ANCHO_CARTA, int(cuadrante_ampliado.height * escala)), 
            Image.Resampling.LANCZOS
        )

    # 4. Pegar el cuadrante ampliado en la parte superior de la nueva hoja carta
    pos_x = (ANCHO_CARTA - cuadrante_ampliado.width) // 2
    hoja_carta.paste(cuadrante_ampliado, (pos_x, 0))

    return hoja_carta

uploaded_file = st.file_uploader("Selecciona tu archivo PDF o Imagen", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Procesando el primer cuadrante de cada página al 200%...")

    # CASO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for num_pag, page in enumerate(doc, start=1):
            # Renderizar la página a 300 DPI para alta definición
            pix = page.get_pixmap(dpi=300)
            img_original = Image.open(io.BytesIO(pix.tobytes("png")))

            # Ampliar cuadrante 1
            hoja_final = ampliar_primer_cuadrante(img_original, factor_zoom=2.0)

            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Insertar en nueva página Carta (612 x 792 pt)
            nueva_pagina = nuevo_doc.new_page(width=612, height=792)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success(f"¡Procesadas {len(doc)} página(s) con éxito!")
        st.download_button(
            label="📥 Descargar PDF Ampliado al 200%",
            data=output_buffer,
            file_name=f"ine_cuadrante1_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # CASO IMAGEN
    else:
        img_original = Image.open(io.BytesIO(file_bytes))
        hoja_final = ampliar_primer_cuadrante(img_original, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        hoja_final.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Primer cuadrante ampliado al 200% en Hoja Carta", use_column_width=True)

        st.success("¡Imagen ampliada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Ampliada al 200%",
            data=output_buffer,
            file_name=f"ine_cuadrante1_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
