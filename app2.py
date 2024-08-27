
import yfinance as yf
import time
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
from dash import dcc, html
from datetime import datetime, timedelta

# Assume data is your DataFrame
app = dash.Dash(__name__)

symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN']

def fetch_data(symbol, start_date, end_date):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def compute_RSI(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_MACD(data, fast=12, slow=26, signal=9):
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def process_data(data):
    data["Day_of_week"] = data.index.day_name()
    data["Month"] = data.index.month
    data["Quarter"] = data.index.quarter
    data["Volume_category"] = pd.cut(data["Volume"], bins=[0, 6e7, 9e7, float('inf')], labels=["Low", "Medium", "High"])
    data["Market_trend"] = pd.cut(data['Close'] - data['Open'], bins=[-float('inf'), 0, float('inf')], labels=['Bearish', 'Bullish'])
    data['RSI'] = compute_RSI(data)
    data['rolling_mean_7'] = data['Close'].rolling(window=7).mean().fillna(0)
    data['rolling_std_7'] = data['Close'].rolling(window=7).std()
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'], data['MACD_signal'], _ = compute_MACD(data)
    return data

# Define color scheme
colors = {
    'background': '#1E1E1E',
    'text': '#FFFFFF',
    'primary': '#007BFF',
    'secondary': '#6C757D',
    'success': '#28A745',
    'danger': '#DC3545',
    'warning': '#FFC107',
    'info': '#17A2B8'
}

# Fetch company names
company_names = {}
for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        company_names[symbol] = ticker.info['longName']
    except:
        company_names[symbol] = symbol

dropdown_options = [{'label': f"{symbol}", 'value': symbol} for symbol in symbols]
dropdown_options.append({'label': 'Total', 'value': 'TOTAL'})

app.layout = html.Div(style={'backgroundColor': colors['background'], 'color': colors['text'], 'fontFamily': 'Arial, sans-serif'}, children=[
    html.Div([
        html.H1("Professional Trading Dashboard", style={'textAlign': 'center', 'paddingTop': '20px', 'color': colors['primary']}),
        html.Div([
            html.Div([
                html.Label("Select Stock Symbol:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='symbol-dropdown',
                    options=dropdown_options,
                    value='AAPL',
                    style={'color': colors['background'], 'backgroundColor': colors['text']}
                ),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("Select Date Range:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=(datetime.now() - timedelta(days=365)).date(),
                    end_date=datetime.now().date(),
                    display_format='YYYY-MM-DD',
                    style={'backgroundColor': colors['text']}
                ),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("Select Indicators:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                dcc.Checklist(
                    id='indicator-checklist',
                    options=[
                        {'label': 'EMA', 'value': 'EMA'},
                        {'label': 'RSI', 'value': 'RSI'},
                        {'label': 'MACD', 'value': 'MACD'}
                    ],
                    value=['EMA', 'RSI', 'MACD'],
                    style={'color': colors['text']}
                ),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("EMA Settings:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                html.Div([
                    html.Label("Fast EMA Period:"),
                    dcc.Input(id='ema-fast', type='number', value=12, style={'width': '100%'})
                ]),
                html.Div([
                    html.Label("Slow EMA Period:"),
                    dcc.Input(id='ema-slow', type='number', value=26, style={'width': '100%'})
                ]),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("RSI Settings:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                html.Div([
                    html.Label("RSI Period:"),
                    dcc.Input(id='rsi-period', type='number', value=14, style={'width': '100%'})
                ]),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("MACD Settings:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                html.Div([
                    html.Label("MACD Fast Period:"),
                    dcc.Input(id='macd-fast', type='number', value=12, style={'width': '100%'})
                ]),
                html.Div([
                    html.Label("MACD Slow Period:"),
                    dcc.Input(id='macd-slow', type='number', value=26, style={'width': '100%'})
                ]),
                html.Div([
                    html.Label("MACD Signal Period:"),
                    dcc.Input(id='macd-signal', type='number', value=9, style={'width': '100%'})
                ]),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
            html.Div([
                html.Label("Chart Heights:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                html.Div([
                    html.Label("Candlestick Chart Height:"),
                    dcc.Slider(id='candlestick-height', min=300, max=800, step=50, value=600, marks={i: str(i) for i in range(300, 801, 100)})
                ]),
                html.Div([
                    html.Label("RSI Chart Height:"),
                    dcc.Slider(id='rsi-height', min=100, max=400, step=50, value=200, marks={i: str(i) for i in range(100, 401, 100)})
                ]),
                html.Div([
                    html.Label("MACD Chart Height:"),
                    dcc.Slider(id='macd-height', min=100, max=400, step=50, value=300, marks={i: str(i) for i in range(100, 401, 100)})
                ]),
            ], style={'padding': '15px', 'backgroundColor': colors['secondary'], 'borderRadius': '10px', 'marginBottom': '15px'}),
        ], style={'width': '250px', 'float': 'left', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '10px', 'marginRight': '20px'}),
        html.Div([
            dcc.Graph(id='candlestick-chart'),
            html.Div([
                dcc.Graph(id='rsi-chart')
            ], id='rsi-container'),
            html.Div([
                dcc.Graph(id='macd-chart')
            ], id='macd-container'),
            # Bar Chart - Market Trend by Day of Week
            dcc.Graph(id='bar-chart'),
            # 3D Plot - RSI vs MACD vs Close
            dcc.Graph(id='3d-plot'),
            # Histogram - Rolling Standard Deviation
            dcc.Graph(id='histogram'),
            # Pie Chart - Volume Category Distribution
            dcc.Graph(id='pie-chart'),
            # Treemap - Volume by Day of Week and Category
            dcc.Graph(id='treemap'),
        ], style={'margin-left': '290px'})
    ])
])

