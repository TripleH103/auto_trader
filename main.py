from okx_api.client import OKXClient
from utils.kline_downloader import KlineDownloader

def main():
    client = OKXClient()
    downloader = KlineDownloader(client)

    # 参数设置
    symbol = "SOL"           # 支持 BTC, ETH, SOL 等
    bar = "15m"              # 支持 1m, 5m, 15m, 1h, 4h, 1d 等
    start_date = "2025-09-01"
    end_date = "2025-09-30"
    save_path = f"utils/{symbol.lower()}_{bar}_2025.csv"

    # 下载数据
    data = downloader.download(symbol, bar, start_date, end_date, save_path)

if __name__ == "__main__":
    main()
