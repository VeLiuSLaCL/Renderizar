import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador de INE al 200% (1 Sola Hoja Carta)")
st.write("Sube tu archivo PDF de 2 páginas o 2 imágenes. El programa tomará el **Cuadrante 1 del Frente** (menos 0.5 cm superior) y el **Cuadrante 1 del Reverso** (menos 1 cm superior), los ampliará al **200%** y colocará el Reverso en la mitad inferior de la hoja.")

def recortar_cuadrante_y_ampliar(imagen_pil, es_pagina_1=True, factor_zoom=2.0):
    """Extrae el primer cuadrante ajustando el margen superior y lo amplía al 200%."""
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # A 300 DPI: 0.5 cm = ~59 px, 1 cm = ~118 px
    margen_px = 59 if es_pagina_1 else 118
    y_inicio = min(margen_px, int(alto / 2) - 10)

    # Recortar Cuadrante 1 (mitad izquierda, mitad superior omitiendo el margen alto)
    cuadrante = img.crop((0, y_inicio, ancho / 2, alto / 2))

    # Multiplicar dimensiones al 200%
    nuevo_ancho = int(cuadrante.width * factor_zoom)
    nuevo_alto = int(cuadrante.height * factor_zoom)

    return cuadrante.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

def combinar_en_una_hoja_carta(img_frente, img_reverso):
    """Junta las dos imágenes ampliadas en un solo lienzo tamaño Carta."""
    frente_200 = recortar_cuadrante_y_ampliar(img_frente, es_pagina_1=True, factor_zoom=2.0)
    reverso_200 = recortar_cuadrante_y_ampliar(img_reverso, es_pagina_1=False, factor_zoom=2.0)

    # Lienzo Hoja Carta en Blanco (2550 x 3300 px a 300 DPI)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # Ajuste de escala para asegurar que ambas imágenes entren en la hoja de forma proporcional
    ANCHO_MAXIMO = ANCHO_CARTA - 100  # Dejar márgenes laterales de 50px

    if frente_200.width > ANCHO_MAXIMO:
        escala_f = ANCHO_MAXIMO / frente_200.width
        frente_200 = frente_200.resize((ANCHO_MAXIMO, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_MAXIMO:
        escala_r = ANCHO_MAXIMO / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_MAXIMO, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    # POSICIONAMIENTO EN LA HOJA CARTA:
    # 1. Frente en la mitad superior
    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 60  # Pegado arriba

    # 2. Reverso en la mitad inferior (calculado exactamente después del término de la primera imagen)
    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    pos_y_reverso = pos_y_frente + frente_200.height + 60  # Ubicado inmediatamente abajo

    # Pegar ambas imágenes sobre el mismo lienzo
    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

uploaded_files = st.file_uploader(
    "Selecciona tu PDF (de 2 páginas) o sube las 2 imágenes (Página 1 y Página 2)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    # CASO PDF (Procesa la Página 1 y la Página 2 del documento)
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El archivo PDF debe tener al menos 2 páginas para extraer ambos lados.")
        else:
            # Extraer Página 1 y Página 2 a 300 DPI
            pix1 = doc[0].get_pixmap(dpi=300)
            img_pag1 = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc[1].get_pixmap(dpi=300)
            img_pag2 = Image.open(io.BytesIO(pix2.tobytes("png")))

            # Unir ambas imágenes en la misma hoja Carta
            hoja_final = combinar_en_una_hoja_carta(img_pag1, img_pag2)

            # Guardar en PDF de 1 SOLA PÁGINA
            nuevo_doc = fitz.open()
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)  # Dimensiones Carta en PDF
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Frente arriba y Reverso abajo en 1 sola Hoja Carta", use_column_width=True)
            st.success("¡Documento unificado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Unificado en 1 Hoja",
                data=output_buffer,
                file_name=f"ine_unificada_200_{pdf_file.name}",
                mime="application/pdf"
            )

    # CASO 2 IMÁGENES SEPARADAS
    elif len(uploaded_files) == 2:
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_en_una_hoja_carta(img1, img2)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Frente arriba y Reverso abajo en 1 sola Hoja Carta", use_column_width=True)
        st.success("¡Imagen unificada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Unificada en 1 Hoja",
            data=output_buffer,
            file_name="ine_unificada_200.png",
            mime="image/png"
        )

    else:
        st.warning("Por favor sube **1 archivo PDF de 2 páginas** o **2 archivos de imagen**.")