@app.callback(
    [Output('candlestick-chart', 'figure'),
     Output('rsi-chart', 'figure'),
     Output('macd-chart', 'figure'),
     Output('rsi-container', 'style'),
     Output('macd-container', 'style'),
     Output('bar-chart', 'figure'),
     Output('3d-plot', 'figure'),
     Output('histogram', 'figure'),
     Output('pie-chart', 'figure'),
     Output('treemap', 'figure')],
    [Input('symbol-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('indicator-checklist', 'value'),
     Input('ema-fast', 'value'),
     Input('ema-slow', 'value'),
     Input('rsi-period', 'value'),
     Input('macd-fast', 'value'),
     Input('macd-slow', 'value'),
     Input('macd-signal', 'value'),
     Input('candlestick-height', 'value'),
     Input('rsi-height', 'value'),
     Input('macd-height', 'value')]
)
def update_charts(symbol, start_date, end_date, selected_indicators, ema_fast, ema_slow, rsi_period, 
                  macd_fast, macd_slow, macd_signal, candlestick_height, rsi_height, macd_height):
    if not symbol or not start_date or not end_date:
        return dash.no_update

    try:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        if symbol == 'TOTAL':
            data = pd.DataFrame()
            for s in symbols:
                stock_data = fetch_data(s, start_date, end_date)
                if data.empty:
                    data = stock_data
                else:
                    data = data.add(stock_data, fill_value=0)
            data = data.div(len(symbols))  # Average of all stocks
        else:
            data = fetch_data(symbol, start_date, end_date)

        if data.empty:
            raise ValueError("No data available for the selected date range")

        data = process_data(data)

        # Candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_line_color=colors['success'],
            decreasing_line_color=colors['danger'],
            name='Price'
        )])

        # Improved volume bars
        colors_volume = [colors['danger'] if data['Close'][i] < data['Open'][i] else colors['success'] for i in range(len(data))]
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors_volume,
            opacity=0.3,
            yaxis='y2'
        ))

        if 'EMA' in selected_indicators:
            ema_fast_line = data['Close'].ewm(span=ema_fast, adjust=False).mean()
            ema_slow_line = data['Close'].ewm(span=ema_slow, adjust=False).mean()
            fig.add_trace(go.Scatter(x=data.index, y=ema_fast_line, mode='lines', name=f'EMA {ema_fast}', line=dict(color=colors['primary'])))
            fig.add_trace(go.Scatter(x=data.index, y=ema_slow_line, mode='lines', name=f'EMA {ema_slow}', line=dict(color=colors['warning'])))

        title = f'{symbol} - {company_names.get(symbol, "Total")}' if symbol != 'TOTAL' else 'Total of Selected Stocks'
        fig.update_layout(
            title=dict(
                text=title,
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            yaxis_title='Price',
            yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            height=candlestick_height,
            margin=dict(t=100),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
                         
        # Common x-axis configuration for all charts
        xaxis_config = dict(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]),
                bgcolor=colors['secondary'],
                activecolor=colors['primary'],
                font=dict(color=colors['text'])
            )
        )

        fig.update_xaxes(**xaxis_config)

        # RSI chart
        rsi_fig = go.Figure()
        if 'RSI' in selected_indicators:
            rsi = compute_RSI(data, window=rsi_period)
            rsi_fig.add_trace(go.Scatter(x=data.index, y=rsi, mode='lines', name='RSI', line=dict(color=colors['info'])))
            rsi_fig.add_hline(y=70, line_dash="dash", line_color=colors['danger'], annotation_text="Overbought")
            rsi_fig.add_hline(y=30, line_dash="dash", line_color=colors['success'], annotation_text="Oversold")
            rsi_fig.update_layout(
                title='RSI',
                yaxis_title='RSI Value',
                template='plotly_dark',
                height=rsi_height,
                margin=dict(l=50, r=50, t=85, b=50)
            )
            rsi_fig.update_xaxes(**xaxis_config)

        # MACD chart
        macd_fig = go.Figure()
        if 'MACD' in selected_indicators:
            macd, signal, histogram = compute_MACD(data, fast=macd_fast, slow=macd_slow, signal=macd_signal)
            macd_fig.add_trace(go.Scatter(x=data.index, y=macd, mode='lines', name='MACD', line=dict(color=colors['primary'])))
            macd_fig.add_trace(go.Scatter(x=data.index, y=signal, mode='lines', name='Signal', line=dict(color=colors['warning'])))
            macd_fig.add_trace(go.Bar(x=data.index, y=histogram, name='Histogram', marker_color=colors['success']))
            macd_fig.update_layout(
                title='MACD',
                yaxis_title='MACD Value',
                template='plotly_dark',
                height=macd_height,
                margin=dict(l=50, r=50, t=85, b=50)
            )
            macd_fig.update_xaxes(**xaxis_config)

        rsi_style = {'display': 'block'} if 'RSI' in selected_indicators else {'display': 'none'}
        macd_style = {'display': 'block'} if 'MACD' in selected_indicators else {'display': 'none'}

        # Bar Chart - Market Trend by Day of Week
        bar_fig = px.bar(data, x='Day_of_week', color='Market_trend',
                         title="Market Trend by Day of the Week",
                         template='plotly_dark')

        # 3D Plot - RSI vs MACD vs Close
        scatter_3d_fig = px.scatter_3d(data, x='RSI', y='MACD', z='Close', color='Market_trend',
                                       title='3D Plot of RSI vs MACD vs Close',
                                       template='plotly_dark')

        # Histogram - Rolling Standard Deviation
        histogram_fig = px.histogram(data, x='rolling_std_7', 
                                     title="Distribution of Rolling Standard Deviation",
                                     template='plotly_dark')

        # Pie Chart - Volume Category Distribution
        pie_fig = px.pie(data, names='Volume_category', 
                         title="Volume Category Distribution",
                         template='plotly_dark')

        # Treemap - Volume by Day of Week and Category
        treemap_fig = px.treemap(data, path=['Volume_category', 'Day_of_week'], values='Volume',
                                 title="Treemap of Volume by Category and Day of Week",
                                 template='plotly_dark')

        return fig, rsi_fig, macd_fig, rsi_style, macd_style, bar_fig, scatter_3d_fig, histogram_fig, pie_fig, treemap_fig

    except Exception as e:
        print(f"Error in update_charts: {e}")
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True, port=8080)