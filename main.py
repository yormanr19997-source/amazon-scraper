from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import math
import re  # 🔥 necesario para el descuento


class AmazonScraper:

    def __init__(self, producto):
        self.producto = producto
        self.data = []
        self.paginas_recorridas = 0  

        options = Options()
        options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(options=options)

    def buscar_producto(self):
        self.driver.get("https://www.amazon.com")
        time.sleep(2)

        buscador = self.driver.find_element(By.ID, "twotabsearchtextbox")
        buscador.send_keys(self.producto)
        buscador.send_keys(Keys.ENTER)
        time.sleep(3)

    def scrapear_pagina(self):
        productos = self.driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

        for p in productos:
            try:
                nombre = p.find_element(By.TAG_NAME, "h2").text
            except:
                continue

            # Precio
            try:
                entero = p.find_element(By.CLASS_NAME, "a-price-whole").text
                decimal = p.find_element(By.CLASS_NAME, "a-price-fraction").text
                precio = float((entero + decimal).replace(",", ""))
            except:
                continue

            # 🔥 DESCUENTO CORREGIDO (más robusto)
            descuento = 0.0
            try:
                spans = p.find_elements(By.XPATH, ".//span")
                for s in spans:
                    texto = s.text.lower()
                    if "%" in texto:
                        match = re.search(r'(\d+)', texto)
                        if match:
                            descuento = float(match.group(1))
                            break
            except:
                descuento = 0.0

            # Calificación
            try:
                rating = p.find_element(By.CLASS_NAME, "a-icon-alt").get_attribute("innerHTML")
                rating = float(rating.split(" ")[0].replace(",", "."))
            except:
                rating = 0.0

            # Tipo
            try:
                p.find_element(By.XPATH, ".//span[contains(text(),'Patrocinado')]")
                tipo = "Patrocinado"
            except:
                tipo = "Orgánico"

            # Estado
            try:
                p.find_element(By.XPATH, ".//span[contains(text(),'Agotado')]")
                estado = "Agotado"
            except:
                estado = "Disponible"

            self.data.append({
                "Nombre": nombre,
                "Precio": precio,
                "Descuento (%)": descuento,
                "Calificación": rating,
                "Tipo": tipo,
                "Estado": estado
            })

    def navegar_paginas(self):
        while True:
            self.paginas_recorridas += 1
            print(f"Scrapeando página {self.paginas_recorridas}")
            time.sleep(2)

            self.scrapear_pagina()

            try:
                siguiente = self.driver.find_element(By.XPATH, "//a[contains(@class,'s-pagination-next')]")

                if "disabled" in siguiente.get_attribute("class"):
                    break

                siguiente.click()
            except:
                break

    def procesar_datos(self):
        df = pd.DataFrame(self.data)

        df["Precio Final"] = df["Precio"] * (1 - df["Descuento (%)"] / 100)

        df = df[df["Nombre"].str.contains(self.producto, case=False, na=False)]

        df = df.sort_values(by="Precio", ascending=False)

        return df

    def guardar_excel_segmentado(self, df):
        total = len(df)
        tamaño_segmento = math.ceil(total / self.paginas_recorridas)

        writer = pd.ExcelWriter("resultado.xlsx", engine="openpyxl")

        for i in range(self.paginas_recorridas):
            inicio = i * tamaño_segmento
            fin = inicio + tamaño_segmento

            df_segmento = df.iloc[inicio:fin]
            df_segmento.to_excel(writer, sheet_name=f"Segmento_{i+1}", index=False)

        writer.close()

    def ejecutar(self):
        self.buscar_producto()
        self.navegar_paginas()

        df = self.procesar_datos()
        self.guardar_excel_segmentado(df)

        self.driver.quit()
        print("Proceso terminado ✅")


if __name__ == "__main__":
    scraper = AmazonScraper("laptop")
    scraper.ejecutar()