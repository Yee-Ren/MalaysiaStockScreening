import yfinance as yf
from datetime import datetime, timedelta
import logging
from tqdm import tqdm  # Import tqdm for the progress bar
import time  # Import time module to measure elapsed time
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os
import shutil

class Test:
    def __init__(self):
        # Initialize the lists for storing stock codes
        self.open_close_above_ema_25_50 = []
        self.open_close_between_ema_25_50 = []
        self.close_above_ema_25 = []
        self.high_potential_stocks = []

    def test(self):
        start_time = time.time()  # Record the start time

        end_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Suppress logging from yfinance
        yfinance_logger = logging.getLogger("yfinance")
        yfinance_logger.setLevel(logging.CRITICAL)  # Set to CRITICAL to suppress less severe logs

        # Suppress logs from the specific utility logger used by yfinance (if known)
        yf_utils_logger = logging.getLogger("yfinance.utils")
        yf_utils_logger.setLevel(logging.CRITICAL)

        # Generate the list of stock codes
        stock_codes = [f"{code:04d}.KL" for code in range(10000)]

        # Batch download all the stock data at once
        all_data = yf.download(stock_codes, start=start_date, end=end_date, group_by='ticker')

        # Iterate through the data for each stock
        for stock_code in tqdm(stock_codes, desc="Processing stock data", unit="stock", ncols=100, ascii=True,
                               leave=False):
            try:
                data = all_data[stock_code]

                if not data.empty and len(data) >= 50:  # Ensure enough data points
                    # Ensure we avoid the SettingWithCopyWarning by using .loc to assign new columns
                    data = data.copy()  # Create a copy to ensure we aren't working on a slice

                    # Calculate EMA 25 and EMA 50 if enough data points
                    if len(data) >= 25:
                        data.loc[:, 'EMA25'] = data['Close'].ewm(span=25, adjust=False).mean()
                    if len(data) >= 50:
                        data.loc[:, 'EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

                    # Get the last and second-last values for close, open, EMA, and volume
                    last_close = data['Close'].iloc[-1]
                    last_open = data['Open'].iloc[-1]
                    last_ema25 = data['EMA25'].iloc[-1] if 'EMA25' in data.columns else None
                    last_ema50 = data['EMA50'].iloc[-1] if 'EMA50' in data.columns else None
                    last_volume = data['Volume'].iloc[-1]

                    prev_open = data['Open'].iloc[-2]
                    prev_close = data['Close'].iloc[-2]
                    prev_volume = data['Volume'].iloc[-2]

                    # Filter out stocks with closing price less than 0.3
                    if last_close >= 0.3 and last_ema25 is not None and last_ema50 is not None and last_ema25 > last_ema50:
                        # High potential stock filter
                        if (last_close > last_ema25 and
                                last_open > last_ema50 and last_close > last_ema50 and
                                last_close > prev_close and last_volume > prev_volume and
                                last_close > last_open and last_close > prev_open):
                            self.high_potential_stocks.append(stock_code)
                        # Categorize the stock based on the other criteria
                        if last_open > last_ema25 and last_close > last_ema25 and last_open > last_ema50 and last_close > last_ema50:
                            self.open_close_above_ema_25_50.append(stock_code)
                        elif last_ema25 < last_open < last_ema50 and last_ema25 < last_close < last_ema50:
                            self.open_close_between_ema_25_50.append(stock_code)
                        elif last_close > last_ema25:
                            self.close_above_ema_25.append(stock_code)

            except Exception:
                pass  # Silently ignore errors

        # Calculate and print the time elapsed
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nTime elapsed: {elapsed_time:.2f} seconds")

        # Print the results with the count of stocks in each category
        print(f"\nHigh Potential Stocks ({len(self.high_potential_stocks)}):", self.high_potential_stocks)
        print(f"\nUptrend stocks above EMA 25 and EMA 50 ({len(self.open_close_above_ema_25_50)}):",
              self.open_close_above_ema_25_50)
        print(f"\nStocks between EMA 25 and EMA 50 ({len(self.open_close_between_ema_25_50)}):",
              self.open_close_between_ema_25_50)
        print(f"\nStocks breakthrough EMA 25 ({len(self.close_above_ema_25)}):", self.close_above_ema_25)

        # Create and display candlestick charts for each category
        self.create_charts(all_data)

    def create_charts(self, all_data):
        # Get today's date in YYYY-MM-DD format
        today_date = datetime.today().strftime('%Y-%m-%d')

        # Path to the .bat file within the same package
        bat_file_path = os.path.join(os.path.dirname(__file__), 'open_multiple_html_files.bat')

        categories = {
            "High Potential Stocks": self.high_potential_stocks,
            # "Uptrend Stocks Above EMA 25 and EMA 50": self.open_close_above_ema_25_50,
            # "Stocks Between EMA 25 and EMA 50": self.open_close_between_ema_25_50,
            # "Stocks Breakthrough EMA 25": self.close_above_ema_25
        }

        for category_name, stock_list in categories.items():
            # Create directory for today's date and category if it doesn't exist
            directory_path = os.path.join(today_date, category_name)
            os.makedirs(directory_path, exist_ok=True)

            # Copy the .bat file into the newly created directory
            shutil.copy(bat_file_path, directory_path)

            for stock_code in stock_list:
                data = all_data[stock_code].copy()  # Ensure a deep copy to avoid the SettingWithCopyWarning

                # Recalculate EMA 25 and EMA 50 in case they weren't calculated before
                if len(data) >= 25:
                    data.loc[:, 'EMA25'] = data['Close'].ewm(span=25, adjust=False).mean()
                if len(data) >= 50:
                    data.loc[:, 'EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

                # Skip if data does not have the necessary EMA columns
                if 'EMA25' not in data.columns or 'EMA50' not in data.columns:
                    print(
                        f"Warning: Not enough data to generate EMA25/EMA50 for {stock_code}. Chart will not be generated.")
                    continue

                # Create a figure with two rows: one for candlesticks and one for volume
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    row_heights=[0.7, 0.3],  # Candlestick chart gets 70% height, volume 30%
                                    vertical_spacing=0.05)

                # Candlestick chart
                fig.add_trace(go.Candlestick(x=data.index.date,  # Use .date to remove time part
                                             open=data['Open'],
                                             high=data['High'],
                                             low=data['Low'],
                                             close=data['Close'],
                                             name='Candlesticks',
                                             hoverinfo='skip'),
                              row=1, col=1)

                # EMA 25 and EMA 50
                fig.add_trace(go.Scatter(x=data.index.date, y=data['EMA25'], mode='lines', name='EMA 25',
                                         line=dict(color='blue'),
                                         hoverinfo='skip'),
                              row=1, col=1)
                fig.add_trace(
                    go.Scatter(x=data.index.date, y=data['EMA50'], mode='lines', name='EMA 50', line=dict(color='red'),
                               hoverinfo='skip'),
                    row=1, col=1)

                # Volume bar chart in the second row
                fig.add_trace(
                    go.Bar(x=data.index.date, y=data['Volume'], name='Volume', marker_color='gray', opacity=0.5),
                    row=2, col=1)

                # Update layout to ensure date-only x-axis and no overlap
                fig.update_layout(
                    xaxis=dict(
                        type="category",
                        rangeslider_visible=False,
                        showspikes=True,  # Enable spike lines for x-axis
                        spikemode='across+marker',  # Show spike lines across the axis and marker
                        spikesnap='cursor',  # Spike snaps to cursor
                        spikedash='solid',  # Solid spike line
                        spikethickness=1,  # Thickness of the spike line
                        spikecolor="black",  # Color of the spike line
                        showline=True,  # Show the x-axis line
                        showgrid=True,  # Show x-axis grid lines
                    ),
                    yaxis=dict(
                        showspikes=True,  # Enable spike lines for y-axis
                        spikemode='across+marker',  # Show spike lines across the axis and marker
                        spikesnap='cursor',  # Spike snaps to cursor
                        spikethickness=1,  # Thickness of the spike line
                        spikecolor="black",  # Color of the spike line
                        showline=True,  # Show the y-axis line
                        showgrid=True,  # Show y-axis grid lines
                        side='right',
                    ),
                    xaxis2=dict(type="category"),  # Volume x-axis configuration
                    height=700,
                    title_text=f"{stock_code} - {category_name}",
                    hovermode='x',  # Hover mode to display values on the axes
                    legend=dict(
                        orientation="v",  # Vertical orientation
                        yanchor="top",  # Align the legend to the top
                        y=1,  # Position the legend at the top of the chart
                        xanchor="left",  # Align the legend to the left
                        x=0  # Position the legend at the left of the chart
                    ),
                    dragmode="pan"  # Set drag mode to "pan"
                )

                # Save the chart to the appropriate directory with scrollZoom enabled
                config = dict(scrollZoom=True)
                filename = os.path.join(directory_path, f"{stock_code}.html")
                fig.write_html(filename, config=config)


if __name__ == "__main__":
    # Step 1: Instantiate the class
    tester = Test()

    # Step 2: Call the `test` method
    tester.test()
