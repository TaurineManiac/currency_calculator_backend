import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime

app = FastAPI()

class Rate(BaseModel):
    Cur_ID: int
    Cur_Abbreviation: str
    Cur_Scale: int
    Cur_Name: str
    Cur_OfficialRate: float

class CurrencyExchangeForUserInput(BaseModel):
    amount : float
    currencyAbbreviationFrom : str
    currencyAbbreviationTo : str

class CurrencyExchangeForProgram(BaseModel):
    amount : float
    convertedAmount : float
    currencyAbbreviationFrom : str
    currencyAbbreviationTo : str
    currencyOfficialRate : float
    exchangeDate : datetime

class NationalBankRepublicBelarus:
    def __init__(self):
        self.base_url = "https://api.nbrb.by/exrates"

    async def getAllRates(self) -> List[Rate]:
        try:
            async with httpx.AsyncClient() as client:
                respones = await client.get(
                f"{self.base_url}/rates?periodicity=0",
                timeout = 10
                )
            respones.raise_for_status()
            list = [Rate(**rate) for rate in respones.json()]
            list.append(Rate(
                Cur_ID=993,
                Cur_Abbreviation="BYN",
                Cur_Scale=1,
                Cur_Name="Белорусский рубль",
                Cur_OfficialRate=1,
                )

            )
            list.sort(key=lambda rate: rate.Cur_Abbreviation)
            return list
        except Exception as e:
            print(f"Не удалось получить валюты {e}")
            return []

    async def getDictionaryFromRates(self) -> Dict[str, float]:
        rates = await self.getAllRates()
        ratesDict = {}
        for rate in rates:
            ratesDict[rate.Cur_Abbreviation] = rate.Cur_OfficialRate/rate.Cur_Scale
        ratesDict["BYN"]=1
        # ratesDict = dict(sorted(ratesDict.items(), key=lambda item: item[0]))
        return ratesDict

nbrb=NationalBankRepublicBelarus()

@app.get("/")
async def root():
    return {
        "version": "1.0",
        "title": "Currency Exchange Calculator",
        "endpoints": {
                        "rates": "/rates - Получить все курсы валют",
                        "convert": "/convert - Конвертировать валюту",
                        "currencies": "/currencies - Список доступных валют",
                        "docs": "/docs - Документация API"
                    }
    }

@app.get("/rates")
async def get_rates():
    rates = await  nbrb.getAllRates()
    if not rates:
        raise HTTPException(
            status_code=503,
            detail="Не удалось получить курсы от НБРБ"
        )
    return rates
@app.get("/currencies")
async def get_currencies():
    currencies = await nbrb.getDictionaryFromRates()
    currencies = dict(sorted(currencies.items(), key=lambda item: item[0]))
    return {
        "количество доступных валют": len(currencies),
        "currencies": currencies

    }

@app.post("/convert")
async def convert_currencies(currencies: CurrencyExchangeForUserInput):
    rates = await nbrb.getDictionaryFromRates()

    if not rates:
        raise HTTPException(
            status_code=503,
            detail = "Не удалось получить данный от нацбанка"
        )
    if currencies.currencyAbbreviationTo not in rates:
        raise HTTPException(
            status_code=404,
            detail = "Не удалось найди входящую валюту списке"
        )
    if currencies.currencyAbbreviationFrom not in rates:
        raise HTTPException(
            status_code=404,
            detail = "Не удалось найти исходящую валюту в списке"
        )
    return CurrencyExchangeForProgram(
        amount= currencies.amount,
        convertedAmount= currencies.amount*(rates[currencies.currencyAbbreviationFrom]/rates[currencies.currencyAbbreviationTo]),
        currencyAbbreviationFrom = currencies.currencyAbbreviationFrom,
        currencyAbbreviationTo = currencies.currencyAbbreviationTo,
        currencyOfficialRate = rates[currencies.currencyAbbreviationFrom]/rates[currencies.currencyAbbreviationTo],
        exchangeDate=datetime.now().date().isoformat(),

    )








