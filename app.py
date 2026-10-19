import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image, ImageChops

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador de INE al 200% (Ajuste de Margen Inferior)")
st.write("Sube tu archivo. Se tomará el Cuadrante 1 de cada página, recortando el margen superior sobrante para subir la segunda imagen y balancear la hoja Carta.")

def recortar_margen_blanco_superior(crop_img):
    """Elimina el espacio blanco vacío arriba de la credencial si lo tiene."""
    bg = Image.new(crop_img.mode, crop_img.size, (255, 255, 255))
    diff = ImageChops.difference(crop_img, bg)
    bbox = diff.getbbox()
    if bbox:
        # Mantener ancho completo pero recortar desde donde empieza el contenido real
        return crop_img.crop((0, bbox[1], crop_img.width, crop_img.height))
    return crop_img

def combinar_cuadrantes_en_una_hoja(img_pag1, img_pag2, factor_zoom=2.0):
    """Extrae el cuadrante 1 de dos imágenes, ajusta márgenes, amplía al 200% y los une."""
    # 1. Recortar Cuadrante 1 de la Página 1 (Frente)
    ancho1, alto1 = img_pag1.size
    cuadrante_frente = img_pag1.crop((0, 0, ancho1 / 2, alto1 / 2))

    # 2. Recortar Cuadrante 1 de la Página 2 (Reverso) y eliminar su margen blanco superior
    ancho2, alto2 = img_pag2.size
    cuadrante_reverso_raw = img_pag2.crop((0, 0, ancho2 / 2, alto2 / 2))
    cuadrante_reverso = recortar_margen_blanco_superior(cuadrante_reverso_raw)

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

    # 6. Nuevas posiciones verticales balanceadas
    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 80  # Subimos el frente hacia arriba (antes era 150)

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    # El reverso se coloca inmediatamente debajo del frente con una separación constante
    pos_y_reverso = pos_y_frente + frente_200.height + 60 

    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

uploaded_files = st.file_uploader(
    "Selecciona tu PDF (de 2 páginas) o sube las 2 imágenes de la INE",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El archivo PDF debe tener 2 páginas.")
        else:
            pix1 = doc[0].get_pixmap(dpi=300)
            img_pag1 = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc[1].get_pixmap(dpi=300)
            img_pag2 = Image.open(io.BytesIO(pix2.tobytes("png")))

            hoja_final = combinar_cuadrantes_en_una_hoja(img_pag1, img_pag2, factor_zoom=2.0)

            nuevo_doc = fitz.open()
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Imagen del reverso elevada con margen balanceado", use_column_width=True)
            st.success("¡PDF procesado con margen ajustado!")
            st.download_button(
                label="📥 Descargar PDF Ajustado",
                data=output_buffer,
                file_name=f"ine_ajustada_200_{pdf_file.name}",
                mime="application/pdf"
            )

    elif len(uploaded_files) == 2:
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_cuadrantes_en_una_hoja(img1, img2, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Imagen del reverso elevada con margen balanceado", use_column_width=True)
        st.success("¡Imagen ajustada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Ajustada",
            data=output_buffer,
            file_name="ine_ajustada_200.png",
            mime="image/png"
        )
