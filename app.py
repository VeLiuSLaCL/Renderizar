import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Ampliador INE al 200% en Hoja Carta")
st.write("Sube tu archivo. Se tomará la INE del cuadrante superior izquierdo, se ampliará al 200% y se colocará sobre una **hoja en blanco tamaño Carta**.")

def colocar_en_hoja_carta(imagen_pil, factor_zoom=2.0):
    """Extrae el cuadrante 1, lo amplía al 200% y lo coloca centrado en una hoja carta."""
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # 1. Recortar el Cuadrante 1 (esquina superior izquierda)
    box_cuadrante_1 = (0, 0, ancho / 2, alto / 2)
    ine_recortada = img.crop(box_cuadrante_1)

    # 2. Duplicar el tamaño de la INE recortada (200%)
    nuevo_ancho_ine = int(ine_recortada.width * factor_zoom)
    nuevo_alto_ine = int(ine_recortada.height * factor_zoom)
    ine_ampliada = ine_recortada.resize((nuevo_ancho_ine, nuevo_alto_ine), Image.Resampling.LANCZOS)

    # 3. Crear lienzo en blanco con tamaño Hoja Carta estándar a 300 DPI (2550 x 3300 px)
    ANCHO_CARTA = 2550
    ALTO_CARTA = 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # 4. Posicionar la INE ampliada en la parte superior/centrada de la hoja carta
    pos_x = (ANCHO_CARTA - nuevo_ancho_ine) // 2
    pos_y = 150  # Margen superior pequeño

    # Si la INE ampliada supera el ancho de la hoja, ajustarla para que entre perfectamente
    if nuevo_ancho_ine > ANCHO_CARTA:
        falla_escala = ANCHO_CARTA / nuevo_ancho_ine
        ine_ampliada = ine_ampliada.resize((ANCHO_CARTA - 100, int(nuevo_alto_ine * falla_escala)), Image.Resampling.LANCZOS)
        pos_x = 50

    # Pegar la INE ampliada dentro del lienzo tamaño carta
    hoja_carta.paste(ine_ampliada, (pos_x, pos_y))

    return hoja_carta

# Componente para subir archivo
uploaded_file = st.file_uploader("Selecciona el archivo de la INE", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Procesando INE en hoja tamaño Carta...")

    # OPCIÓN 1: ARCHIVO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for page in doc:
            # Renderizar a 300 DPI para máxima calidad de impresión
            pix = page.get_pixmap(dpi=300)
            img_original = Image.open(io.BytesIO(pix.tobytes("png")))

            # Procesar la imagen en tamaño carta
            hoja_final = colocar_en_hoja_carta(img_original, factor_zoom=2.0)

            # Convertir imagen procesada a bytes
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Crear página del PDF exactamente en tamaño Carta estándar (612 x 792 pt)
            nueva_pagina = nuevo_doc.new_page(width=612, height=792)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success("¡PDF generado con éxito en tamaño Carta!")
        st.download_button(
            label="📥 Descargar PDF Tamaño Carta al 200%",
            data=output_buffer,
            file_name=f"ine_carta_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # OPCIÓN 2: IMAGEN (JPG / PNG)
    else:
        img_original = Image.open(io.BytesIO(file_bytes))
        hoja_final = colocar_en_hoja_carta(img_original, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        hoja_final.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Hoja Carta con INE ampliada al 200%", use_column_width=True)

        st.success("¡Imagen generada con éxito en tamaño Carta!")
        st.download_button(
            label="📥 Descargar Imagen Tamaño Carta al 200%",
            data=output_buffer,
            file_name=f"ine_carta_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
