import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,#КАКОЙ тип middleware добавляем   Middleware = "Промежуточное ПО"
# 1. Браузер → Запрос к API
# 2. FastAPI → "Эй, CORS Middleware, проверь этот запрос!"
# 3. CORS Middleware → Смотрит настройки allow_origins
# 4. CORS Middleware → "Окей, этот origin разрешен → пропускаем"
# 5. Запрос попадает в твой эндпоинт (/convert, /rates)
# 6. Твой код обрабатывает и возвращает ответ
# 7. CORS Middleware → Добавляет специальные заголовки в ответ
# 8. Браузер → Видит заголовки → "Окей, показываю ответ!"
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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








