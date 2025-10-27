import time
import csv
import os
from typing import Optional
from okx_api.client import OKXClient
from okx_api.endpoints import HISTORY_CANDLES
from datetime import datetime


class KlineDownloader:
    def __init__(self, client: OKXClient):
        self.client = client

    @staticmethod
    def to_timestamp(date_str: str) -> int:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)

    def download(
        self,
        symbol: str,
        bar: str,
        start_date: str,
        end_date: str,
        save_path: Optional[str] = None,
    ) -> list:
        instId = f"{symbol}-USDT"
        start_ts = self.to_timestamp(start_date)
        end_ts = self.to_timestamp(end_date)
        all_data = []
        current_ts = end_ts

        while current_ts > start_ts:
            params = {"instId": instId, "bar": bar, "before": current_ts, "limit": 100}
            result = self.client.request("GET", HISTORY_CANDLES, params)
            batch = result.get("data", [])
            print(f"📊 拉取 {len(batch)} 条数据（{symbol}, {bar}）")

            if not batch:
                break

            all_data.extend(batch)
            last_ts = int(batch[-1][0])
            if last_ts <= start_ts:
                break
            current_ts = last_ts
            time.sleep(0.2)

        all_data.reverse()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ts", "o", "h", "l", "c", "vol", "volCcy"])
                writer.writerows(all_data)
            print(f"✅ 数据已保存到 {save_path}")

        return all_data
