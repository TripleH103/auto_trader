import hmac
import base64
import datetime
import json
from typing import Optional
import requests
from config import config
from .endpoints import ACCOUNT_BALANCE, POSITIONS

class OKXClient:

    def __init__ (self, base_url: Optional[str] = None, debug=True) -> None:
        self.base_url:str = config.BASE_URL
        self.api_key:str  = config.OKX_API_KEY
        self.secret_key:str  = config.OKX_SECRET_KEY
        self.passphrase:str  = config.OKX_PASSPHRASE
        self.proxies:dict = config.PROXIES
        self.debug:bool = debug

    def get_timestamp(self) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        return now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
    def sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        mac = hmac.new(self.secret_key.encode(), message.encode(), digestmod="sha256")
        return base64.b64encode(mac.digest()).decode()

    def headers(self, method: str, request_path: str, body: str = "") -> dict:
        timestamp = self.get_timestamp()
        signature = self.sign(timestamp, method, request_path, body)
        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

    def request(self, method: str, endpoint: str, params: Optional[dict] = None) -> dict:
        url = self.base_url + endpoint
        body = json.dumps(params) if method.upper() in ["POST", "PUT"] else ""
        headers = self.headers(method, endpoint, body)
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, proxies=self.proxies)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=body, proxies=self.proxies)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, data=body, proxies=self.proxies)
            else:
                raise ValueError("Unsupported HTTP method")
            if self.debug:
                print(f"[DEBUG] {method} {url}")
                print(f"[DEBUG] Response Status: {response.status_code}")
                try:
                    parsed = response.json()
                    print("[DEBUG] JSON Response:\n" + json.dumps(parsed, indent=2, ensure_ascii=False))
                except Exception:
                    print("[DEBUG] Raw Response:\n" + response.text)
            return response.json()
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return {"error": str(e)}

    # 获取账户余额
    def get_account_balance(self) -> None:
        result = self.request("GET", ACCOUNT_BALANCE)
        if result.get("code") == "0":
            details = result["data"][0].get("details", [])
            print("📊 当前账户余额（可用余额 > 0）：\n")
            for asset in details:
                ccy = asset.get("ccy")
                avail = float(asset.get("availBal", "0"))
                usd_value = float(asset.get("eqUsd", "0"))
                if avail > 0:
                    print(f"🪙  {ccy}: {avail:.8f} ≈ ${usd_value:.2f} USD")
        else:
            print("❌ 获取余额失败：", result.get("msg", "未知错误"))

    # 查询持仓
    def get_positions(self) -> list:
        result = self.request("GET", POSITIONS)
        if result.get("code") == "0":
            return result.get("data", [])
        else:
            print("❌ 获取合约持仓失败：", result.get("msg", "未知错误"))
            return []
        
    def show_positions(self) -> None:
        positions = self.get_positions()
        if not positions:
            print("📭 当前没有任何合约持仓。")
            return
        print("📈 当前合约持仓：\n")
        for pos in positions:
            inst_id = pos.get("instId")
            pos_side = pos.get("posSide")
            pos_amt = pos.get("pos")
            avg_px = pos.get("avgPx")
            unreal_pnl = pos.get("upl")
            print(f"🪙 {inst_id} | 方向: {pos_side} | 持仓: {pos_amt} | 开仓均价: {avg_px} | 未实现盈亏: {unreal_pnl}")

   # 查询策略网格 
    def get_contract_grid_strategies(self) -> None:
        result = self.request("GET", "/api/v5/tradingBot/grid/order-algo")
        if result.get("code") == "0":
            strategies = result.get("data", [])
            contract_strategies = [s for s in strategies if s.get("strategyType") == "contract_grid"]
            if not contract_strategies:
                print("📭 当前没有合约网格策略。")
                return
            print("🤖 当前合约网格策略：\n")
            for s in contract_strategies:
                inst_id = s.get("instId")
                algo_id = s.get("algoId")
                status = s.get("state")
                pnl = s.get("pnl")
                investment = s.get("investmentData", {}).get("totalInvestment", "N/A")
                print(f"🧠 策略ID: {algo_id} | 币种: {inst_id} | 状态: {status} | 投入: {investment} | 盈亏: {pnl}")
        else:
            print("❌ 获取策略失败：", result.get("msg", "未知错误"))



    # 获取当前币对行情
    def get_ticker(self, inst_id: str) -> dict:
        return self.request("GET", "/api/v5/market/ticker", {"instId": inst_id})

    
    
