# عثمان کو ٹیک AI سگنل بوٹ — Railway Deployment Edition

یہ پیکج Railway پر Python/Flask backend کے ساتھ آن لائن چلنے کے لیے تیار کیا گیا ہے۔

## اہم اصول
- 1m، 5m اور 15m candles اسکین ہوتی ہیں۔
- EMA، RSI، Stochastic، MACD، ADX/DMI، Parabolic SAR، Bollinger، price action اور market structure استعمال ہوتے ہیں۔
- 5m اور 15m ایک ہی سمت میں واضح confirmation دیں تو ہی UP/DOWN signal آتا ہے۔
- indicators آپس میں نہ ملیں تو **NO TRADE** آتا ہے۔
- یہ guaranteed prediction نہیں ہے اور Quotex OTC feed کی exact نقل نہیں کرتا۔
- موجودہ data provider public Binance candles استعمال کرتا ہے؛ اسے Quotex OTC candles کے برابر نہیں سمجھنا چاہیے۔

## Railway پر چلانے کا طریقہ
1. اس ZIP کو GitHub repository میں upload کریں۔
2. Railway میں New Project بنائیں۔
3. Deploy from GitHub Repo منتخب کریں۔
4. repository منتخب کریں۔
5. Railway خود Python dependencies انسٹال کرے گا اور `gunicorn app:app` سے server چلائے گا۔
6. Deploy مکمل ہونے کے بعد Railway کا generated public domain کھولیں۔
7. `/health` پر `{"status":"ok"}` آئے تو backend چل رہا ہے۔

## مقامی ٹیسٹ
`pip install -r requirements.txt`
`python app.py`
پھر Chrome میں `http://127.0.0.1:5000` کھولیں۔

یہ ورژن broker login، account bypass یا خودکار trade placement نہیں کرتا۔
