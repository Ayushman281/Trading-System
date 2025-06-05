"""
Generate reports from trading strategy backtest results.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from utils.logger import get_logger

logger = get_logger(__name__)

class ReportGenerator:
    def __init__(self, backtest_results):
        """
        Initialize the report generator.
        
        Args:
            backtest_results: Dictionary with backtest results
        """
        self.results = backtest_results
        self.portfolio = backtest_results['portfolio']
        self.metrics = backtest_results['metrics']
        
    def generate_html_report(self):
        """
        Generate an HTML report of the backtest results.
        
        Returns:
            String containing HTML report
        """
        # Generate charts
        performance_chart = self._generate_performance_chart()
        drawdown_chart = self._generate_drawdown_chart()
        
        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Strategy Backtest Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0; }}
                .metric-card {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; }}
                .chart {{ margin: 20px 0; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Trading Strategy Backtest Report</h1>
                    <p>Period: {self.metrics['start_date']} to {self.metrics['end_date']}</p>
                </div>
                
                <div class="summary">
                    <h2>Performance Summary</h2>
                    <div class="metrics">
                        <div class="metric-card">
                            <h3>Initial Capital</h3>
                            <p>${self.metrics['initial_value']:,.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Final Value</h3>
                            <p>${self.metrics['final_value']:,.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Total Return</h3>
                            <p>{self.metrics['total_return']:.2%}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Annual Return</h3>
                            <p>{self.metrics['annual_return']:.2%}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Volatility</h3>
                            <p>{self.metrics['volatility']:.2%}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Sharpe Ratio</h3>
                            <p>{self.metrics['sharpe_ratio']:.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Max Drawdown</h3>
                            <p>{self.metrics['max_drawdown']:.2%}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Number of Trades</h3>
                            <p>{self.metrics['num_trades']}</p>
                        </div>
                    </div>
                </div>
                
                <div class="chart">
                    <h2>Portfolio Performance</h2>
                    <img src="data:image/png;base64,{performance_chart}" alt="Portfolio Performance Chart" style="max-width:100%;">
                </div>
                
                <div class="chart">
                    <h2>Drawdown Analysis</h2>
                    <img src="data:image/png;base64,{drawdown_chart}" alt="Drawdown Chart" style="max-width:100%;">
                </div>
                
                <div class="trades">
                    <h2>Trade Summary</h2>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>Buy Signals</td>
                            <td>{self.metrics['buy_signals']}</td>
                        </tr>
                        <tr>
                            <td>Sell Signals</td>
                            <td>{self.metrics['sell_signals']}</td>
                        </tr>
                        <tr>
                            <td>Total Trades</td>
                            <td>{self.metrics['num_trades']}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_performance_chart(self):
        """
        Generate portfolio performance chart.
        
        Returns:
            Base64 encoded string of the chart image
        """
        plt.figure(figsize=(10, 6))
        
        # Plot portfolio value
        plt.plot(self.portfolio.index, self.portfolio['total'], label='Portfolio Value', color='blue')
        
        # Add buy/sell markers
        buy_signals = self.portfolio[self.portfolio['position'] == 1.0]
        sell_signals = self.portfolio[self.portfolio['position'] == -1.0]
        
        plt.scatter(buy_signals.index, buy_signals['total'], color='green', marker='^', s=100, label='Buy')
        plt.scatter(sell_signals.index, sell_signals['total'], color='red', marker='v', s=100, label='Sell')
        
        # Add price and moving averages
        ax2 = plt.twinx()
        ax2.plot(self.portfolio.index, self.portfolio['close'], alpha=0.3, color='gray', label='Price')
        
        if 'MA_50' in self.portfolio.columns and 'MA_200' in self.portfolio.columns:
            ax2.plot(self.portfolio.index, self.portfolio['MA_50'], alpha=0.5, color='orange', label='50-day MA')
            ax2.plot(self.portfolio.index, self.portfolio['MA_200'], alpha=0.5, color='purple', label='200-day MA')
        
        # Customize the plot
        plt.title('Portfolio Performance')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        ax2.set_ylabel('Price ($)')
        
        # Add legends
        lines1, labels1 = plt.gca().get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _generate_drawdown_chart(self):
        """
        Generate drawdown chart.
        
        Returns:
            Base64 encoded string of the chart image
        """
        plt.figure(figsize=(10, 6))
        
        # Calculate drawdowns
        cum_returns = (1 + self.portfolio['returns']).cumprod()
        running_max = cum_returns.cummax()
        drawdowns = (cum_returns / running_max - 1) * 100  # In percentage
        
        # Plot drawdowns
        plt.fill_between(drawdowns.index, 0, drawdowns, color='red', alpha=0.3)
        plt.plot(drawdowns.index, drawdowns, color='red', alpha=0.5)
        
        # Customize the plot
        plt.title('Portfolio Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, alpha=0.3)
        
        # Add maximum drawdown line
        plt.axhline(y=drawdowns.min(), color='r', linestyle='--', 
                   label=f'Maximum Drawdown: {drawdowns.min():.2f}%')
        plt.legend()
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def save_report_to_file(self, filename="backtest_report.html"):
        """
        Save the HTML report to a file.
        
        Args:
            filename: Name of the output file
            
        Returns:
            Path to the saved file
        """
        html_content = self.generate_html_report()
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Report saved to {filename}")
        return filename
