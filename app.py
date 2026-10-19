import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador INE 200% (Ambas Caras en 1 Hoja)")
st.write("El programa toma el **Cuadrante 1** de cada hoja, ajusta la altura al área de la credencial, las amplía al **200%** y las apila en una sola hoja Carta.")

def recortar_y_ampliar_credencial(imagen_pil, es_pagina_1=True, factor_zoom=2.0):
    """
    Recorta el Cuadrante 1 ajustando la altura para evitar que el fondo blanco
    haga que la imagen sea demasiado alta al ampliar al 200%.
    """
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # Márgenes superiores en píxeles (a 300 DPI: 0.5 cm = ~59px, 1 cm = ~118px)
    margen_sup_px = 59 if es_pagina_1 else 118

    # 1. Ancho: Mitad izquierda de la hoja (Cuadrante 1)
    ancho_cuadrante = ancho / 2

    # 2. Alto: Una INE en la hoja ocupa aproximadamente el 30% a 35% del alto total.
    # Usamos 0.35 * alto para no arrastrar tanto espacio blanco inferior.
    alto_cuadrante = int(alto * 0.35)

    y_inicio = min(margen_sup_px, int(alto / 2) - 10)
    y_fin = min(y_inicio + alto_cuadrante, alto)

    # Recorte ajustado: (x1, y1, x2, y2)
    cuadrante = img.crop((0, y_inicio, ancho_cuadrante, y_fin))

    # 3. Ampliar al 200%
    nuevo_ancho = int(cuadrante.width * factor_zoom)
    nuevo_alto = int(cuadrante.height * factor_zoom)

    return cuadrante.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

def combinar_frente_y_reverso(img_frente, img_reverso):
    """Une el Frente y el Reverso ampliados en una sola hoja tamaño Carta."""
    frente_200 = recortar_y_ampliar_credencial(img_frente, es_pagina_1=True, factor_zoom=2.0)
    reverso_200 = recortar_y_ampliar_credencial(img_reverso, es_pagina_1=False, factor_zoom=2.0)

    # Lienzo Carta a 300 DPI (2550 x 3300 px)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # Limitar el ancho si sobrepasa la hoja
    ANCHO_MAXIMO = ANCHO_CARTA - 120  # Margen lateral de 60px por lado

    if frente_200.width > ANCHO_MAXIMO:
        escala_f = ANCHO_MAXIMO / frente_200.width
        frente_200 = frente_200.resize((ANCHO_MAXIMO, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_MAXIMO:
        escala_r = ANCHO_MAXIMO / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_MAXIMO, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    # Posicionamiento vertical proporcional
    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 100  # Margen superior razonable

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    # El reverso se coloca con un espacio de separación cómodo de 100px debajo del frente
    pos_y_reverso = pos_y_frente + frente_200.height + 100

    # Pegar ambas caras en la misma hoja
    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

uploaded_files = st.file_uploader(
    "Selecciona tu PDF de 2 páginas o las 2 imágenes (Frente y Reverso)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    # PROCESAMIENTO DE PDF
    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".pdf"):
        pdf_file = uploaded_files[0]
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        if len(doc) < 2:
            st.warning("El PDF debe tener al menos 2 páginas para extraer Frente y Reverso.")
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

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)  # Tamaño Carta estándar
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

            output_buffer = io.BytesIO()
            nuevo_doc.save(output_buffer)
            output_buffer.seek(0)

            st.image(hoja_final, caption="Vista previa: Frente y Reverso unificados al 200%", use_column_width=True)
            st.success("¡Documento generado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Unificado en 1 Hoja",
                data=output_buffer,
                file_name=f"ine_unificada_200_{pdf_file.name}",
                mime="application/pdf"
            )

    # PROCESAMIENTO DE 2 IMÁGENES
    elif len(uploaded_files) == 2:
        img1 = Image.open(uploaded_files[0])
        img2 = Image.open(uploaded_files[1])

        hoja_final = combinar_frente_y_reverso(img1, img2)

        output_buffer = io.BytesIO()
        hoja_final.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Frente y Reverso unificados al 200%", use_column_width=True)
        st.success("¡Imagen generada con éxito!")
        st.download_button(
            label="📥 Descargar Imagen Unificada en 1 Hoja",
            data=output_buffer,
            file_name="ine_unificada_200.png",
            mime="image/png"
        )

    else:
        st.warning("Por favor sube **1 PDF de 2 páginas** o **2 archivos de imagen**.")
