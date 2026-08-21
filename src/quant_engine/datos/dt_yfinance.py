import pandas as pd
import yfinance as yf
import openpyxl

def Universo_yf(ruta: str) -> pd.DataFrame:
    return pd.read_excel(ruta)


def cierre_sect_yf(Universo_yf: pd.DataFrame, sector: str, start:str, end:str) -> pd.DataFrame:
    Filtro_sect= Universo_yf[Universo_yf["Sector"]==sector]["Ticket"].tolist()
    datos =yf.download(Filtro_sect, start=start, end=end)
    return datos [["Close","Open"]] #Doble corchete para la lista