# app = FastAPI(
#     title="Currency Calculator with NBRB Rates",
#     description="🚀 Умный калькулятор валют с реальными курсами от Национального Банка РБ",
#     version="1.0.0"
# )
#
# class CurrencyRate(BaseModel):
#     Cur_ID: int
#     Cur_Abbreviation: str
#     Cur_Scale: int
#     Cur_Name: str
#     Cur_OfficialRate: float
#
# class ConversionRequest(BaseModel):
#     amount: float
#     from_currency: str
#     to_currency: str
#
# class ConversionResponse(BaseModel):#we don`t unite this 2 classes becurse 2nd class is data,that send user and 3d class is data,that user get
#     amount: float
#     converted_amount: float
#     from_currency: str
#     to_currency: str
#     exchange_rate: float
#     rate_date: str
#
# class NBRBService:
#     def __init__(self):
#         self.base_url = "https://api.nbrb.by/exrates"
#
#     async def get_all_rates(self) -> List[CurrencyRate]:
#         """Получить ВСЕ курсы валют на текущую дату"""
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(
#                     f"{self.base_url}/rates?periodicity=0",
#                     timeout=10.0
#                 )
#                 response.raise_for_status()
#                 return [CurrencyRate(**rate) for rate in response.json()]
#
#         except Exception as e:
#             print(f"Ошибка получения курсов: {e}")
#             return []
#
#     async def get_rates_dict(self) -> Dict[str, float]:
#         """Получить курсы в удобном формате для конвертации"""
#         rates = await self.get_all_rates()
#
#         rates_dict = {}
#         for rate in rates:
#             # Приводим к курсу за 1 единицу валюты
#             rate_per_unit = rate.Cur_OfficialRate / rate.Cur_Scale
#             rates_dict[rate.Cur_Abbreviation] = rate_per_unit
#
#         # Добавляем BYN как базовую валюту
#         rates_dict["BYN"] = 1.0
#
#         return rates_dict
#
# # Инициализация сервиса
# nbrb_service = NBRBService()
#
# @app.get("/")
# async def root():
#     """Корневой эндпоинт с информацией о API"""
#     return {
#         "message": "💰 Currency Calculator API",
#         "version": "1.0.0",
#         "description": "Калькулятор валют с реальными курсами от НБРБ",
#         "endpoints": {
#             "rates": "/rates - Получить все курсы валют",
#             "convert": "/convert - Конвертировать валюту",
#             "currencies": "/currencies - Список доступных валют",
#             "docs": "/docs - Документация API"
#         }
#     }
#
# @app.get("/rates")
# async def get_current_rates():
#     """Получить все текущие курсы валют"""
#     rates = await nbrb_service.get_all_rates()
#
#     if not rates:
#         raise HTTPException(
#             status_code=503,
#             detail="Не удалось получить курсы от НБРБ"
#         )
#
#     return {
#         "date": datetime.now().date().isoformat(),
#         "rates": rates
#     }
#
# @app.post("/convert", response_model=ConversionResponse)
# async def convert_currency(request: ConversionRequest):
#     """Конвертировать валюту используя реальные курсы НБРБ"""
#     rates = await nbrb_service.get_rates_dict()
#
#     if not rates:
#         raise HTTPException(
#             status_code=503,
#             detail="Сервис курсов временно недоступен"
#         )
#
#     if request.from_currency not in rates:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Валюта {request.from_currency} не поддерживается"
#         )
#
#     if request.to_currency not in rates:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Валюта {request.to_currency} не поддерживается"
#         )
#
#     # Расчет курса и конвертированной суммы
#     from_rate = rates[request.from_currency]
#     to_rate = rates[request.to_currency]
#     exchange_rate = to_rate / from_rate
#     converted_amount = request.amount * exchange_rate
#
#     return ConversionResponse(
#         amount=request.amount,
#         converted_amount=round(converted_amount, 4),
#         from_currency=request.from_currency,
#         to_currency=request.to_currency,
#         exchange_rate=round(exchange_rate, 6),
#         rate_date=datetime.now().date().isoformat()
#     )
#
# @app.get("/currencies")
# async def get_available_currencies():
#     """Получить список доступных валют"""
#     rates = await nbrb_service.get_rates_dict()
#     return {
#         "available_currencies": list(rates.keys()),
#         "count": len(rates)
#     }
#
# # Удали эту строку - она не нужна!
# # if __name__ == "__main__":
# #     "E:\removal\Шестопалов Игнат Романович\СЯП\currency_calculator_service\.venv\Scripts\python.exe" -m uvicorn main:app --reload
