import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador de INE al 200% (Ajuste de Margen 1 cm)")
st.write("Sube tu archivo. El programa tomará el **Cuadrante 1** de cada página, lo ampliará al **200%** y colocará ambas imágenes juntas subiendo el margen superior $1\\text{ cm}$.")

def combinar_cuadrantes_con_margen_reducido(img_pag1, img_pag2, factor_zoom=2.0):
    """Toma el cuadrante 1 de ambas imágenes, las amplía al 200% y las apila con margen ajustado."""
    # 1. Recortar Cuadrante 1 puro de la Página 1 (Frente)
    ancho1, alto1 = img_pag1.size
    cuadrante_frente = img_pag1.crop((0, 0, ancho1 / 2, alto1 / 2))

    # 2. Recortar Cuadrante 1 puro de la Página 2 (Reverso)
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

    # 5. Ajustar ancho en caso de que exceda los bordes de la página
    if frente_200.width > ANCHO_CARTA:
        escala_f = ANCHO_CARTA / frente_200.width
        frente_200 = frente_200.resize((ANCHO_CARTA, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_CARTA:
        escala_r = ANCHO_CARTA / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_CARTA, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    # 6. Posicionamiento vertical (1 cm a 300 DPI = ~118px)
    MARGEN_SUPERIOR = 118  # 1 cm desde el borde superior
    SEPARACION_INTERMEDIA = 80  # Separación compacta entre las dos imágenes (~0.7 cm)

    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = MARGEN_SUPERIOR

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    pos_y_reverso = pos_y_frente + frente_200.height + SEPARACION_INTERMEDIA

    # Pegar ambas caras en la hoja Carta
    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

uploaded_files = st.file_uploader(
    "Selecciona tu PDF (de 2 páginas) o sube las 2 imágenes de la INE",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    # CASO PDF (2 páginas)
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El archivo PDF debe tener al menos 2 páginas.")
        else:
            pix1 = doc[0].get_pixmap(dpi=300)
            img_pag1 = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc[1].get_pixmap(dpi=300)
            img_pag2 = Image.open(io.BytesIO(pix2.tobytes("png")))

            hoja_final = combinar_cuadrantes_con_margen_reducido(img_pag1, img_pag2, factor_zoom=2.0)

            nuevo_doc = fitz.open()
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)  # Carta en PDF
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Cuadrantes 1 apilados con 1 cm de margen superior", use_column_width=True)
            st.success("¡PDF generado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Unificado",
                data=output_buffer,
                file_name=f"ine_unificada_margen1cm_{pdf_file.name}",
                mime="application/pdf"
            )

    # CASO 2 IMÁGENES SEPARADAS
    elif len(uploaded_files) == 2:
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_cuadrantes_con_margen_reducido(img1, img2, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Cuadrantes 1 apilados con 1 cm de margen superior", use_column_width=True)
        st.success("¡Imagen generada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Unificada",
            data=output_buffer,
            file_name="ine_unificada_margen1cm.png",
            mime="image/png"
        )

    else:
        st.warning("Sube 1 archivo PDF de 2 páginas o 2 archivos de imagen.")
