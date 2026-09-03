import yfinance as yf
import matplotlib.pyplot as plt


# creates a yfinance object for Microsoft
# A Ticker is an object which acts as a financial instrument to retrieve data specific to the specified ticker symbol
microsoft = yf.Ticker("MSFT")

# retrieves the historical data for Microsoft for the last month
data = microsoft.history(period="1mo")

# prints data to the console
print(data)

# creates a plot of the closing price of Microsoft
data["Close"].plot(
    title="Microsoft closing price: Last month"
)

# labels the x and y axes
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid()
plt.show()
