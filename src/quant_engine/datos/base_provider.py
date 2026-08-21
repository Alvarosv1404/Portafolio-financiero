from abc import ABC, abstractmethod
import pandas as pd

class DataProvider(ABC):
    """
    Clase base abstracta para cualquier proveedor de datos de mercado,
    Definir el contrato que todo proveedor concreto (YFinanceProvider,
    TwelveDataProvider, etc.) debe cumplir.
    """

    @abstractmethod
    def llamar_precios(self, tickets:list, start:str, end:str) -> pd.DataFrame:
        """
        Debe dar un Dataframe con los precios históricos
        de los tickets indicados, entre start y end.
        """