import yfinance as yf
import time
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go


apple = yf.Ticker("AAPL")
data = apple.history(
    # period="max",
    start="2020-01-01",
    end=time.strftime("%Y-%m-%d", time.localtime()),
    # interval="1d"
)

data["Day_of_week"] = data.index.day_name()
data["Month"] = data.index.month
data["Quarter"] = data.index.quarter

data["Volume_category"] = pd.cut(data["Volume"], bins=[0, 6e7, 9e7, float('inf')], labels=["Low", "Medium", "High"])

data["Market_trend"] = pd.cut(data['Close'] - data['Open'], bins=[-float('inf'), 0, float('inf')], labels=['Bearish', 'Bullish'])

def compute_RSI(data, window=14):
    delta = data['Close'].diff()
    U = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    D = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    RS = U / D
    RSI = 100 - (100 / (1 + RS))
    return RSI

data['RSI'] = compute_RSI(data)

data['rolling_mean_7'] = data['Close'].rolling(window=7).mean().fillna(0)
data['rolling_std_7'] = data['Close'].rolling(window=7).std()

data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = data['EMA_12'] - data['EMA_26']
data['MACD_signal'] = data['MACD'].ewm(span=9, adjust=False).mean()


# Assume data is your DataFrame
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1("Financial Market Analysis Dashboard"),

    # Line Chart - Close Prices with Moving Averages
    dcc.Graph(id='line-chart',
              figure={
                  'data': [
                      go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'),
                      go.Scatter(x=data.index, y=data['EMA_12'], mode='lines', name='EMA_12'),
                      go.Scatter(x=data.index, y=data['EMA_26'], mode='lines', name='EMA_26'),
                  ],
                  'layout': go.Layout(title='Closing Prices with EMA')
              }),

    # Bar Chart - Market Trend by Day of Week
    dcc.Graph(id='bar-chart',
              figure=px.bar(data, x='Day_of_week', color='Market_trend',
                            title="Market Trend by Day of the Week")),

    # Trend Chart - MACD and MACD Signal
    dcc.Graph(id='trend-chart',
              figure={
                  'data': [
                      go.Scatter(x=data.index, y=data['MACD'], mode='lines', name='MACD'),
                      go.Scatter(x=data.index, y=data['MACD_signal'], mode='lines', name='MACD Signal')
                  ],
                  'layout': go.Layout(title='MACD vs MACD Signal')
              }),

    # 3D Plot - RSI vs MACD vs Close
    dcc.Graph(id='3d-plot',
              figure=px.scatter_3d(data, x='RSI', y='MACD', z='Close', color='Market_trend',
                                   title='3D Plot of RSI vs MACD vs Close')),

    # Histogram - Rolling Standard Deviation
    dcc.Graph(id='histogram',
              figure=px.histogram(data, x='rolling_std_7', title="Distribution of Rolling Standard Deviation")),

    # Pie Chart - Volume Category Distribution
    dcc.Graph(id='pie-chart',
              figure=px.pie(data, names='Volume_category', title="Volume Category Distribution")),

    # Treemap - Volume by Day of Week and Category
    dcc.Graph(id='treemap',
              figure=px.treemap(data, path=['Volume_category', 'Day_of_week'], values='Volume',
                                title="Treemap of Volume by Category and Day of Week")),
])

if __name__ == '__main__':
    app.run_server(debug=True, port=80)