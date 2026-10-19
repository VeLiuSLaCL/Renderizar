import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador INE 200% (Ajuste Reverso Completo)")
st.write("El programa ajusta el recorte del Reverso para capturar todo el texto inferior y apilar ambas imágenes perfectamente en una hoja Carta.")

def recortar_y_ampliar_credencial(imagen_pil, es_pagina_1=True, factor_zoom=2.0):
    """
    Recorta el Cuadrante 1 capturando la altura exacta de cada cara
    para asegurar que el reverso salga 100% completo.
    """
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # Márgenes superiores (0.5 cm en pág 1, 1.0 cm en pág 2)
    margen_sup_px = 59 if es_pagina_1 else 118

    # Ancho: Mitad de la hoja (Cuadrante 1)
    ancho_cuadrante = ancho / 2

    # Alto diferenciado: 30% para el frente, 42% para el reverso (captura el texto inferior completo)
    porcentaje_alto = 0.30 if es_pagina_1 else 0.42
    alto_cuadrante = int(alto * porcentaje_alto)

    y_inicio = min(margen_sup_px, int(alto / 2) - 10)
    y_fin = min(y_inicio + alto_cuadrante, alto)

    # Recorte ajustado: (x1, y1, x2, y2)
    cuadrante = img.crop((0, y_inicio, ancho_cuadrante, y_fin))

    # Ampliar al 200%
    nuevo_ancho = int(cuadrante.width * factor_zoom)
    nuevo_alto = int(cuadrante.height * factor_zoom)

    return cuadrante.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

def combinar_frente_y_reverso(img_frente, img_reverso):
    """Une el Frente (al fondo) y el Reverso (al frente) subiendo ligeramente la segunda imagen."""
    frente_200 = recortar_y_ampliar_credencial(img_frente, es_pagina_1=True, factor_zoom=2.0)
    reverso_200 = recortar_y_ampliar_credencial(img_reverso, es_pagina_1=False, factor_zoom=2.0)

    # Lienzo Carta a 300 DPI (2550 x 3300 px)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    ANCHO_MAXIMO = ANCHO_CARTA - 100

    if frente_200.width > ANCHO_MAXIMO:
        escala_f = ANCHO_MAXIMO / frente_200.width
        frente_200 = frente_200.resize((ANCHO_MAXIMO, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_MAXIMO:
        escala_r = ANCHO_MAXIMO / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_MAXIMO, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    # Acomodo: Subimos el reverso usando un offset negativo (-50px) sobre la altura del frente
    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 50  # Pegado más arriba

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    pos_y_reverso = pos_y_frente + frente_200.height - 50  # Subimos la segunda imagen 50px más arriba

    # 1. PASO 1 (AL FONDO): Pegamos primero la Imagen 1
    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))

    # 2. PASO 2 (AL FRENTE): Pegamos la Imagen 2 en segundo lugar para colocarla por encima
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

uploaded_files = st.file_uploader(
    "Selecciona tu PDF de 2 páginas o las 2 imágenes (Frente y Reverso)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El PDF debe tener al menos 2 páginas.")
        else:
            pix1 = doc[0].get_pixmap(dpi=300)
            img_pag1 = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc[1].get_pixmap(dpi=300)
            img_pag2 = Image.open(io.BytesIO(pix2.tobytes("png")))

            hoja_final = combinar_frente_y_reverso(img_pag1, img_pag2)

            nuevo_doc = fitz.open()
            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Frente y Reverso unificados 100% completos", use_column_width=True)
            st.success("¡Documento generado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Unificado",
                data=output_buffer,
                file_name=f"ine_unificada_200_{pdf_file.name}",
                mime="application/pdf"
            )

    elif len(uploaded_files) == 2:
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_frente_y_reverso(img1, img2)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Frente y Reverso unificados 100% completos", use_column_width=True)
        st.success("¡Imagen generada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Unificada",
            data=output_buffer,
            file_name="ine_unificada_200.png",
            mime="image/png"
        )

    else:
        st.warning("Por favor sube **1 PDF de 2 páginas** o **2 archivos de imagen**.")
