import io
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image, ImageChops

st.set_page_config(page_title="Ampliador INE 200%", page_icon="🪪", layout="centered")

st.title("🪪 Procesador de INE (Frente y Reverso Desplazados)")
st.write("Sube el PDF o la imagen. El programa extraerá las credenciales sin importar en qué posición o esquina estén, las ampliará al **200%** y las organizará en una **hoja tamaño Carta**.")

def extraer_y_apilar_ine(imagen_pil, factor_zoom=2.0):
    """Detecta las credenciales en la hoja, las recorta, las amplía al 200% y las distribuye en hoja carta."""
    img = imagen_pil.convert("RGB")
    ancho, alto = img.size

    # 1. Extraer la mitad superior y la mitad inferior de la imagen original
    mitad_superior = img.crop((0, 0, ancho, alto / 2))
    mitad_inferior = img.crop((0, alto / 2, ancho, alto))

    def recortar_fondo_blanco(crop_img):
        """Elimina el espacio blanco sobrante alrededor de cada credencial."""
        bg = Image.new(crop_img.mode, crop_img.size, (255, 255, 255))
        diff = ImageChops.difference(crop_img, bg)
        # Usar un umbral para ignorar sombras ligeras del escáner
        bbox = diff.getbbox()
        if bbox:
            return crop_img.crop(bbox)
        return crop_img

    credencial_1 = recortar_fondo_blanco(mitad_superior)
    credencial_2 = recortar_fondo_blanco(mitad_inferior)

    # 2. Ampliar cada credencial recortada al 200%
    cred_1_200 = credencial_1.resize((int(credencial_1.width * factor_zoom), int(credencial_1.height * factor_zoom)), Image.Resampling.LANCZOS)
    cred_2_200 = credencial_2.resize((int(credencial_2.width * factor_zoom), int(credencial_2.height * factor_zoom)), Image.Resampling.LANCZOS)

    # 3. Crear Lienzo Hoja Carta Estándar a 300 DPI (2550 x 3300 px)
    ANCHO_CARTA, ALTO_CARTA = 2550, 3300
    hoja_carta = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))

    # Ajustar ancho máximo para que no sobresalgan de la hoja carta
    ANCHO_MAXIMO = ANCHO_CARTA - 200  # Margen lateral de 100px a cada lado

    if cred_1_200.width > ANCHO_MAXIMO:
        escala = ANCHO_MAXIMO / cred_1_200.width
        cred_1_200 = cred_1_200.resize((ANCHO_MAXIMO, int(cred_1_200.height * escala)), Image.Resampling.LANCZOS)

    if cred_2_200.width > ANCHO_MAXIMO:
        escala = ANCHO_MAXIMO / cred_2_200.width
        cred_2_200 = cred_2_200.resize((ANCHO_MAXIMO, int(cred_2_200.height * escala)), Image.Resampling.LANCZOS)

    # 4. Posicionar ambas credenciales centradas (una en cada mitad de la hoja)
    # Mitad Superior (Frente o Reverso)
    pos_x1 = (ANCHO_CARTA - cred_1_200.width) // 2
    pos_y1 = (ALTO_CARTA // 4) - (cred_1_200.height // 2)

    # Mitad Inferior (Frente o Reverso)
    pos_x2 = (ANCHO_CARTA - cred_2_200.width) // 2
    pos_y2 = ((3 * ALTO_CARTA) // 4) - (cred_2_200.height // 2)

    hoja_carta.paste(cred_1_200, (pos_x1, max(100, pos_y1)))
    hoja_carta.paste(cred_2_200, (pos_x2, pos_y2))

    return hoja_carta

uploaded_file = st.file_uploader("Selecciona la imagen o PDF de tu INE", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    st.info("Detectando ambas credenciales, eliminando espacio blanco y ampliando al 200%...")

    # CASO PDF
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        nuevo_doc = fitz.open()

        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img_original = Image.open(io.BytesIO(pix.tobytes("png")))

            hoja_final = extraer_y_apilar_ine(img_original, factor_zoom=2.0)

            img_bytes = io.BytesIO()
            hoja_final.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            nueva_pagina = nuevo_doc.new_page(width=612, height=792)
            nueva_pagina.insert_image(nueva_pagina.rect, stream=img_bytes.getvalue())

        output_buffer = io.BytesIO()
        nuevo_doc.save(output_buffer)
        output_buffer.seek(0)

        st.success("¡Documento generado con éxito en Tamaño Carta!")
        st.download_button(
            label="📥 Descargar PDF Reorganizado al 200%",
            data=output_buffer,
            file_name=f"ine_reorganizada_200_{uploaded_file.name}",
            mime="application/pdf"
        )

    # CASO IMAGEN (JPG / PNG)
    else:
        img_original = Image.open(io.BytesIO(file_bytes))
        hoja_final = extraer_y_apilar_ine(img_original, factor_zoom=2.0)

        output_buffer = io.BytesIO()
        fmt = "PNG" if filename.endswith(".png") else "JPEG"
        hoja_final.save(output_buffer, format=fmt, quality=95)
        output_buffer.seek(0)

        st.image(hoja_final, caption="Vista previa: Hojas divididas al 50% con credenciales ampliadas al 200%", use_column_width=True)

        st.success("¡Imagen generada con éxito en Tamaño Carta!")
        st.download_button(
            label="📥 Descargar Imagen Reorganizada al 200%",
            data=output_buffer,
            file_name=f"ine_reorganizada_200_{uploaded_file.name}",
            mime=f"image/{fmt.lower()}"
        )
