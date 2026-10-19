import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador de INE al 200% (1 Sola Hoja Carta)")
st.write("Sube tu archivo PDF o imágenes. El programa tomará el **primer cuadrante de la Página 1** y el **primer cuadrante de la Página 2**, los ampliará al **200%** y los colocará juntos en **una sola hoja Carta**.")

def combinar_cuadrantes_en_una_hoja(img_pag1, img_pag2, factor_zoom=2.0):
    """Extrae el cuadrante 1 de dos imágenes, los amplía al 200% y los une en una sola hoja carta."""
    # 1. Recortar Cuadrante 1 de la Página 1 (Frente)
    ancho1, alto1 = img_pag1.size
    cuadrante_frente = img_pag1.crop((0, 0, ancho1 / 2, alto1 / 2))

    # 2. Recortar Cuadrante 1 de la Página 2 (Reverso)
    ancho2, alto2 = img_pag2.size
    cuadrante_reverso = img_pag2.crop((0, 0, ancho2 / 2, alto2 / 2))

    # 3. Ampliar ambos cuadrantes al 200%
    frente_200 = cuadrante_frente.resize(
        (int(cuadrante_frente.width * factor_zoom), int(cuadrante_frente.height * factor_zoom)),
        Image.Resampling.LANCZOS
    )
    reverso_200 = cuadrante_reverso.resize(
        (int(cuadrante_reverso.width * factor_zoom), int(cuadrante_reverso.height * factor_zoom)),
        Image.Resampling.LANCZOS
    )

    # 4. Crear lienzo en blanco para Hoja Carta (2550 x 3300 px a 300 DPI)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # 5. Ajustar ancho si sobrepasa los bordes de la hoja
    if frente_200.width > ANCHO_CARTA:
        escala_f = ANCHO_CARTA / frente_200.width
        frente_200 = frente_200.resize((ANCHO_CARTA, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_CARTA:
        escala_r = ANCHO_CARTA / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_CARTA, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    # 6. Acomodar Frente en la mitad superior y Reverso en la mitad inferior
    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 150  # Margen superior

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    pos_y_reverso = (ALTO_CARTA // 2) + 100  # Inicio en la segunda mitad de la hoja

    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

# Opción para cargar PDF o múltiples imágenes
uploaded_files = st.file_uploader(
    "Selecciona tu PDF (de 2 páginas) o sube las 2 imágenes de la INE (Frente y Reverso)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    # CASO PDF UNICAMENTE
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El archivo PDF tiene solo 1 página. Se requiere un PDF de al menos 2 páginas (Página 1: Frente, Página 2: Reverso).")
        else:
            st.info("Procesando Cuadrante 1 de las Páginas 1 y 2...")

            # Renderizar Página 1 y Página 2 a 300 DPI
            pix1 = doc[0].get_pixmap(dpi=300)
            img_pag1 = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc[1].get_pixmap(dpi=300)
            img_pag2 = Image.open(io.BytesIO(pix2.tobytes("png")))

            hoja_final = combinar_cuadrantes_en_una_hoja(img_pag1, img_pag2, factor_zoom=2.0)

            # Generar PDF de 1 sola página
            nuevo_doc = fitz.open()
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)  # Carta estándar en PDF
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Ambas caras ampliadas al 200% en 1 sola hoja Carta", use_column_width=True)
            st.success("¡Documento unificado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Unificado en 1 Hoja",
                data=output_buffer,
                file_name=f"ine_unificada_200_{pdf_file.name}",
                mime="application/pdf"
            )

    # CASO 2 IMÁGENES SEPARADAS (JPG / PNG)
    elif len(uploaded_files) == 2:
        st.info("Procesando las 2 imágenes subidas...")
        
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_cuadrantes_en_una_hoja(img1, img2, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Ambas caras ampliadas al 200% en 1 sola hoja Carta", use_column_width=True)
        st.success("¡Imagen unificada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Unificada en 1 Hoja",
            data=output_buffer,
            file_name="ine_unificada_200.png",
            mime="image/png"
        )

    else:
        st.warning("Por favor sube **1 archivo PDF de 2 páginas** o bien **2 archivos de imagen** (Página 1 y Página 2).")
