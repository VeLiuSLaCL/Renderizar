import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Ampliador e Insertador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Unificador de INE al 200% e Inserción en PDF")
st.write("Sube el PDF o imágenes de la INE (Frente y Reverso) y el PDF de destino donde deseas **insertar la INE en la Página 2**.")

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

    # Alto diferenciado: 30% para el frente, 42% para el reverso
    porcentaje_alto = 0.30 if es_pagina_1 else 0.42
    alto_cuadrante = int(alto * porcentaje_alto)

    y_inicio = min(margen_sup_px, int(alto / 2) - 10)
    y_fin = min(y_inicio + alto_cuadrante, alto)

    cuadrante = img.crop((0, y_inicio, ancho_cuadrante, y_fin))

    nuevo_ancho = int(cuadrante.width * factor_zoom)
    nuevo_alto = int(cuadrante.height * factor_zoom)

    return cuadrante.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

def combinar_frente_y_reverso(img_frente, img_reverso):
    """Une el Frente (al fondo) y el Reverso (al frente) subiendo 0.5 cm adicionales la segunda imagen."""
    frente_200 = recortar_y_ampliar_credencial(img_frente, es_pagina_1=True, factor_zoom=2.0)
    reverso_200 = recortar_y_ampliar_credencial(img_reverso, es_pagina_1=False, factor_zoom=2.0)

    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    ANCHO_MAXIMO = ANCHO_CARTA - 100

    if frente_200.width > ANCHO_MAXIMO:
        escala_f = ANCHO_MAXIMO / frente_200.width
        frente_200 = frente_200.resize((ANCHO_MAXIMO, int(frente_200.height * escala_f)), Image.Resampling.LANCZOS)

    if reverso_200.width > ANCHO_MAXIMO:
        escala_r = ANCHO_MAXIMO / reverso_200.width
        reverso_200 = reverso_200.resize((ANCHO_MAXIMO, int(reverso_200.height * escala_r)), Image.Resampling.LANCZOS)

    pos_x_frente = (ANCHO_CARTA - frente_200.width) // 2
    pos_y_frente = 50

    pos_x_reverso = (ANCHO_CARTA - reverso_200.width) // 2
    pos_y_reverso = pos_y_frente + frente_200.height - 110

    # 1. Pegar frente al fondo
    hoja_carta.paste(frente_200, (pos_x_frente, pos_y_frente))

    # 2. Pegar reverso al frente
    hoja_carta.paste(reverso_200, (pos_x_reverso, pos_y_reverso))

    return hoja_carta

# --- PASO 1: SUBIR INE ---
st.subheader("1. Sube el origen de la INE")
uploaded_ine_files = st.file_uploader(
    "PDF de 2 páginas de la INE o 2 Imágenes (Frente y Reverso)",
    type=["pdf"],
    accept_multiple_files=True,
    key="ine_files"
)

# --- PASO 2: SUBIR DOCUMENTO DESTINO ---
st.subheader("2. Sube el PDF destino donde insertarás la INE")
uploaded_target_pdf = st.file_uploader(
    "PDF Destino (Se insertará la INE como la Página 2)",
    type=["pdf"],
    key="target_pdf"
)

if uploaded_ine_files and uploaded_target_pdf:
    img_frente, img_reverso = None, None

    # Extracción de imágenes del origen de la INE
    if len(uploaded_ine_files) == 1 and uploaded_ine_files[0].name.lower().endswith(".pdf"):
        doc_ine = fitz.open(stream=uploaded_ine_files[0].read(), filetype="pdf")
        if len(doc_ine) >= 2:
            pix1 = doc_ine[0].get_pixmap(dpi=300)
            img_frente = Image.open(io.BytesIO(pix1.tobytes("png")))

            pix2 = doc_ine[1].get_pixmap(dpi=300)
            img_reverso = Image.open(io.BytesIO(pix2.tobytes("png")))
        else:
            st.warning("El PDF de la INE debe tener al menos 2 páginas.")

    elif len(uploaded_ine_files) == 2:
        img_frente = Image.open(uploaded_ine_files[0])
        img_reverso = Image.open(uploaded_ine_files[1])

    else:
        st.warning("Por favor sube **1 PDF de 2 páginas** o **2 archivos de imagen** para la INE.")

    # Procesamiento e inserción en el PDF destino
    if img_frente and img_reverso:
        hoja_ine = combinar_frente_y_reverso(img_frente, img_reverso)

        # Convertir hoja_ine (PIL) a PNG en memoria
        img_bytes = io.BytesIO()
        hoja_ine.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Abrir PDF destino
        doc_destino = fitz.open(stream=uploaded_target_pdf.read(), filetype="pdf")

        # Crear la página donde irá la INE (Página 2, índice 1)
        nueva_pag_ine = doc_destino.new_page(pno=1, width=612, height=792)
        nueva_pag_ine.insert_image(nueva_pag_ine.rect, stream=img_bytes.getvalue())

        # Guardar resultado final
        output_buffer = io.BytesIO()
        doc_destino.save(output_buffer)
        output_buffer.seek(0)

        st.image(hoja_ine, caption="Vista previa de la hoja de INE a insertar", use_column_width=True)
        st.success(f"¡INE procesada e insertada como Página 2 en {uploaded_target_pdf.name}! (Total páginas: {len(doc_destino)})")

        st.download_button(
            label="📥 Descargar PDF Final Combinado",
            data=output_buffer,
            file_name=f"combinado_{uploaded_target_pdf.name}",
            mime="application/pdf"
        )
